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
from selenium.common.exceptions import TimeoutException, WebDriverException

class LatamAutomation:
    def __init__(self):
        self.chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.user_data_dir = os.path.join(os.environ['USERPROFILE'], 'AppData', 'Local', 'Google', 'Chrome', 'User Data')
        self.target_endpoint = "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        self.driver = None
        self.response_received = False
        self.login_verified = False
        self.session_retry_count = 0
        self.max_session_retries = 3
        self.last_session_renewal = 0
        self.session_timeout = 300  # 5 minutos entre renovações
        
        # Configuração de performance logging
        self.performance_log_file = "performance_log.json"
        self.current_phase = None
        self.performance_data = {
            'execution_id': datetime.now().strftime("%Y%m%d_%H%M%S"),
            'start_time': None,
            'end_time': None,
            'phases': {},
            'metrics': {
                'request_count': 0,
                'error_count': 0,
                'session_renewals': 0,
                'page_loads': 0,
                'login_attempts': 0
            }
        }
        
        self.setup_logging()
        self.chrome_options = self.configure_chrome()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='[%(levelname)s] %(asctime)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler('automation.log', mode='a', encoding='utf-8')
            ]
        )
        logging.info("Sistema de logging configurado")

    def configure_chrome(self):
        """Configura as opções do Chrome para máxima performance"""
        options = Options()
        options.binary_location = self.chrome_path
        temp_profile = os.path.join(self.user_data_dir, 'AutomationTemp')
        os.makedirs(temp_profile, exist_ok=True)

        options.add_argument(f"user-data-dir={temp_profile}")
        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        # Otimizações de performance
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-notifications")
        options.add_argument("--disable-popup-blocking")
        
        # Configuração de rede
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.set_capability("goog:chromeOptions", {
            "perfLoggingPrefs": {
                "enableNetwork": True,
                "enablePage": False,
                "enableTimeline": False
            },
            "args": ["--enable-logging", "--v=1"]
        })
        
        return options

    def init_performance_log(self):
        """Inicializa o registro de performance"""
        self.performance_data['start_time'] = datetime.now().isoformat()
        self.start_phase("initialization")

    def start_phase(self, phase_name):
        """Registra o início de uma fase com timestamp"""
        if self.current_phase:
            self.end_phase()
            
        self.current_phase = phase_name
        self.performance_data['phases'][phase_name] = {
            'start': datetime.now().isoformat(),
            'end': None,
            'duration': None
        }
        logging.debug(f"Iniciando fase: {phase_name}")

    def end_phase(self):
        """Finaliza a fase atual calculando a duração"""
        if self.current_phase:
            phase_data = self.performance_data['phases'][self.current_phase]
            phase_data['end'] = datetime.now().isoformat()
            start = datetime.fromisoformat(phase_data['start'])
            end = datetime.fromisoformat(phase_data['end'])
            phase_data['duration'] = (end - start).total_seconds()
            logging.debug(f"Fase {self.current_phase} concluída em {phase_data['duration']:.2f}s")
            self.current_phase = None

    def increment_metric(self, metric_name):
        """Incrementa um contador de métrica"""
        if metric_name in self.performance_data['metrics']:
            self.performance_data['metrics'][metric_name] += 1
            logging.debug(f"Métrica incrementada: {metric_name} = {self.performance_data['metrics'][metric_name]}")

    def save_performance_log(self):
        """Salva os dados de performance em arquivo JSON"""
        self.end_phase()  # Garante que a última fase seja fechada
        
        # Calcula o tempo total
        self.performance_data['end_time'] = datetime.now().isoformat()
        start = datetime.fromisoformat(self.performance_data['start_time'])
        end = datetime.fromisoformat(self.performance_data['end_time'])
        self.performance_data['total_duration'] = (end - start).total_seconds()
        
        # Estrutura do arquivo de log
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'execution_data': self.performance_data
        }
        
        try:
            # Lê o arquivo existente ou cria um novo
            if os.path.exists(self.performance_log_file):
                with open(self.performance_log_file, 'r') as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []
            
            # Adiciona a nova entrada
            data.append(log_entry)
            
            # Salva de volta no arquivo
            with open(self.performance_log_file, 'w') as f:
                json.dump(data, f, indent=2)
                
            logging.info("Dados de performance salvos com sucesso")
        except Exception as e:
            logging.error(f"Erro ao salvar log de performance: {str(e)}")

    def print_performance_report(self):
        """Exibe um relatório detalhado de performance"""
        print("\n" + "="*60)
        print(f"RELATÓRIO DE PERFORMANCE - Execução {self.performance_data['execution_id']}")
        print("="*60)
        
        print(f"\n🔹 Tempo Total: {self.performance_data['total_duration']:.2f} segundos")
        
        print("\n⏱️ Tempo por Fase:")
        for phase, data in sorted(self.performance_data['phases'].items(), 
                                key=lambda x: x[1]['duration'], reverse=True):
            percent = (data['duration']/self.performance_data['total_duration'])*100
            print(f"- {phase.upper():<20} {data['duration']:.2f}s ({percent:.1f}%)")
        
        print("\n📊 Métricas:")
        for metric, value in self.performance_data['metrics'].items():
            print(f"- {metric.replace('_', ' ').title():<20}: {value}")
        
        print("\n" + "="*60)

    def start_driver(self):
        """Inicia o navegador Chrome com configurações otimizadas"""
        self.start_phase("driver_initialization")
        try:
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(20)
            self.driver.implicitly_wait(3)
            
            # Ativa o monitoramento de rede
            self.driver.execute_cdp_cmd("Network.enable", {})
            
            logging.info("Navegador iniciado com sucesso")
            self.increment_metric('page_loads')
            return True
        except Exception as e:
            logging.error(f"Falha ao iniciar o navegador: {str(e)}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verifica o estado de login de forma eficiente"""
        try:
            # Verificação rápida usando JavaScript
            return self.driver.execute_script("""
                return !!document.querySelector('[data-testid="user-menu"], .user-avatar, button.logout') || 
                       !document.querySelector('input#form-input--alias');
            """)
        except Exception as e:
            logging.debug(f"Erro na verificação de login: {str(e)}")
            return False

    def renew_session(self):
        """Realiza uma renovação completa de sessão"""
        current_time = time.time()
        if current_time - self.last_session_renewal < self.session_timeout:
            logging.info("Renovação de sessão recente, aguardando...")
            return False
            
        self.start_phase("session_renewal")
        self.session_retry_count += 1
        self.last_session_renewal = current_time
        self.increment_metric('session_renewals')
        
        try:
            logging.info("Iniciando renovação de sessão...")
            
            # 1. Limpeza completa de dados de sessão
            self.driver.execute_cdp_cmd("Network.clearBrowserCookies", {})
            self.driver.execute_cdp_cmd("Storage.clearDataForOrigin", {
                "origin": "https://www.latamairlines.com",
                "storageTypes": "cookies,local_storage,indexeddb,websql,service_workers,cache_storage"
            })
            
            # 2. Recarrega a página inicial
            self.driver.get("https://www.latamairlines.com/br/pt")
            time.sleep(2)  # Espera para carregamento
            
            # 3. Verifica e realiza login se necessário
            if not self.check_login_state():
                logging.info("Realizando novo login após renovação de sessão")
                if not self.do_login():
                    return False
            
            logging.info("Sessão renovada com sucesso")
            return True
        except Exception as e:
            logging.error(f"Falha na renovação de sessão: {str(e)}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def intercept_response(self, timeout=30):
        """Monitora as respostas de rede para capturar a resposta desejada"""
        self.start_phase("response_monitoring")
        start_time = time.time()
        
        while not self.response_received and (time.time() - start_time < timeout):
            try:
                logs = self.driver.get_log("performance")
                self.increment_metric('request_count')
                
                for entry in logs:
                    try:
                        message = json.loads(entry["message"])["message"]
                        
                        # Filtra apenas respostas de rede
                        if message["method"] != "Network.responseReceived":
                            continue
                            
                        url = message.get("params", {}).get("response", {}).get("url", "")
                        if not url.startswith(self.target_endpoint):
                            continue
                            
                        status = message.get("params", {}).get("response", {}).get("status", 0)
                        
                        # Tratamento especial para erro 403
                        if status == 403:
                            body = self.get_response_body(message["params"]["requestId"])
                            if body and '"error":403' in body:
                                logging.warning("Erro 403 (Forbidden) detectado - Tentando renovar sessão")
                                if self.session_retry_count < self.max_session_retries:
                                    if self.renew_session():
                                        # Recarrega a página após renovação
                                        self.driver.get("https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-08-02T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED")
                                        return False
                                else:
                                    logging.error("Máximo de tentativas de renovação atingido")
                                    return False
                            continue
                            
                        # Processa apenas respostas 200 OK
                        if status != 200:
                            continue
                            
                        body = self.get_response_body(message["params"]["requestId"])
                        if not body:
                            continue
                            
                        try:
                            response = json.loads(body)
                            print(json.dumps(response, indent=2))
                            self.response_received = True
                            return True
                        except json.JSONDecodeError:
                            print(body)
                            self.response_received = True
                            return True
                            
                    except Exception as e:
                        logging.debug(f"Erro ao processar entrada de log: {str(e)}")
                        continue
                        
                time.sleep(0.2)  # Intervalo otimizado
                
            except Exception as e:
                logging.error(f"Erro ao monitorar respostas: {str(e)}")
                self.increment_metric('error_count')
                time.sleep(1)
                
        return False

    def get_response_body(self, request_id):
        """Obtém o corpo da resposta de forma segura"""
        try:
            result = self.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
            return result.get("body", "")
        except Exception as e:
            logging.debug(f"Erro ao obter corpo da resposta: {str(e)}")
            return None

    def execute_flow(self):
        """Executa o fluxo principal de automação"""
        self.start_phase("main_execution_flow")
        try:
            target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-08-02T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
            
            # Tenta até o máximo de tentativas permitidas
            for attempt in range(1, self.max_session_retries + 2):
                logging.info(f"🚀 Tentativa {attempt} de {self.max_session_retries + 1}")
                
                # Carrega a página alvo
                self.driver.get(target_url)
                self.increment_metric('page_loads')
                
                # Verifica o estado de login
                if not self.check_login_state():
                    logging.info("🔑 Realizando login...")
                    self.increment_metric('login_attempts')
                    if not self.do_login():
                        continue
                
                # Monitora as respostas da API
                if self.intercept_response(timeout=20):
                    return True
                
                if self.session_retry_count >= self.max_session_retries:
                    break
                    
                time.sleep(1.5)  # Espera otimizada entre tentativas
            
            logging.error("❌ Fluxo principal não concluído após todas as tentativas")
            return False

        except Exception as e:
            logging.error(f"⛔ Erro no fluxo principal: {str(e)}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def do_login(self):
        """Executa o processo de login"""
        self.start_phase("login_process")
        try:
            logging.info("Iniciando procedimento de login...")
            
            # Preenche e-mail
            if not self.fill_field("form-input--alias", "dionlan.alves@gmail.com", timeout=5):
                return False
                
            # Clica no botão de continuar
            if not self.click_element("primary-button", timeout=3):
                return False
                
            # Espera pelo campo de senha
            if not self.wait_for_element("form-input--password", timeout=10):
                return False
                
            # Preenche senha
            if not self.fill_field("form-input--password", "Dionlan!@#123", timeout=5):
                return False
                
            # Submete o formulário
            if not self.click_element("primary-button", timeout=3):
                return False
                
            logging.info("✅ Login realizado com sucesso")
            self.login_verified = True
            return True
            
        except Exception as e:
            logging.error(f"❌ Falha no login: {str(e)}")
            self.increment_metric('error_count')
            return False
        finally:
            self.end_phase()

    def fill_field(self, locator, value, locator_type=By.ID, timeout=10):
        """Preenche um campo de formulário"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator)))
            element.clear()
            element.send_keys(value)
            return True
        except Exception as e:
            logging.debug(f"Campo não preenchido: {locator} - {str(e)}")
            return False

    def click_element(self, locator, locator_type=By.ID, timeout=10):
        """Clica em um elemento"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable((locator_type, locator)))
            element.click()
            return True
        except Exception as e:
            logging.debug(f"Elemento não clicável: {locator} - {str(e)}")
            return False

    def wait_for_element(self, locator, locator_type=By.ID, timeout=10):
        """Aguarda por um elemento"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator)))
            return True
        except Exception as e:
            logging.debug(f"Elemento não encontrado: {locator} - {str(e)}")
            return False
        
    def run(self):
        """Método principal para execução do script"""
        try:
            self.init_performance_log()
            
            if not self.start_driver():
                return False
                
            result = self.execute_flow()
            
            return result
        except KeyboardInterrupt:
            logging.info("⏹️ Execução interrompida pelo usuário")
            return False
        except Exception as e:
            logging.error(f"⚠️ Erro não tratado: {str(e)}")
            return False
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logging.info("🛑 Navegador fechado")
                except Exception as e:
                    logging.error(f"Erro ao fechar navegador: {str(e)}")
            
            self.save_performance_log()
            self.print_performance_report()

if __name__ == "__main__":
    automation = LatamAutomation()
    success = automation.run()
    exit(0 if success else 1)
