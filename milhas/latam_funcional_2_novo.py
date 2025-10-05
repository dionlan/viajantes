import os
import json
import logging
import time
import random
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
        # Usar perfil temporário para evitar persistência
        self.automation_profile_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", "Default")
        self.target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
        self.login_url = "https://accounts.latamairlines.com/login"
        self.home_url = "https://www.latamairlines.com/br/pt"
        self.target_endpoint = "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        self.response_received = False
        self.login_verified = False
        self.api_response = None
        self.credentials = {
            'email': 'dionlan.alves@gmail.com',
            'password': 'Dionlan!@#123'
        }
        self.captured_requests = []
        
        # Novos atributos para controle de sessão
        self.session_recovery_attempts = 0
        self.max_session_recovery_attempts = 2
        
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
                'api_calls': 0,
                '403_errors': 0,
                'session_recoveries': 0,
                'profile_changes': 0
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
        """Configura Chrome com opções avançadas de privacidade"""
        options = Options()
        options.binary_location = self.chrome_path

        os.makedirs(self.automation_profile_path, exist_ok=True)
        
        # CONFIGURAÇÕES AVANÇADAS PARA PRIVACIDADE
        options.add_argument(f"--user-data-dir={self.automation_profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # CONFIGURAÇÕES DE PRIVACIDADE E SEGURANÇA
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-gpu")
        options.add_argument("--log-level=3")
        options.add_argument("--disable-logging")
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        options.add_argument("--disable-component-extensions-with-background-pages")
        options.add_argument("--disable-site-isolation-trials")
        options.add_argument("--disable-features=TranslateUI")
        options.add_argument("--disable-ipc-flooding-protection")
        options.add_argument("--disable-hang-monitor")
        options.add_argument("--disable-prompt-on-repost")
        options.add_argument("--disable-domain-reliability")
        options.add_argument("--disable-back-forward-cache")
        options.add_argument("--disable-client-side-phishing-detection")
        
        # USER AGENT REALISTA E VARIÁVEL
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
        ]
        options.add_argument(f"--user-agent={random.choice(user_agents)}")
        
        # 🎯 ABRIR DEVTOOLS AUTOMATICAMENTE
        options.add_argument("--auto-open-devtools-for-tabs")
        
        # Habilita logs de performance
        options.set_capability("goog:loggingPrefs", {'performance': 'ALL'})
        
        prefs = {
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_setting_values.geolocation": 2,
            "profile.default_content_setting_values.images": 1,
            "profile.default_content_setting_values.cookies": 2,  # Bloquear cookies de terceiros
            "profile.default_content_setting_values.javascript": 1,
            "profile.default_content_setting_values.plugins": 2,
            "profile.default_content_setting_values.popups": 2,
            "profile.default_content_setting_values.media_stream": 2,
            "credentials_enable_service": False,
            "password_manager_enabled": False,
            "profile.password_manager_enabled": False,
            "devtools.preferences.currentDockState": '"bottom"',
            "devtools.preferences.networkPanelSelectedFilter": '"all"',
            "devtools.preferences.showNetworkOverview": True,
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
        """Inicia navegador com configurações avançadas"""
        self.start_phase("driver_initialization")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            
            self.driver.set_page_load_timeout(30)
            self.driver.set_script_timeout(20)
            self.driver.implicitly_wait(10)
            
            # Habilita monitoramento de rede
            self.driver.execute_cdp_cmd("Network.enable", {})
            
            # Remove detecção de automação de forma mais avançada
            self.driver.execute_script("""
                // Override the plugins property to use a custom getter
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });

                // Override the languages property to use a custom getter
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en'],
                });

                // Override the webdriver property to use a custom getter
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Pass the Chrome Test
                window.chrome = {
                    runtime: {},
                    // etc.
                };

                // Pass the Permissions Test
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Override geolocation
                Object.defineProperty(navigator, 'geolocation', {
                    value: {
                        getCurrentPosition: () => {},
                        watchPosition: () => {},
                        clearWatch: () => {}
                    }
                });
            """)
            
            logging.info("✅ Navegador iniciado com configurações avançadas de privacidade")
            
            self.increment_metric("page_loads")
            return True
            
        except Exception as e:
            logging.error(f"❌ Falha ao iniciar navegador: {e}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verificação de login precisa"""
        try:
            login_state = self.driver.execute_script("""
                try {
                    const isLoginPage = window.location.href.includes('accounts.latamairlines.com/login');
                    const loginElements = document.querySelectorAll('#form-input--alias, #form-input--password');
                    const userElements = document.querySelectorAll('[data-testid="nick-name-component"], [class*="user"]');
                    
                    if (isLoginPage || loginElements.length > 0) {
                        return {status: 'login_required', reason: 'login_page_or_elements'};
                    }
                    
                    if (userElements.length > 0) {
                        return {status: 'logged_in', reason: 'user_elements_found'};
                    }
                    
                    return {status: 'unknown', reason: 'no_clear_indicators'};
                    
                } catch(e) {
                    return {status: 'error', reason: e.message};
                }
            """)
            
            if login_state and 'status' in login_state:
                status = login_state['status']
                if status == 'logged_in':
                    logging.info("🔐 Estado de login: LOGADO")
                    return True
                elif status == 'login_required':
                    logging.info("🔐 Estado de login: LOGIN NECESSÁRIO")
                    return False
                else:
                    logging.info("🔐 Estado de login: INDETERMINADO")
                    return None
            return None
                
        except Exception as e:
            logging.warning(f"⚠️ Erro na verificação de login: {e}")
            return None

    def wait_for_page_load(self, timeout=15):
        """Aguarda o carregamento completo da página"""
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState === 'complete'")
            )
            logging.info("✅ Página carregada completamente")
            return True
        except TimeoutException:
            logging.warning("⚠️ Timeout no carregamento da página")
            return False

    def handle_cookies_popup(self):
        """Lida com o popup de cookies se estiver presente"""
        try:
            # Aguarda o botão de cookies aparecer
            cookies_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[data-testid="cookies-politics-button--button"]'))
            )
            
            logging.info("🍪 Popup de cookies detectado - clicando em 'Aceite todos os cookies'")
            cookies_button.click()
            time.sleep(2)
            logging.info("✅ Cookies aceitos")
            return True
            
        except TimeoutException:
            logging.info("ℹ️ Nenhum popup de cookies detectado")
            return True
        except Exception as e:
            logging.warning(f"⚠️ Erro ao lidar com popup de cookies: {e}")
            return False

    def click_login_button(self):
        """Clica no botão de login na página inicial com múltiplas estratégias"""
        try:
            logging.info("🔑 Procurando botão de login...")
            
            # Estratégia 1: Buscar pelo ID específico
            try:
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, 'button#header__profile__lnk-sign-in'))
                )
                logging.info("✅ Botão de login encontrado pelo ID")
            except TimeoutException:
                # Estratégia 2: Buscar por texto
                logging.info("🔍 Buscando botão de login por texto...")
                login_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, '//button[contains(text(), "Fazer login") or contains(text(), "Entrar")]'))
                )
                logging.info("✅ Botão de login encontrado por texto")
            
            logging.info("🖱️ Clicando no botão de login")
            login_button.click()
            time.sleep(3)
            
            # Aguarda redirecionamento para página de login
            WebDriverWait(self.driver, 10).until(
                EC.url_contains('accounts.latamairlines.com/login')
            )
            
            logging.info("✅ Redirecionado para página de login")
            return True
            
        except TimeoutException:
            logging.error("❌ Timeout ao encontrar/clicar no botão de login")
            return False
        except Exception as e:
            logging.error(f"❌ Erro ao clicar no botão de login: {e}")
            return False

    def clear_session_data_advanced(self):
        """Limpeza profunda de todos os dados de sessão"""
        try:
            logging.info("🧹🧹🧹 LIMPEZA PROFUNDA DE DADOS INICIADA...")
            
            # 1. Limpa cookies via Selenium
            self.driver.delete_all_cookies()
            logging.info("✅ Cookies do navegador removidos")
            
            # 2. Limpeza JavaScript avançada
            deep_clean_script = """
            try {
                console.log('🧹 Iniciando limpeza profunda...');
                
                // Limpa todos os storages
                localStorage.clear();
                sessionStorage.clear();
                console.log('✅ Storages limpos');
                
                // Limpa indexedDB
                if (window.indexedDB) {
                    indexedDB.databases().then(databases => {
                        databases.forEach(db => {
                            if (db.name) {
                                indexedDB.deleteDatabase(db.name);
                                console.log('🗑️ Deletado database:', db.name);
                            }
                        });
                    }).catch(e => console.log('ℹ️ IndexedDB já limpo'));
                }
                
                // Limpa service workers
                if (navigator.serviceWorker) {
                    navigator.serviceWorker.getRegistrations().then(registrations => {
                        registrations.forEach(registration => {
                            registration.unregister();
                            console.log('🗑️ Service Worker removido:', registration.scope);
                        });
                    }).catch(e => console.log('ℹ️ Service Workers já limpos'));
                }
                
                // Limpa caches
                if (window.caches) {
                    caches.keys().then(cacheNames => {
                        cacheNames.forEach(cacheName => {
                            caches.delete(cacheName);
                            console.log('🗑️ Cache removido:', cacheName);
                        });
                    }).catch(e => console.log('ℹ️ Caches já limpos'));
                }
                
                // Limpa dados de performance
                if (window.performance && performance.clearResourceTimings) {
                    performance.clearResourceTimings();
                    console.log('✅ Performance data limpo');
                }
                
                // Limpa todas as variáveis globais que podem conter dados de sessão
                const sensitiveKeys = ['session', 'token', 'auth', 'user', 'login', 'profile', 'latam'];
                sensitiveKeys.forEach(key => {
                    try {
                        if (window[key]) delete window[key];
                    } catch(e) {}
                });
                
                console.log('🎉 Limpeza profunda concluída');
                return {success: true, message: 'Limpeza profunda concluída'};
                
            } catch(e) {
                console.error('❌ Erro na limpeza:', e);
                return {success: false, error: e.message};
            }
            """
            
            result = self.driver.execute_script(deep_clean_script)
            if result and result.get('success'):
                logging.info("✅ Limpeza JavaScript profunda concluída")
            else:
                logging.warning("⚠️ Limpeza JavaScript pode não ter sido completa")
            
            # 3. Limpa dados de aplicação via CDP
            try:
                self.driver.execute_cdp_cmd('Storage.clearDataForOrigin', {
                    "origin": "*",
                    "storageTypes": "all"
                })
                logging.info("✅ Dados de origem limpos via CDP")
            except Exception as e:
                logging.warning(f"⚠️ Não foi possível limpar dados via CDP: {e}")
            
            # 4. Aguarda um pouco para garantir limpeza
            time.sleep(3)
            
            logging.info("🧹🧹🧹 LIMPEZA PROFUNDA CONCLUÍDA")
            return True
            
        except Exception as e:
            logging.error(f"❌ Erro na limpeza profunda: {e}")
            return False

    def execute_latam_login_flow(self):
        """Executa o fluxo específico de login da LATAM com verificação"""
        self.start_phase("login_process")
        self.increment_metric('login_attempts')
        
        try:
            logging.info("🔑 Iniciando fluxo de login da LATAM...")
            
            # Verifica se já está na página de login correta
            current_url = self.driver.current_url
            if 'accounts.latamairlines.com/login' not in current_url:
                logging.info("🌐 Navegando para página de login...")
                self.driver.get(self.login_url)
                if not self.wait_for_page_load(15):
                    return False

            # Verifica se precisa preencher email (pode já estar logado)
            try:
                email_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "form-input--alias"))
                )
                
                if email_input.is_displayed() and email_input.is_enabled():
                    logging.info("📧 Preenchendo email...")
                    email_input.clear()
                    email_input.send_keys(self.credentials['email'])
                    logging.info("✅ Email preenchido")

                    # Clica em Continuar
                    continue_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "primary-button"))
                    )
                    continue_button.click()
                    logging.info("✅ Continuar clicado")
                    time.sleep(3)
                else:
                    logging.info("ℹ️ Campo de email não está visível, pode já estar autenticado")
                    
            except TimeoutException:
                logging.info("ℹ️ Campo de email não encontrado, verificando se já está autenticado...")

            # Verifica se precisa preencher senha
            try:
                password_input = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.ID, "form-input--password"))
                )
                
                if password_input.is_displayed() and password_input.is_enabled():
                    logging.info("🔒 Preenchendo senha...")
                    password_input.clear()
                    password_input.send_keys(self.credentials['password'])
                    logging.info("✅ Senha preenchida")

                    # Clica em Fazer login
                    login_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.ID, "primary-button"))
                    )
                    login_button.click()
                    logging.info("✅ Fazer login clicado")
                else:
                    logging.info("ℹ️ Campo de senha não está visível")
                    
            except TimeoutException:
                logging.info("ℹ️ Campo de senha não encontrado, pode já estar logado")

            # Aguarda redirecionamento
            logging.info("⏳ Aguardando redirecionamento pós-login...")
            time.sleep(8)
            
            # Verifica se o login foi bem sucedido
            login_state = self.check_login_state()
            if login_state:
                logging.info(f"✅ Login realizado com sucesso! URL atual: {self.driver.current_url}")
                return True
            else:
                logging.warning("⚠️ Estado de login não confirmado após tentativa")
                return False

        except Exception as e:
            logging.error(f"❌ Erro durante o fluxo de login: {e}")
            return False
        finally:
            self.end_phase()

    def handle_403_error(self):
        """Processa erro 403 com limpeza profunda e estratégias avançadas"""
        self.start_phase("403_error_recovery")
        self.increment_metric('403_errors')
        self.session_recovery_attempts += 1
        
        logging.warning(f"🔒 ERRO 403 DETECTADO. TENTATIVA DE RECUPERAÇÃO #{self.session_recovery_attempts}")
        
        try:
            # ESTRATÉGIA 1: Limpeza profunda completa
            if not self.clear_session_data_advanced():
                logging.error("❌ Falha na limpeza profunda de dados")
                return False
            
            # ESTRATÉGIA 2: Aguarda um tempo aleatório (comportamento humano)
            wait_time = random.uniform(3, 8)
            logging.info(f"⏳ Aguardando {wait_time:.1f}s (comportamento humano)...")
            time.sleep(wait_time)
            
            # ESTRATÉGIA 3: Navega para página inicial limpa
            logging.info("🏠 Navegando para página inicial limpa...")
            self.driver.get(self.home_url)
            time.sleep(3)
            
            if not self.wait_for_page_load(15):
                logging.warning("⚠️ Timeout no carregamento da página inicial")
            
            # ESTRATÉGIA 4: Aceita cookies
            if not self.handle_cookies_popup():
                logging.warning("⚠️ Problema ao lidar com popup de cookies")
            
            # ESTRATÉGIA 5: Aguarda mais um pouco
            time.sleep(2)
            
            # ESTRATÉGIA 6: Clica no login
            if not self.click_login_button():
                logging.error("❌ Falha ao clicar no botão de login")
                return False
            
            # ESTRATÉGIA 7: Executa fluxo de login
            if self.execute_latam_login_flow():
                logging.info("✅ Login realizado com sucesso após erro 403")
                self.increment_metric('session_recoveries')
                
                # ESTRATÉGIA 8: Navega de volta para a URL alvo
                logging.info("🌐 Navegando de volta para URL alvo...")
                self.driver.get(self.target_url)
                if not self.wait_for_page_load(15):
                    return False
                
                # ESTRATÉGIA 9: Lida com cookies novamente
                self.handle_cookies_popup()
                
                # ESTRATÉGIA 10: Aguarda um tempo antes de retentar
                time.sleep(5)
                
                return True
            else:
                logging.error("❌ Falha no login após erro 403")
                return False
                
        except Exception as e:
            logging.error(f"❌ Erro crítico no tratamento de 403: {e}")
            return False
        finally:
            self.end_phase()

    # ... (mantenha os métodos restantes igual ao código anterior: setup_javascript_interception, monitor_network_responses_detailed, check_javascript_interception, force_api_trigger, monitor_api_comprehensive, execute_complete_flow, run)

    def setup_javascript_interception(self):
        """Configura interceptação JavaScript para capturar respostas incluindo status code"""
        try:
            interception_script = """
            // Cria objeto global para interceptação
            window._latamApiInterceptor = {
                responses: [],
                lastResponse: null,
                requestCount: 0,
                responseCount: 0,
                
                storeResponse: function(response, method, status) {
                    const responseData = {
                        data: response,
                        timestamp: Date.now(),
                        method: method,
                        status: status
                    };
                    this.responses.push(responseData);
                    this.lastResponse = responseData;
                    this.responseCount++;
                    console.log('🔍 Resposta API capturada via ' + method + '. Status: ' + status + '. Total: ' + this.responseCount);
                }
            };

            // Intercepta Fetch API
            const originalFetch = window.fetch;
            window.fetch = function(...args) {
                const url = args[0];
                const startTime = Date.now();
                
                return originalFetch.apply(this, args).then(response => {
                    if (response.url && response.url.includes('/offers/search/redemption')) {
                        console.log('🎯 Fetch API chamada para:', response.url, 'Status:', response.status);
                        
                        return response.clone().json().then(data => {
                            window._latamApiInterceptor.storeResponse(data, 'fetch', response.status);
                            return response;
                        }).catch(err => {
                            console.log('❌ Erro ao parsear fetch response:', err);
                            // Armazena resposta mesmo com erro de parse
                            window._latamApiInterceptor.storeResponse({error: err.message}, 'fetch', response.status);
                            return response;
                        });
                    }
                    return response;
                });
            };

            // Intercepta XMLHttpRequest
            const OriginalXHR = window.XMLHttpRequest;
            window.XMLHttpRequest = function() {
                const xhr = new OriginalXHR();
                const originalOpen = xhr.open;
                const originalSend = xhr.send;

                xhr.open = function(method, url, ...rest) {
                    this._url = url;
                    this._method = method;
                    return originalOpen.call(this, method, url, ...rest);
                };

                xhr.send = function(data) {
                    this.addEventListener('load', () => {
                        if (this._url && this._url.includes('/offers/search/redemption')) {
                            console.log('🎯 XHR carregado:', this._url, 'Status:', this.status);
                            
                            try {
                                const responseData = this.status === 200 ? JSON.parse(this.responseText) : {error: this.statusText};
                                window._latamApiInterceptor.storeResponse(responseData, 'xhr', this.status);
                            } catch (err) {
                                console.log('❌ Erro ao parsear XHR response:', err);
                                window._latamApiInterceptor.storeResponse({error: err.message}, 'xhr', this.status);
                            }
                        }
                    });
                    
                    this.addEventListener('error', () => {
                        if (this._url && this._url.includes('/offers/search/redemption')) {
                            console.log('❌ XHR erro para:', this._url);
                        }
                    });
                    
                    return originalSend.call(this, data);
                };

                return xhr;
            };

            console.log('✅ Interceptação JavaScript configurada - Pronta para capturar respostas da API');
            return true;
            """
            
            self.driver.execute_script(interception_script)
            logging.info("✅ Interceptação JavaScript configurada")
            return True
        except Exception as e:
            logging.error(f"❌ Erro na interceptação JavaScript: {e}")
            return False

    def monitor_network_responses_detailed(self):
        """Monitora respostas de rede de forma detalhada usando performance logs"""
        try:
            logs = self.driver.get_log('performance')
            
            for entry in logs:
                try:
                    message = json.loads(entry['message'])['message']
                    
                    # Captura responses recebidas
                    if message['method'] == 'Network.responseReceived':
                        response = message['params']['response']
                        url = response['url']
                        
                        if '/offers/search/redemption' in url:
                            logging.info(f"📥 Response detectado: {url} - Status: {response['status']}")
                            
                            # Para respostas de sucesso, tenta obter o corpo
                            if response['status'] == 200:
                                try:
                                    request_id = message['params']['requestId']
                                    result = self.driver.execute_cdp_cmd("Network.getResponseBody", {
                                        "requestId": request_id
                                    })
                                    
                                    if "body" in result:
                                        response_data = json.loads(result["body"])
                                        self.api_response = response_data
                                        self.increment_metric('api_calls')
                                        
                                        print("\n" + "="*80)
                                        print("🎯 RESPOSTA DA API CAPTURADA VIA NETWORK LOGS!")
                                        print("="*80)
                                        print(f"📊 Status: {response['status']}")
                                        print(f"🔗 URL: {url}")
                                        print("="*80)
                                        print(json.dumps(response_data, indent=2, ensure_ascii=False))
                                        print("="*80)
                                        
                                        return True
                                        
                                except Exception as e:
                                    logging.debug(f"⚠️ Não foi possível obter response body: {e}")
                            
                            # Processa erro 403
                            elif response['status'] == 403:
                                logging.error(f"❌ ACESSO PROIBIDO (403) para: {url}")
                                if self.session_recovery_attempts < self.max_session_recovery_attempts:
                                    if self.handle_403_error():
                                        logging.info("🔄 Retentando após recuperação de sessão...")
                                        # Retorna False para continuar o monitoramento com nova sessão
                                        return False
                                else:
                                    logging.error("❌ Número máximo de tentativas de recuperação excedido")
                                    return False
                                    
                            elif response['status'] >= 400:
                                logging.warning(f"⚠️ Erro HTTP {response['status']} para: {url}")
                                
                except Exception as e:
                    continue
                    
            return False
            
        except Exception as e:
            logging.debug(f"⚠️ Erro ao monitorar network responses: {e}")
            return False

    def check_javascript_interception(self):
        """Verifica se a interceptação JavaScript capturou alguma resposta"""
        try:
            result = self.driver.execute_script("""
                if (window._latamApiInterceptor && window._latamApiInterceptor.lastResponse) {
                    return {
                        success: true,
                        data: window._latamApiInterceptor.lastResponse,
                        responseCount: window._latamApiInterceptor.responseCount,
                        method: 'javascript'
                    };
                }
                return {success: false};
            """)
            
            if result and result.get('success'):
                response_data = result['data']
                
                # Verifica o status code da resposta
                status = response_data.get('status', 200)
                
                if status == 403:
                    logging.error("❌ Erro 403 detectado via JavaScript interception")
                    if self.session_recovery_attempts < self.max_session_recovery_attempts:
                        if self.handle_403_error():
                            logging.info("🔄 Retentando após recuperação de sessão...")
                            return False
                    else:
                        logging.error("❌ Número máximo de tentativas de recuperação excedido")
                        return False
                
                elif status == 200:
                    self.api_response = response_data['data']
                    self.increment_metric('api_calls')
                    
                    print("\n" + "="*80)
                    print("🎯 RESPOSTA DA API CAPTURADA VIA JAVASCRIPT!")
                    print("="*80)
                    print(f"📊 Status: {status}")
                    print(f"📊 Total de respostas: {result.get('responseCount', 0)}")
                    print(f"🔧 Método: {result.get('method')}")
                    print("="*80)
                    print(json.dumps(response_data['data'], indent=2, ensure_ascii=False))
                    print("="*80)
                    
                    return True
                
            return False
            
        except Exception as e:
            logging.debug(f"⚠️ Erro ao verificar interceptação JavaScript: {e}")
            return False

    def force_api_trigger(self):
        """Tenta forçar o disparo da API se necessário"""
        try:
            logging.info("🔄 Tentando forçar disparo da API...")
            
            # Script para tentar interagir com a página e disparar a API
            trigger_script = """
            try {
                // Tenta encontrar e clicar em elementos que podem disparar a busca
                const buttons = document.querySelectorAll('button, [role="button"], [onclick]');
                let clicked = false;
                
                for (let btn of buttons) {
                    const text = btn.textContent?.toLowerCase() || '';
                    if (text.includes('buscar') || text.includes('pesquisar') || 
                        text.includes('search') || btn.getAttribute('data-testid')?.includes('search')) {
                        
                        if (btn.offsetParent !== null) { // Elemento visível
                            btn.click();
                            console.log('✅ Botão clicado:', text);
                            clicked = true;
                            break;
                        }
                    }
                }
                
                // Se não encontrou botões, tenta via JavaScript
                if (!clicked) {
                    // Dispara evento de scroll ou resize que pode acionar a API
                    window.dispatchEvent(new Event('scroll'));
                    window.dispatchEvent(new Event('resize'));
                    console.log('✅ Eventos disparados');
                }
                
                return {success: true, clicked: clicked};
                
            } catch(e) {
                return {success: false, error: e.message};
            }
            """
            
            result = self.driver.execute_script(trigger_script)
            if result and result.get('success'):
                logging.info(f"✅ Trigger executado - clique: {result.get('clicked', False)}")
                time.sleep(2)  # Aguarda possível carregamento
            return True
            
        except Exception as e:
            logging.warning(f"⚠️ Erro ao forçar trigger: {e}")
            return False

    def monitor_api_comprehensive(self, timeout=60):
        """Monitoramento abrangente da API com tratamento de 403"""
        self.start_phase("api_monitoring")
        start_time = time.time()
        
        logging.info(f"🎯 Iniciando monitoramento abrangente da API (timeout: {timeout}s)")
        
        # Configura interceptação JavaScript
        if not self.setup_javascript_interception():
            logging.error("❌ Falha na configuração da interceptação")
            return False

        try:
            last_trigger_time = time.time()
            trigger_interval = 10  # Tenta forçar API a cada 10 segundos
            
            while time.time() - start_time < timeout:
                current_time = time.time()
                
                # Verifica se excedeu o número máximo de recuperações
                if self.session_recovery_attempts >= self.max_session_recovery_attempts:
                    logging.error("❌ Número máximo de recuperações de sessão excedido")
                    return False
                
                # 🎯 ESTRATÉGIA 1: Verifica interceptação JavaScript
                js_result = self.check_javascript_interception()
                if js_result is True:
                    logging.info("✅ Resposta capturada via JavaScript interception")
                    return True
                elif js_result is False and self.session_recovery_attempts > 0:
                    # Se houve recuperação de sessão, continua monitorando
                    continue
                
                # 🎯 ESTRATÉGIA 2: Monitora logs de performance
                network_result = self.monitor_network_responses_detailed()
                if network_result is True:
                    logging.info("✅ Resposta capturada via network logs")
                    return True
                elif network_result is False and self.session_recovery_attempts > 0:
                    # Se houve recuperação de sessão, continua monitorando
                    continue
                
                # 🎯 ESTRATÉGIA 3: Força trigger periódico
                if current_time - last_trigger_time >= trigger_interval:
                    last_trigger_time = current_time
                    self.force_api_trigger()
                
                # Pequena pausa para não sobrecarregar
                time.sleep(0.5)
                
                # Log de progresso
                elapsed = current_time - start_time
                if int(elapsed) % 5 == 0 and int(elapsed) > 0:
                    logging.info(f"⏳ Monitorando... ({elapsed:.1f}s)")
            
            logging.warning(f"⏰ Timeout após {timeout}s")
            return False
            
        except Exception as e:
            logging.error(f"❌ Erro no monitoramento: {e}")
            return False
        finally:
            self.end_phase()

    def execute_complete_flow(self):
        """Executa o fluxo completo"""
        self.start_phase("main_execution_flow")
        
        try:
            # Navega para a URL alvo
            logging.info(f"🌐 Navegando para: {self.target_url}")
            self.driver.get(self.target_url)
            self.increment_metric('page_loads')
            
            if not self.wait_for_page_load(20):
                return False

            # Lida com popup de cookies na primeira carga
            self.handle_cookies_popup()

            # Verifica estado de login
            login_state = self.check_login_state()
            
            if login_state is False:
                logging.info("🔐 Login necessário - executando fluxo de autenticação")
                
                # Clica no botão de login primeiro
                if not self.click_login_button():
                    return False
                
                if not self.execute_latam_login_flow():
                    return False
                
                # Navega novamente após login
                current_url = self.driver.current_url
                if 'latamairlines.com/br/pt/oferta-voos' not in current_url:
                    logging.info("🔄 Navegando para URL alvo após login...")
                    self.driver.get(self.target_url)
                    if not self.wait_for_page_load(15):
                        return False
                
                # Lida com cookies novamente após navegação
                self.handle_cookies_popup()

            # Monitora a API com estratégia abrangente
            if self.monitor_api_comprehensive(timeout=60):
                self.login_verified = True
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
                
            result = self.execute_complete_flow()
            
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
                    logging.info("⏳ Mantendo browser aberto para inspeção...")
                    time.sleep(10)
                    
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