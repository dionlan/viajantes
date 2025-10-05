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
        """Configura Chrome para máxima performance"""
        options = Options()
        options.binary_location = self.chrome_path

        os.makedirs(self.automation_profile_path, exist_ok=True)
        
        # 🚀 CONFIGURAÇÕES DE PERFORMANCE
        options.add_argument(f"--user-data-dir={self.automation_profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-images")  # 🚀 BLOQUEIA IMAGENS
        options.add_argument("--disable-gpu")
        
        # Habilita logs de performance
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.images": 2,  # 🚀 BLOQUEIA IMAGENS
            "profile.default_content_setting_values.cookies": 1,
            "profile.default_content_setting_values.javascript": 1,
            "credentials_enable_service": False,  # 🚀 DESABILITA CREDENCIAIS
            "password_manager_enabled": False,    # 🚀 DESABILITA GERENCIADOR DE SENHAS
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
        """Inicia navegador otimizado"""
        self.start_phase("driver_initialization")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            # 🚀 TIMEOUTS REDUZIDOS
            self.driver.set_page_load_timeout(20)
            self.driver.set_script_timeout(15)
            self.driver.implicitly_wait(5)
            
            # Habilita monitoramento de rede
            self.driver.execute_cdp_cmd("Network.enable", {})
            
            # Remove detecção de automação
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
                window.chrome = {runtime: {}};
            """)
            
            logging.info("✅ Navegador iniciado com otimizações")
            self.increment_metric("page_loads")
            return True
            
        except Exception as e:
            logging.error(f"❌ Falha ao iniciar navegador: {e}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verifica estado de login de forma rápida"""
        try:
            # Script mais rápido e confiável
            is_logged_in = self.driver.execute_script("""
                return !document.querySelector('input[type=\"password\"], input[type=\"email\"], #form-input--password, #form-input--alias') &&
                       (document.querySelector('[data-testid=\"nick-name-component\"], .user-profile, [class*=\"user\"], [class*=\"profile\"]') !== null);
            """)
            
            logging.info(f"🔐 Estado de login: {'Logado' if is_logged_in else 'Não logado'}")
            return is_logged_in
            
        except Exception as e:
            logging.warning(f"⚠️ Erro na verificação de login: {e}")
            return False

    def accept_cookies(self):
        """Aceita cookies rapidamente"""
        try:
            # Tenta aceitar cookies de forma não-bloqueante
            self.driver.execute_script("""
                const selectors = [
                    '#cookies-politics-button',
                    'button[data-testid*=\"cookie\"]',
                    'button:contains(\"Aceitar\")',
                    'button:contains(\"Accept\")'
                ];
                
                for (const selector of selectors) {
                    const btn = document.querySelector(selector);
                    if (btn) {
                        btn.click();
                        return true;
                    }
                }
                return false;
            """)
            logging.info("✅ Cookies aceitos (se existirem)")
            return True
        except:
            return False

    def do_login(self):
        """Executa login de forma otimizada"""
        self.start_phase("login_process")
        try:
            logging.info("🔑 Iniciando processo de login...")
            
            # 🚀 MÉTODO DIRETO VIA JAVASCRIPT (MAIS RÁPIDO)
            login_script = """
            function fillField(selector, value) {
                const field = document.querySelector(selector);
                if (field) {
                    field.value = value;
                    field.dispatchEvent(new Event('input', {bubbles: true}));
                    return true;
                }
                return false;
            }
            
            function clickButton(selector) {
                const btn = document.querySelector(selector);
                if (btn) {
                    btn.click();
                    return true;
                }
                return false;
            }
            
            // Tenta preencher email
            if (fillField('#form-input--alias', 'dionlan.alves@gmail.com') || 
                fillField('input[type=\"email\"]', 'dionlan.alves@gmail.com')) {
                
                // Clica para continuar
                if (clickButton('#primary-button') || clickButton('button[type=\"submit\"]')) {
                    // Aguarda um pouco para o próximo passo
                    return 'email_filled';
                }
            }
            return 'failed';
            """
            
            result = self.driver.execute_script(login_script)
            if result == 'email_filled':
                logging.info("✅ Email preenchido")
                time.sleep(2)  # Aguarda carregamento
                
                # Preenche senha
                password_script = """
                if (fillField('#form-input--password', 'Dionlan!@#123') || 
                    fillField('input[type=\"password\"]', 'Dionlan!@#123')) {
                    
                    if (clickButton('#primary-button') || clickButton('button[type=\"submit\"]')) {
                        return 'password_filled';
                    }
                }
                return 'failed';
                """
                
                result = self.driver.execute_script(password_script)
                if result == 'password_filled':
                    logging.info("✅ Senha preenchida e login submetido")
                    
                    # Aguarda login completar
                    time.sleep(3)
                    
                    if self.check_login_state():
                        logging.info("✅ Login confirmado com sucesso")
                        return True
            
            # 🚀 FALLBACK: Método tradicional se JavaScript falhar
            logging.info("🔄 Fallback para método tradicional de login...")
            return self.traditional_login()
            
        except Exception as e:
            logging.error(f"❌ Falha no login: {e}")
            return False
        finally:
            self.end_phase()

    def traditional_login(self):
        """Método tradicional de login (fallback)"""
        try:
            # Preenche email
            email_selectors = [
                (By.ID, "form-input--alias"),
                (By.CSS_SELECTOR, "input[type='email']"),
                (By.NAME, "email")
            ]
            
            for by, selector in email_selectors:
                try:
                    email_field = WebDriverWait(self.driver, 3).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    email_field.clear()
                    email_field.send_keys("dionlan.alves@gmail.com")
                    logging.info("✅ Email preenchido (fallback)")
                    break
                except:
                    continue
            
            # Clica para continuar
            continue_buttons = [
                (By.ID, "primary-button"),
                (By.CSS_SELECTOR, "button[type='submit']")
            ]
            
            for by, selector in continue_buttons:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    button.click()
                    logging.info("✅ Botão de continuar clicado (fallback)")
                    time.sleep(2)
                    break
                except:
                    continue
            
            # Preenche senha
            password_selectors = [
                (By.ID, "form-input--password"),
                (By.CSS_SELECTOR, "input[type='password']")
            ]
            
            for by, selector in password_selectors:
                try:
                    password_field = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((by, selector))
                    )
                    password_field.clear()
                    password_field.send_keys("Dionlan!@#123")
                    logging.info("✅ Senha preenchida (fallback)")
                    break
                except:
                    continue
            
            # Finaliza login
            for by, selector in continue_buttons:
                try:
                    button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    button.click()
                    logging.info("✅ Login finalizado (fallback)")
                    
                    # Verifica sucesso
                    time.sleep(3)
                    return self.check_login_state()
                except:
                    continue
            
            return False
            
        except Exception as e:
            logging.error(f"❌ Falha no login tradicional: {e}")
            return False

    def setup_javascript_interception(self):
        """Configura interceptação JavaScript para capturar respostas da API"""
        try:
            interception_script = """
            // Cria objeto global para armazenar respostas
            window._latamApiInterceptor = {
                responses: [],
                lastResponse: null,
                isMonitoring: true
            };
            
            // Salva XMLHttpRequest original
            const originalXHR = window.XMLHttpRequest;
            
            // Substitui XMLHttpRequest
            window.XMLHttpRequest = function() {
                const xhr = new originalXHR();
                const originalOpen = xhr.open;
                const originalSend = xhr.send;
                
                xhr.open = function(method, url, ...args) {
                    this._url = url;
                    return originalOpen.apply(this, [method, url, ...args]);
                };
                
                xhr.send = function(data) {
                    this.addEventListener('load', function() {
                        if (this._url && this._url.includes('/offers/search/redemption') && this.status === 200) {
                            try {
                                const response = JSON.parse(this.responseText);
                                window._latamApiInterceptor.responses.push(response);
                                window._latamApiInterceptor.lastResponse = response;
                                console.log('🎯 API Response intercepted via XHR:', response);
                            } catch(e) {
                                console.log('❌ Error parsing XHR response:', e);
                            }
                        }
                    });
                    return originalSend.call(this, data);
                };
                
                return xhr;
            };
            
            // Intercepta Fetch API
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                return originalFetch.apply(this, args).then(response => {
                    if (response.url && response.url.includes('/offers/search/redemption') && response.status === 200) {
                        return response.clone().json().then(data => {
                            window._latamApiInterceptor.responses.push(data);
                            window._latamApiInterceptor.lastResponse = data;
                            console.log('🎯 API Response intercepted via Fetch:', data);
                            return response;
                        }).catch(() => response);
                    }
                    return response;
                });
            };
            
            console.log('✅ JavaScript interception configured');
            return true;
            """
            
            self.driver.execute_script(interception_script)
            logging.info("✅ Interceptação JavaScript configurada")
            return True
        except Exception as e:
            logging.error(f"❌ Erro na interceptação JavaScript: {e}")
            return False

    def monitor_api_response(self, timeout=25):
        """Monitora a resposta da API de forma eficiente"""
        self.start_phase("api_monitoring")
        start_time = time.time()
        
        logging.info(f"🎯 Monitorando resposta da API (timeout: {timeout}s)")
        
        # Configura interceptação
        self.setup_javascript_interception()
        
        try:
            last_check = time.time()
            check_interval = 0.5  # Verifica a cada 0.5 segundos
            
            while time.time() - start_time < timeout:
                current_time = time.time()
                
                if current_time - last_check >= check_interval:
                    last_check = current_time
                    
                    # Verifica se há resposta via JavaScript
                    js_result = self.driver.execute_script("""
                        if (window._latamApiInterceptor && window._latamApiInterceptor.lastResponse) {
                            return {
                                success: true, 
                                data: window._latamApiInterceptor.lastResponse,
                                method: 'javascript'
                            };
                        }
                        return {success: false};
                    """)
                    
                    if js_result.get('success'):
                        self.api_response = js_result['data']
                        self.increment_metric('api_calls')
                        
                        # 🎯 IMPRIME JSON IMEDIATAMENTE
                        print("\n" + "="*80)
                        print("🎯 RESPOSTA DA API CAPTURADA VIA JAVASCRIPT")
                        print("="*80)
                        #print(json.dumps(js_result['data'], indent=2, ensure_ascii=False))
                        print("="*80)
                        
                        logging.info("✅ Resposta da API obtida via interceptação JavaScript")
                        return True
                    
                    # Método alternativo: verifica performance entries
                    perf_result = self.driver.execute_script("""
                        try {
                            const entries = performance.getEntriesByType('resource');
                            const apiEntry = entries.find(entry => 
                                entry.name.includes('/offers/search/redemption') && 
                                entry.responseStatus === 200
                            );
                            
                            if (apiEntry) {
                                // Tenta buscar a resposta via fetch
                                return fetch(apiEntry.name, {
                                    method: 'GET',
                                    credentials: 'include',
                                    headers: {'Accept': 'application/json'}
                                }).then(r => r.json()).then(data => ({
                                    success: true, data: data, method: 'performance'
                                })).catch(() => ({success: false}));
                            }
                        } catch(e) {}
                        return {success: false};
                    """)
                    
                    # Se perf_result é uma promise, precisamos esperar
                    if perf_result and not isinstance(perf_result, dict):
                        time.sleep(0.1)
                        continue
                        
                    if perf_result and perf_result.get('success'):
                        self.api_response = perf_result['data']
                        self.increment_metric('api_calls')
                        
                        print("\n" + "="*80)
                        print("🎯 RESPOSTA DA API CAPTURADA VIA PERFORMANCE API")
                        print("="*80)
                        print(json.dumps(perf_result['data'], indent=2, ensure_ascii=False))
                        print("="*80)
                        
                        logging.info("✅ Resposta da API obtida via Performance API")
                        return True
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.1)
            
            logging.warning(f"⏰ Timeout após {timeout}s sem resposta da API")
            return False
            
        except Exception as e:
            logging.error(f"❌ Erro no monitoramento da API: {e}")
            return False
        finally:
            self.end_phase()

    def execute_flow(self):
        """Fluxo principal otimizado"""
        self.start_phase("main_execution_flow")
        try:
            target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
            
            logging.info(f"🌐 Navegando para página de ofertas...")
            self.driver.get(target_url)
            self.increment_metric('page_loads')
            
            # Aceita cookies rapidamente (não bloqueante)
            self.accept_cookies()
            
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
            
            # 🎯 MONITORAMENTO PRINCIPAL DA API
            if self.monitor_api_response(timeout=20):
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

if __name__ == "__main__":
    automation = LatamAutomation()
    success = automation.run()
    exit(0 if success else 1)