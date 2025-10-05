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
from selenium.common.exceptions import TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service

class LatamAutomation:
    def __init__(self):
        self.chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.automation_profile_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", "Default"
        )
        self.target_endpoint = "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        self.response_received = False
        self.login_verified = False
        
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
                'cache_hits': 0
            }
        }
        
        self.setup_logging()
        self.chrome_options = self.configure_chrome()
        self.driver = None

    def setup_logging(self):
        """Configura logging otimizado"""
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
        logging.getLogger('chromedriver').setLevel(logging.ERROR)

    def configure_chrome(self):
        """Configura Chrome com otimizações extremas de performance e persistência"""
        options = Options()
        options.binary_location = self.chrome_path

        # Garante que o diretório do profile existe
        os.makedirs(self.automation_profile_path, exist_ok=True)
        
        # CONFIGURAÇÕES PRINCIPAIS PARA PERFORMANCE E PERSISTÊNCIA
        options.add_argument(f"--user-data-dir={self.automation_profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        
        # OTIMIZAÇÕES DE PERFORMANCE CRÍTICAS
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # CONFIGURAÇÕES DE MEMÓRIA E CPU
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # OTIMIZAÇÕES DE REDE E CACHE
        options.add_argument("--disk-cache-size=524288000")  # 500MB cache
        options.add_argument("--media-cache-size=524288000")
        options.add_argument("--aggressive-cache-discard")
        options.add_argument("--max-decoded-image-size=100000000")
        
        # CONFIGURAÇÕES PARA EVITAR RECARREGAMENTOS DESNECESSÁRIOS
        options.add_argument("--disable-background-networking")
        options.add_argument("--disable-component-update")
        options.add_argument("--disable-default-apps")
        options.add_argument("--disable-sync")
        options.add_argument("--disable-translate")
        options.add_argument("--disable-web-resources")
        options.add_argument("--safebrowsing-disable-auto-update")
        options.add_argument("--metrics-recording-only")
        options.add_argument("--no-first-run")
        options.add_argument("--no-default-browser-check")
        
        # PREFERÊNCIAS PARA PERSISTÊNCIA E PERFORMANCE
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.images": 1,
            "profile.default_content_setting_values.cookies": 1,
            "profile.default_content_setting_values.javascript": 1,
            "profile.default_content_setting_values.popups": 2,
            
            # CONFIGURAÇÕES DE PERSISTÊNCIA
            "credentials_enable_service": True,  # Mantém logins
            "password_manager_enabled": True,    # Gerencia senhas
            "profile.password_manager_enabled": True,
            
            # CONFIGURAÇÕES DE CACHE
            "disk_cache_size": 524288000,
            "media_cache_size": 524288000,
            
            # OTIMIZAÇÕES DE PERFORMANCE
            "autofill.profile_enabled": False,
            "autofill.credit_card_enabled": False,
            "download.default_directory": os.path.join(os.getcwd(), "downloads"),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
        # HABILITA LOGS DE PERFORMANCE
        options.set_capability("goog:loggingPrefs", {'performance': 'INFO'})
        
        logging.info("✅ Chrome configurado para performance máxima e persistência")
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
        """Inicia navegador com otimizações extremas"""
        self.start_phase("driver_initialization")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            self.driver.set_page_load_timeout(20)
            self.driver.set_script_timeout(15)
            self.driver.implicitly_wait(2)  # Reduzido para melhor performance
            
            # Configura network monitoring
            self.driver.execute_cdp_cmd("Network.enable", {})
            self.driver.execute_cdp_cmd("Network.setCacheDisabled", {"cacheDisabled": False})
            
            # Remove detecção de automação
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                Object.defineProperty(navigator, 'chrome', {get: () => undefined});
            """)
            
            logging.info("✅ Navegador iniciado com otimizações de performance")
            self.increment_metric("page_loads")
            return True
            
        except Exception as e:
            logging.error(f"❌ Falha ao iniciar navegador: {e}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verifica estado de login de forma otimizada"""
        try:
            # Verificação ultra-rápida
            script = """
                return !document.querySelector('input#form-input--password') && 
                       !document.querySelector('input#form-input--alias') &&
                       !document.querySelector('button[data-testid="login-button"]');
            """
            is_logged_in = self.driver.execute_script(script)
            logging.info(f"🔐 Estado de login: {'Logado' if is_logged_in else 'Não logado'}")
            return is_logged_in
        except Exception:
            return False

    def accept_cookies(self):
        """Aceita cookies de forma não-bloqueante"""
        try:
            cookie_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.ID, "cookies-politics-button"))
            )
            cookie_button.click()
            logging.info("✅ Cookies aceitos")
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def intercept_response_optimized(self, timeout=25):
        """Método otimizado para interceptar resposta da API"""
        self.start_phase("response_monitoring")
        start_time = time.time()
        
        logging.info("🎯 Monitorando resposta da API...")
        
        while time.time() - start_time < timeout:
            try:
                # Método 1: Verifica performance entries (mais rápido)
                performance_data = self.driver.execute_script("""
                    try {
                        const resources = performance.getEntriesByType('resource');
                        const targetCall = resources.find(res => 
                            res.name.includes('/air-offers/v2/offers/search/redemption') &&
                            res.responseStatus === 200
                        );
                        
                        if (targetCall) {
                            return {
                                success: true,
                                url: targetCall.name,
                                status: targetCall.responseStatus,
                                size: targetCall.transferSize
                            };
                        }
                    } catch (e) {}
                    return {success: false};
                """)
                
                if performance_data.get('success'):
                    logging.info(f"✅ Chamada API detectada: {performance_data['url']}")
                    
                    # Tenta obter os dados via fetch
                    response_data = self.driver.execute_script("""
                        try {
                            return fetch('%s', {
                                method: 'GET',
                                credentials: 'include',
                                headers: {
                                    'Accept': 'application/json',
                                    'Content-Type': 'application/json'
                                }
                            })
                            .then(response => response.json())
                            .then(data => ({success: true, data: data}))
                            .catch(error => ({success: false, error: error.toString()}));
                        } catch (e) {
                            return {success: false, error: e.toString()};
                        }
                    """ % performance_data['url'])
                    
                    if response_data and response_data.get('success'):
                        logging.info("✅ Dados da API obtidos com sucesso!")
                        print(json.dumps(response_data['data'], indent=2))
                        self.response_received = True
                        return True
                
                # Método 2: Verifica se os dados já estão no DOM
                dom_data = self.driver.execute_script("""
                    try {
                        // Procura por scripts com dados JSON
                        const scripts = document.querySelectorAll('script[type="application/json"]');
                        for (const script of scripts) {
                            try {
                                const data = JSON.parse(script.textContent);
                                if (data && (data.offers || data.data || data.flights)) {
                                    return {success: true, data: data};
                                }
                            } catch (e) {}
                        }
                        
                        // Procura em variáveis globais
                        const globalKeys = Object.keys(window);
                        const targetKeys = globalKeys.filter(key => 
                            key.toLowerCase().includes('offer') || 
                            key.toLowerCase().includes('flight')
                        );
                        
                        for (const key of targetKeys) {
                            const data = window[key];
                            if (data && typeof data === 'object' && 
                                (data.offers || data.flights || data.data)) {
                                return {success: true, data: data};
                            }
                        }
                    } catch (e) {}
                    return {success: false};
                """)
                
                if dom_data.get('success'):
                    logging.info("✅ Dados encontrados no DOM")
                    print(json.dumps(dom_data['data'], indent=2))
                    self.response_received = True
                    return True
                
                time.sleep(1)  # Polling mais espaçado para performance
                
            except Exception as e:
                logging.debug(f"Debug: {e}")
                time.sleep(1)
        
        return False

    def execute_flow(self):
        """Fluxo principal otimizado"""
        self.start_phase("main_execution_flow")
        try:
            # URL otimizada com parâmetros específicos
            target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
            
            logging.info(f"🌐 Navegando para página de ofertas...")
            self.driver.get(target_url)
            self.increment_metric('page_loads')
            
            # Aceita cookies rapidamente
            #self.accept_cookies()
            
            # Verifica estado de login de forma rápida
            is_logged_in = self.check_login_state()
            self.login_verified = is_logged_in
            
            if not is_logged_in:
                logging.info("🔐 Usuário não logado - iniciando autenticação")
                self.increment_metric('login_attempts')
                
                if not self.do_login():
                    logging.error("❌ Falha no processo de login")
                    return False
                
                self.login_verified = True
                logging.info("✅ Login realizado com sucesso")
            
            # Aguarda breve momento para carregamento completo
            time.sleep(2)
            
            # Intercepta resposta da API
            if self.intercept_response_optimized(timeout=20):
                return True
                
            logging.error("❌ Não foi possível obter os dados da API")
            return False

        except Exception as e:
            logging.error(f"💥 Erro no fluxo principal: {e}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def do_login(self):
        """Executa login de forma otimizada"""
        self.start_phase("login_process")
        try:
            logging.info("🔑 Iniciando processo de login...")
            
            # Preenche e-mail
            if not self.fill_field("form-input--alias", "dionlan.alves@gmail.com", timeout=5):
                return False
                
            if not self.click_element("primary-button", timeout=5):
                return False
                
            # Aguarda campo de senha
            if not self.wait_for_element("form-input--password", timeout=8):
                return False
                
            # Preenche senha
            if not self.fill_field("form-input--password", "Dionlan!@#123", timeout=5):
                return False
                
            if not self.click_element("primary-button", timeout=5):
                return False
            
            # Verificação rápida de login
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda d: d.execute_script(
                        'return !!document.querySelector(\'[data-testid="nick-name-component"]\');'
                    )
                )
                logging.info("✅ Login confirmado")
                return True
            except TimeoutException:
                logging.error("❌ Timeout ao confirmar login")
                return False
            
        except Exception as e:
            logging.error(f"❌ Falha no login: {e}")
            return False
        finally:
            self.end_phase()

    def fill_field(self, locator, value, locator_type=By.ID, timeout=5):
        """Preenche campo de forma otimizada"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator)))
            element.clear()
            element.send_keys(value)
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def click_element(self, locator, locator_type=By.ID, timeout=5):
        """Clica em elemento de forma otimizada"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((locator_type, locator)))
            element.click()
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

    def wait_for_element(self, locator, locator_type=By.ID, timeout=5):
        """Aguarda elemento de forma otimizada"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator)))
            return True
        except TimeoutException:
            return False
        except Exception:
            return False

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
                except Exception:
                    pass
                
            self.save_performance_log()
            self.print_performance_report()

if __name__ == "__main__":
    automation = LatamAutomation()
    success = automation.run()
    exit(0 if success else 1)