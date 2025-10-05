import os
import json
import logging
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class LatamAutomation:
    def __init__(self):
        self.chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.automation_profile_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", "LatamAutomationProfile"
        )
        self.target_endpoint = "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        self.response_received = False
        self.login_verified = False
        self.api_response = None
        
        # Configuração de performance
        self.performance_log_file = "latam_performance_log.json"
        self.current_phase = None
        self.performance_data = {
            'execution_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'start_time': None,
            'end_time': None,
            'phases': {},
            'metrics': {
                'request_count': 0,
                'error_count': 0,
                'page_loads': 0,
                'login_attempts': 0,
                'cache_hits': 0,
                'api_calls': 0
            }
        }
        
        self.setup_logging()
        self.chrome_options = self.configure_chrome()
        self.driver = None

    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(asctime)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('automation.log', mode='a', encoding='utf-8')
            ]
        )
        logging.getLogger('selenium').setLevel(logging.WARNING)
        logging.getLogger('urllib3').setLevel(logging.WARNING)

    def configure_chrome(self):
        """Configura Chrome para interceptação de rede"""
        options = Options()
        options.binary_location = self.chrome_path

        os.makedirs(self.automation_profile_path, exist_ok=True)
        
        options.add_argument(f"--user-data-dir={self.automation_profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Configurações para interceptação de rede
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        
        # Habilita logs de performance
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.images": 1,
            "credentials_enable_service": True,
            "password_manager_enabled": True,
        }
        options.add_experimental_option("prefs", prefs)
        
        return options

    def init_performance_log(self):
        """Inicializa registro de performance"""
        self.performance_data['start_time'] = datetime.now().isoformat()
        self.start_phase("initialization")

    def start_phase(self, phase_name):
        """Registra início de fase"""
        if self.current_phase:
            self.end_phase()
        self.current_phase = phase_name
        self.performance_data['phases'][phase_name] = {
            'start': time.time(),
            'end': None,
            'duration': None
        }

    def end_phase(self):
        """Finaliza fase atual"""
        if self.current_phase:
            phase_data = self.performance_data['phases'][self.current_phase]
            phase_data['end'] = time.time()
            phase_data['duration'] = phase_data['end'] - phase_data['start']
            self.current_phase = None

    def increment_metric(self, metric_name):
        """Incrementa métrica"""
        if metric_name in self.performance_data['metrics']:
            self.performance_data['metrics'][metric_name] += 1

    def save_performance_log(self):
        """Salva dados de performance"""
        self.end_phase()
        self.performance_data['end_time'] = datetime.now().isoformat()
        self.performance_data['total_duration'] = time.time() - self.performance_data['phases']['initialization']['start']
        
        try:
            data = []
            if os.path.exists(self.performance_log_file):
                with open(self.performance_log_file, 'r') as f:
                    data = json.load(f)
            
            data.append({
                'timestamp': datetime.now().isoformat(),
                'execution_data': self.performance_data
            })
            
            with open(self.performance_log_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass

    def print_performance_report(self):
        """Exibe relatório de performance"""
        total_time = self.performance_data['total_duration']
        print(f"\n⏱️  TEMPO TOTAL: {total_time:.2f}s")
        print("📊 MÉTRICAS:")
        for metric, value in self.performance_data['metrics'].items():
            print(f"   {metric}: {value}")

    def start_driver(self):
        """Inicia navegador com interceptação de rede"""
        self.start_phase("driver_initialization")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(20)
            self.driver.implicitly_wait(10)
            
            # Habilita monitoramento de rede
            self.driver.execute_cdp_cmd("Network.enable", {})
            
            # Remove detecção de automação
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)
            
            logging.info("✅ Navegador iniciado com interceptação de rede")
            self.increment_metric("page_loads")
            return True
            
        except Exception as e:
            logging.error(f"❌ Falha ao iniciar navegador: {e}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verifica estado de login"""
        try:
            login_elements = self.driver.execute_script("""
                return {
                    has_password: !!document.querySelector('input[type="password"]'),
                    has_email: !!document.querySelector('input[type="email"], input[name="email"]'),
                    has_login_button: !!document.querySelector('button[type="submit"], button[data-testid*="login"]'),
                    has_profile: !!document.querySelector('[data-testid="nick-name-component"], .user-profile')
                };
            """)
            
            is_logged_in = not (login_elements['has_password'] or login_elements['has_email'] or login_elements['has_login_button'])
            
            logging.info(f"🔐 Estado de login: {'Logado' if is_logged_in else 'Não logado'}")
            return is_logged_in
            
        except Exception as e:
            logging.warning(f"⚠️ Erro na verificação de login: {e}")
            return False

    def accept_cookies(self):
        """Aceita cookies"""
        try:
            cookie_selectors = [
                (By.ID, "cookies-politics-button"),
                (By.CSS_SELECTOR, "button[data-testid*='cookie']"),
                (By.XPATH, "//button[contains(text(), 'Aceitar')]"),
                (By.XPATH, "//button[contains(text(), 'Accept')]")
            ]
            
            for by, selector in cookie_selectors:
                try:
                    cookie_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    cookie_button.click()
                    logging.info("✅ Cookies aceitos")
                    return True
                except (TimeoutException, NoSuchElementException):
                    continue
            
            logging.debug("ℹ️ Banner de cookies não encontrado")
            return False
            
        except Exception as e:
            logging.warning(f"⚠️ Erro ao aceitar cookies: {e}")
            return False

    def do_login(self):
        """Executa login"""
        self.start_phase("login_process")
        try:
            logging.info("🔑 Iniciando processo de login...")
            
            # Preenche email
            email_selectors = [
                (By.ID, "form-input--alias"),
                (By.NAME, "email"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.CSS_SELECTOR, "input[data-testid*='email']")
            ]
            
            for by, selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    email_field.clear()
                    email_field.send_keys("dionlan.alves@gmail.com")
                    logging.info("✅ Email preenchido")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Clica no botão de continuar
            continue_selectors = [
                (By.ID, "primary-button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Continuar')]"),
                (By.XPATH, "//button[contains(text(), 'Continue')]")
            ]
            
            for by, selector in continue_selectors:
                try:
                    continue_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    continue_button.click()
                    logging.info("✅ Botão de continuar clicado")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Aguarda e preenche senha
            password_selectors = [
                (By.ID, "form-input--password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.CSS_SELECTOR, "input[data-testid*='password']")
            ]
            
            for by, selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    password_field.clear()
                    password_field.send_keys("Dionlan!@#123")
                    logging.info("✅ Senha preenchida")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Clica no botão de login final
            login_selectors = [
                (By.ID, "primary-button"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.XPATH, "//button[contains(text(), 'Entrar')]"),
                (By.XPATH, "//button[contains(text(), 'Login')]")
            ]
            
            for by, selector in login_selectors:
                try:
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    login_button.click()
                    logging.info("✅ Botão de login clicado")
                    break
                except (TimeoutException, NoSuchElementException):
                    continue
            
            # Verifica se login foi bem-sucedido
            try:
                WebDriverWait(self.driver, 15).until(
                    lambda driver: self.check_login_state()
                )
                logging.info("✅ Login confirmado com sucesso")
                return True
                
            except TimeoutException:
                if self.check_login_state():
                    logging.info("✅ Login verificado manualmente")
                    return True
                return False
            
        except Exception as e:
            logging.error(f"❌ Falha no login: {e}")
            return False
        finally:
            self.end_phase()

    def monitor_network_responses(self, timeout=60):
        """Monitora respostas de rede em tempo real usando CDP"""
        self.start_phase("network_monitoring")
        start_time = time.time()
        
        logging.info("🎯 Monitorando respostas de rede em tempo real...")
        
        try:
            # Configura listener para respostas de rede
            self.driver.execute_cdp_cmd("Network.setRequestInterception", {
                "patterns": [{"urlPattern": "*", "resourceType": "XHR"}]
            })
            
            while time.time() - start_time < timeout:
                try:
                    # Obtém logs de performance
                    logs = self.driver.get_log("performance")
                    self.increment_metric('request_count')
                    
                    for entry in logs:
                        try:
                            message = json.loads(entry["message"])["message"]
                            
                            if message["method"] == "Network.responseReceived":
                                response = message["params"]["response"]
                                url = response["url"]
                                
                                if self.target_endpoint in url and response["status"] == 200:
                                    logging.info(f"✅ Resposta API detectada: {url}")
                                    
                                    # Obtém o corpo da resposta
                                    request_id = message["params"]["requestId"]
                                    result = self.driver.execute_cdp_cmd("Network.getResponseBody", {
                                        "requestId": request_id
                                    })
                                    
                                    if "body" in result:
                                        try:
                                            response_data = json.loads(result["body"])
                                            self.api_response = response_data
                                            self.increment_metric('api_calls')
                                            
                                            # Imprime o JSON formatado
                                            print("\n" + "="*80)
                                            print("🎯 RESPOSTA DA API - JSON FORMATADO")
                                            print("="*80)
                                            print(json.dumps(response_data, indent=2, ensure_ascii=False))
                                            print("="*80)
                                            
                                            logging.info("✅ JSON da API impresso com sucesso!")
                                            return True
                                            
                                        except json.JSONDecodeError:
                                            logging.error("❌ Resposta não é JSON válido")
                                            return False
                        except Exception as e:
                            logging.debug(f"Erro ao processar log de performance: {e}")
                                    
                    time.sleep(1)  # Polling a cada 1 segundo
                    
                except Exception as e:
                    logging.debug(f"Debug network monitoring: {e}")
                    time.sleep(1)
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Erro no monitoramento de rede: {e}")
            return False
        finally:
            self.end_phase()

    def extract_json_from_page(self):
        """Extrai JSON diretamente da página se disponível"""
        try:
            logging.info("🔍 Procurando JSON na página...")
            
            # Procura por dados JSON no DOM
            page_data = self.driver.execute_script("""
                try {
                    // Procura por scripts com dados JSON
                    const scripts = document.querySelectorAll('script[type="application/json"]');
                    for (const script of scripts) {
                        try {
                            const data = JSON.parse(script.textContent);
                            if (data && (data.offers || data.data || data.flights)) {
                                return {success: true, data: data, source: 'script'};
                            }
                        } catch (e) {}
                    }
                    
                    // Procura por dados em atributos data-*
                    const elements = document.querySelectorAll('[data-json], [data-offers]');
                    for (const element of elements) {
                        try {
                            const jsonAttr = element.getAttribute('data-json') || 
                                           element.getAttribute('data-offers');
                            if (jsonAttr) {
                                const data = JSON.parse(jsonAttr);
                                if (data && (data.offers || data.data)) {
                                    return {success: true, data: data, source: 'data-attr'};
                                }
                            }
                        } catch (e) {}
                    }
                    
                    // Procura em variáveis globais
                    const globalVars = ['__REDUX_STATE__', 'initialState', 'appData', 'offersData'];
                    for (const varName of globalVars) {
                        if (window[varName]) {
                            return {success: true, data: window[varName], source: 'global'};
                        }
                    }
                    
                    return {success: false, error: 'No JSON data found'};
                    
                } catch (error) {
                    return {success: false, error: error.toString()};
                }
            """)
            
            if page_data and page_data.get('success'):
                self.api_response = page_data['data']
                self.increment_metric('api_calls')
                
                # Imprime o JSON formatado
                print("\n" + "="*80)
                print(f"🎯 DADOS EXTRAÍDOS DA PÁGINA ({page_data['source']})")
                print("="*80)
                print(json.dumps(page_data['data'], indent=2, ensure_ascii=False))
                print("="*80)
                
                logging.info("✅ JSON extraído da página com sucesso!")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Erro ao extrair JSON da página: {e}")
            return False

    def execute_flow(self):
        """Fluxo principal com monitoramento em tempo real"""
        self.start_phase("main_execution_flow")
        try:
            target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
            
            logging.info(f"🌐 Navegando para página de ofertas...")
            self.driver.get(target_url)
            self.increment_metric('page_loads')
            
            # Aceita cookies
            # self.accept_cookies()
            
            # Verifica estado de login
            is_logged_in = self.check_login_state()
            self.login_verified = is_logged_in
            
            if not is_logged_in:
                logging.info("🔐 Usuário não logado - iniciando autenticação")
                self.increment_metric('login_attempts')
                
                if not self.do_login():
                    logging.error("❌ Falha no processo de login")
                    logging.info("🔄 Continuando sem login...")
                    self.login_verified = False
                else:
                    self.login_verified = True
                    logging.info("✅ Login realizado com sucesso")
            
            # Monitora respostas de rede em tempo real
            if self.monitor_network_responses(timeout=30):
                return True
            
            # Se não detectou via network, tenta extrair da página
            if self.extract_json_from_page():
                return True
            
            logging.error("❌ Não foi possível obter os dados da API")
            return False

        except Exception as e:
            logging.error(f"💥 Erro no fluxo principal: {e}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def run(self):
        """Execução principal"""
        try:
            self.init_performance_log()
            
            logging.info("🎬 Iniciando automação Latam...")
            if not self.start_driver():
                return False
                
            result = self.execute_flow()
            
            if result:
                logging.info("🎉 Automação concluída com sucesso!")
            else:
                # logging.info("🔄 Iniciando renovação de sessão...")

                # 1. Limpeza de sessão
                # if not self.clear_session_data():
                #     return False
                logging.error("💥 Automação falhou")
                
            return result
            
        except KeyboardInterrupt:
            logging.info("⏹️ Execução interrompida pelo usuário")
            return False
        except Exception as e:
            logging.error(f"💥 Erro não tratado: {e}")
            return False
        finally:
            if self.driver:
                try:
                    logging.info("🔚 Fechando navegador...")
                    self.driver.quit()
                    logging.info("✅ Navegador fechado")
                except Exception as e:
                    logging.error(f"❌ Erro ao fechar navegador: {e}")
                
            self.save_performance_log()
            self.print_performance_report()
            
    def clear_session_data(self):
        """Limpa completamente todos os dados de navegação, inclusive cookies, cache, storages e dados salvos."""
        try:
            logging.info("🧹 Iniciando limpeza completa de dados de navegação...")

            # 1. Cookies e cache
            logging.info("🍪 Limpando cookies e cache do navegador...")
            self.driver.delete_all_cookies()
            for cmd in ["Network.clearBrowserCookies", "Network.clearBrowserCache"]:
                try:
                    self.driver.execute_cdp_cmd(cmd, {})
                except Exception as e:
                    logging.warning(f"⚠️ Falha ao executar {cmd}: {e}")

            # 2. Credenciais e autofill
            logging.info(
                "🔑 Limpando credenciais e dados de preenchimento automático..."
            )
            try:
                self.driver.execute_cdp_cmd("Autofill.clear", {})
            except Exception:
                logging.debug("ℹ️ Autofill.clear não suportado, ignorando.")

            try:
                self.driver.execute_cdp_cmd(
                    "Storage.clearDataForOrigin",
                    {"origin": "*", "storageTypes": "passwords"},
                )
            except Exception as e:
                logging.debug(f"ℹ️ Limpeza de senhas não suportada: {e}")

            # 3. Limpeza geral de storages
            storage_types = ",".join(
                [
                    "appcache",
                    "cache_storage",
                    "cookies",
                    "file_systems",
                    "indexeddb",
                    "local_storage",
                    "service_workers",
                    "websql",
                    "shared_storage",
                    "storage_buckets",
                ]
            )
            logging.info(
                "🗄️ Limpando todos os storages e dados de aplicação (origem global)..."
            )
            try:
                self.driver.execute_cdp_cmd(
                    "Storage.clearDataForOrigin",
                    {"origin": "*", "storageTypes": storage_types},
                )
            except Exception as e:
                logging.warning(f"⚠️ Falha ao limpar dados globais: {e}")

            # 4. Fallback com JavaScript
            logging.info("🧠 Executando limpeza via JavaScript (fallback)...")
            self.driver.execute_script(
                """
                (async () => {
                    try {
                        localStorage.clear();
                        sessionStorage.clear();

                        if ('serviceWorker' in navigator) {
                            const registrations = await navigator.serviceWorker.getRegistrations();
                            for (const reg of registrations) {
                                await reg.unregister();
                            }
                        }

                        if (window.indexedDB && indexedDB.databases) {
                            const dbs = await indexedDB.databases();
                            for (const db of dbs) {
                                await indexedDB.deleteDatabase(db.name);
                            }
                        }

                        if (window.caches) {
                            const keys = await caches.keys();
                            for (const key of keys) {
                                await caches.delete(key);
                            }
                        }

                        if (document.forms) {
                            [...document.forms].forEach(f => f.reset());
                        }

                        console.log("✅ Limpeza via JS concluída.");
                    } catch (e) {
                        console.error("Erro na limpeza via JS:", e);
                    }
                })();
            """
            )

            # 5. Limpeza por domínio (caso "*" falhe)
            domains = [
                "https://www.latamairlines.com",
                "https://latamairlines.com",
                "https://latam.absmartly.io",
                "https://api.us1.exponea.com",
                "https://ct.pinterest.com",
                "https://us.creativecdn.com",
                "https://ara.paa-reporting-advertising.amazon",
                "https://rs.fullstory.com",
                "https://gum.criteo.com",
                "https://resources.digital-cloud.medallia.com",
                "https://app.adjust.com",
                "https://v.clarity.ms",
                "https://analytics-fe.digital-cloud.medallia.com",
                "https://www.google.com",
                "https://analytics.google.com",
                "http://localhost",
            ]
            logging.info("🌐 Limpando dados por domínio específico...")
            for domain in domains:
                try:
                    self.driver.execute_cdp_cmd(
                        "Storage.clearDataForOrigin",
                        {"origin": domain, "storageTypes": storage_types},
                    )
                except Exception as e:
                    logging.warning(f"⚠️ Falha ao limpar dados de {domain}: {e}")

            # 6. Força coleta de lixo (GC)
            logging.info("♻️ Forçando coleta de lixo do navegador...")
            try:
                self.driver.execute_cdp_cmd("HeapProfiler.collectGarbage", {})
            except Exception:
                logging.debug("♻️ Coleta de lixo não suportada ou desnecessária.")

            logging.info("✅ Limpeza completa finalizada com sucesso.")
            return True

        except Exception as e:
            logging.error(f"❌ Erro inesperado durante a limpeza: {str(e)}")
            return False

if __name__ == "__main__":
    automation = LatamAutomation()
    success = automation.run()
    exit(0 if success else 1)