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
        self.automation_profile_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData",
            "Local",
            "Google",
            "Chrome",
            "User Data",
            "Default"
        )
        self.target_endpoint = (
            "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        )
        self.driver = None
        self.response_received = False
        self.login_verified = False
        self.session_retry_count = 0
        self.max_session_retries = 3
        self.last_session_renewal = 0
        self.session_timeout = 300  # 5 minutos entre renovações
        self.max_retry_intercept = 2

        # Configuração de logging de performance
        self.performance_log_file = "latam_performance_log.json"
        self.current_phase = None
        self.performance_data = {
            "execution_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "start_time": None,
            "end_time": None,
            "phases": {},
            "metrics": {
                "request_count": 0,
                "error_count": 0,
                "session_renewals": 0,
                "page_loads": 0,
                "login_attempts": 0,
            },
        }

        self.setup_logging()
        self.chrome_options = self.configure_chrome()

    def setup_logging(self):
        """Configura o sistema de logging"""
        logging.basicConfig(
            level=logging.INFO,
            format="[%(levelname)s] %(asctime)s - %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler("automation.log", mode="a", encoding="utf-8"),
            ],
        )
        logging.info("Sistema de logging configurado")

    def configure_chrome(self):
        """Configura as opções do Chrome"""
        options = Options()
        options.binary_location = self.chrome_path

        # Usa o caminho definido no __init__
        os.makedirs(self.automation_profile_path, exist_ok=True)
        
        # CONFIGURAÇÕES PRINCIPAIS PARA PERFORMANCE E PERSISTÊNCIA
        options.add_argument(f"--user-data-dir={self.automation_profile_path}")
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
        options.set_capability(
            "goog:chromeOptions",
            {
                "perfLoggingPrefs": {
                    "enableNetwork": True,
                    "enablePage": False,
                    "enableTimeline": False,
                },
                "args": ["--enable-logging", "--v=1"],
            },
        )

        return options

    def init_performance_log(self):
        """Inicializa o registro de performance"""
        self.performance_data["start_time"] = datetime.now().isoformat()
        self.start_phase("initialization")

    def start_phase(self, phase_name):
        """Registra o início de uma fase"""
        if self.current_phase:
            self.end_phase()

        self.current_phase = phase_name
        self.performance_data["phases"][phase_name] = {
            "start": datetime.now().isoformat(),
            "end": None,
            "duration": None,
        }
        logging.debug(f"Iniciando fase: {phase_name}")

    def end_phase(self):
        """Finaliza a fase atual"""
        if self.current_phase:
            phase_data = self.performance_data["phases"][self.current_phase]
            phase_data["end"] = datetime.now().isoformat()
            start = datetime.fromisoformat(phase_data["start"])
            end = datetime.fromisoformat(phase_data["end"])
            phase_data["duration"] = (end - start).total_seconds()
            logging.debug(
                f"Fase {self.current_phase} concluída em {phase_data['duration']:.2f}s"
            )
            self.current_phase = None

    def increment_metric(self, metric_name):
        """Incrementa um contador de métrica"""
        if metric_name in self.performance_data["metrics"]:
            self.performance_data["metrics"][metric_name] += 1
            logging.debug(
                f"Métrica incrementada: {metric_name} = {self.performance_data['metrics'][metric_name]}"
            )

    def save_performance_log(self):
        """Salva os dados de performance em arquivo JSON"""
        self.end_phase()

        self.performance_data["end_time"] = datetime.now().isoformat()
        start = datetime.fromisoformat(self.performance_data["start_time"])
        end = datetime.fromisoformat(self.performance_data["end_time"])
        self.performance_data["total_duration"] = (end - start).total_seconds()

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "execution_data": self.performance_data,
        }

        try:
            if os.path.exists(self.performance_log_file):
                with open(self.performance_log_file, "r") as f:
                    try:
                        data = json.load(f)
                        if not isinstance(data, list):
                            data = []
                    except json.JSONDecodeError:
                        data = []
            else:
                data = []

            data.append(log_entry)

            with open(self.performance_log_file, "w") as f:
                json.dump(data, f, indent=2)

            logging.info("Dados de performance salvos com sucesso")
        except Exception as e:
            logging.error(f"Erro ao salvar log de performance: {str(e)}")

    def print_performance_report(self):
        """Exibe um relatório de performance"""
        print("\n" + "=" * 60)
        print(
            f"RELATÓRIO DE PERFORMANCE - Execução {self.performance_data['execution_id']}"
        )
        print("=" * 60)

        print(
            f"\n🔹 Tempo Total: {self.performance_data['total_duration']:.2f} segundos"
        )

        print("\n⏱️ Tempo por Fase:")
        for phase, data in sorted(
            self.performance_data["phases"].items(),
            key=lambda x: x[1]["duration"],
            reverse=True,
        ):
            percent = (data["duration"] / self.performance_data["total_duration"]) * 100
            print(f"- {phase.upper():<20} {data['duration']:.2f}s ({percent:.1f}%)")

        print("\n📊 Métricas:")
        for metric, value in self.performance_data["metrics"].items():
            print(f"- {metric.replace('_', ' ').title():<20}: {value}")

        print("\n" + "=" * 60)

    def start_driver(self):
        """Inicia o navegador Chrome"""
        self.start_phase("driver_initialization")
        try:
            start_time = time.time()
            self.driver = webdriver.Chrome(options=self.chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            self.driver.execute_cdp_cmd("Network.enable", {})

            logging.info(f"🚀 Navegador iniciado em {time.time()-start_time:.2f}s")
            self.increment_metric("page_loads")
            return True
        except Exception as e:
            logging.error(f"❌ Falha ao iniciar navegador: {str(e)}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def check_login_state(self):
        """Verifica se o usuário está logado com base no elemento do avatar/nome"""
        try:
            is_logged_in = self.driver.execute_script(
                "return !!document.querySelector('[data-testid=\"nick-name-component\"]');"
            )
            status = "✅ Logado" if is_logged_in else "🔒 Não logado"
            logging.info(f"🔍 Estado de login: {status}")
            return is_logged_in
        except Exception as e:
            logging.error(f"❌ Erro na verificação de login: {str(e)}")
            return False


    def renew_session(self):
        """Renova a sessão com tratamento completo"""
        current_time = time.time()
        if current_time - self.last_session_renewal < self.session_timeout:
            wait_time = int(
                self.session_timeout - (current_time - self.last_session_renewal)
            )
            logging.warning(f"⏳ Renovação recente - Aguarde {wait_time}s")
            return False

        self.start_phase("session_renewal")
        self.session_retry_count += 1
        self.last_session_renewal = current_time
        self.increment_metric("session_renewals")

        try:
            logging.info("🔄 Iniciando renovação de sessão...")

            # 1. Limpeza de sessão
            if not self.clear_session_data():
                return False

            # 2. Nova navegação
            self.driver.get("https://www.latamairlines.com/br/pt")

            # 3. Aceitar cookies
            self.accept_cookies()

            # 4. Verificar se já está logado após renovação
            # if self.check_login_state():
            #    logging.info("✅ Sessão renovada com sucesso")
            #    return True

            # 5. Fluxo de login completo
            if not self.click_login_button():
                return False

            if not self.do_login():
                return False

            logging.info("✅ Sessão renovada e login realizado")
            return True

        except Exception as e:
            logging.error(f"❌ Falha na renovação: {str(e)}")
            return False
        finally:
            self.end_phase()

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

    def accept_cookies(self):
        """Aceita os cookies se o banner estiver presente"""
        try:
            cookie_button = WebDriverWait(self.driver, 5).until(
                EC.element_to_be_clickable((By.ID, "cookies-politics-button"))
            )
            cookie_button.click()
            logging.info("Cookies aceitos")
            return True
        except:
            logging.debug("Banner de cookies não encontrado")
            return False

    def click_login_button(self):
        """Clica no botão de login"""
        try:
            login_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.ID, "login-incentive-login"))
            )
            login_button.click()
            logging.info("Botão de login clicado")
            return True
        except Exception as e:
            logging.error(f"Falha ao clicar no botão de login: {str(e)}")
            return False

    def execute_flow(self):
        """Fluxo principal otimizado"""
        self.start_phase("main_execution_flow")
        try:
            target_url = "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-11-01T15:00:00.000Z&destination=CGH&inbound=undefined&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"

            # 1. Carregar página inicial
            logging.info("🌐 Carregando página de consulta...")
            self.driver.get(target_url)
            self.increment_metric("page_loads")

            # 2. Verificar estado de login
            is_logged_in = self.check_login_state()
            self.login_verified = is_logged_in

            # 3. Se não logado, renovar sessão e tentar novamente
            if not is_logged_in:
                logging.info("🔑 Usuário não autenticado - renovando sessão...")
                if not self.renew_session():
                    logging.error("❌ Falha ao renovar sessão")
                    return False

                # Recarrega a página após renovação
                logging.info("🔄 Recarregando página após renovação...")
                self.driver.get(target_url)
                self.increment_metric("page_loads")

                # Verifica novamente o estado de login
                is_logged_in = self.check_login_state()
                if not is_logged_in:
                    logging.error("❌ Falha na autenticação após renovação")
                    return False

            # 4. Monitorar respostas da API
            logging.info("📡 Monitorando respostas da API...")
            if self.intercept_response(timeout=15):
                return True

            logging.error("❌ Falha ao obter resposta válida")
            return False

        except Exception as e:
            logging.error(f"💥 Erro no fluxo principal: {str(e)}")
            return False
        finally:
            self.end_phase()

    def intercept_response(self, timeout=15):
        """Monitora respostas da API com tratamento de erros"""
        self.start_phase("response_monitoring")
        start_time = time.time()
        retry_count = 0

        logging.info(f"🔍 Iniciando monitoramento por {timeout}s...")

        while not self.response_received and (time.time() - start_time < timeout):
            try:
                logs = self.driver.get_log("performance")
                self.increment_metric("request_count")

                for entry in logs:
                    try:
                        message = json.loads(entry["message"])["message"]
                        if message["method"] != "Network.responseReceived":
                            continue

                        url = (
                            message.get("params", {}).get("response", {}).get("url", "")
                        )
                        if not url.startswith(self.target_endpoint):
                            continue

                        status = (
                            message.get("params", {})
                            .get("response", {})
                            .get("status", 0)
                        )
                        request_id = message["params"]["requestId"]

                        # Tratamento para erro 403
                        if status == 403:
                            logging.warning(
                                f"⚠️ Erro 403 detectado (tentativa {retry_count+1}/{self.max_retry_intercept})"
                            )

                            if retry_count >= self.max_retry_intercept:
                                logging.error("🚫 Máximo de tentativas atingido")
                                return False

                            if self.renew_session():
                                retry_count += 1
                                # Recarrega a página após renovação
                                self.driver.get(
                                    "https://www.latamairlines.com/br/pt/oferta-voos?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z&destination=CGH&adt=1&chd=0&inf=0&trip=OW&cabin=Economy&redemption=true&sort=RECOMMENDED"
                                )
                                break

                        # Processa resposta 200
                        if status == 200:
                            body = self.get_response_body(request_id)
                            if body:
                                try:
                                    response = json.loads(body) # Valida JSON
                                    print(json.dumps(response, indent=2))
                                    logging.info("✅ Resposta válida recebida")
                                    self.response_received = True
                                    return True
                                except json.JSONDecodeError:
                                    logging.warning("⚠️ Resposta não é JSON válido")
                                    self.response_received = True
                                    return True

                    except Exception:
                        continue

                time.sleep(0.5)

            except Exception as e:
                logging.error(f"⛔ Erro no monitoramento: {str(e)}")
                time.sleep(1)

        logging.error(f"⌛ Timeout após {timeout}s")
        return False

    def get_response_body(self, request_id):
        """Obtém o corpo da resposta"""
        try:
            result = self.driver.execute_cdp_cmd(
                "Network.getResponseBody", {"requestId": request_id}
            )
            return result.get("body", "")
        except Exception as e:
            logging.debug(f"Erro ao obter corpo da resposta: {str(e)}")
            return None

    def do_login(self):
        """Executa o login com verificação robusta"""
        self.start_phase("login_process")
        try:
            logging.info("Iniciando login...")

            # Preenche e-mail
            if not self.fill_field("form-input--alias", "dionlan.alves@gmail.com"):
                return False

            if not self.click_element("primary-button", timeout=10):
                return False

            if not self.wait_for_element("form-input--password"):
                return False

            if not self.fill_field("form-input--password", "Dionlan!@#123"):
                return False

            if not self.click_element("primary-button"):
                return False
            
            # Espera explícita pelo menu de perfil e nome do usuário
            try:
                WebDriverWait(self.driver, 20).until(
                    lambda d: d.execute_script(
                        'return !!document.querySelector(\'[data-testid="header__profile-dropdown-dropdown-menu"]\') && ' +
                        '!!document.querySelector(\'[data-testid="nick-name-component"]\');'
                    )
                )
                user_name = self.driver.execute_script(
                    'return document.querySelector(\'[data-testid="nick-name-component"]\').textContent.trim();'
                )
                logging.info(f"✅ Login confirmado - Usuário: {user_name}")
                return True
            except TimeoutException:
                logging.error("❌ Timeout ao aguardar confirmação de login")
                return False

        except Exception as e:
            logging.error(f"Falha no login: {str(e)}")
            self.increment_metric("error_count")
            return False
        finally:
            self.end_phase()

    def fill_field(self, locator, value, locator_type=By.ID, timeout=10):
        """Preenche um campo"""
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator))
            )
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
                EC.element_to_be_clickable((locator_type, locator))
            )
            element.click()
            return True
        except Exception as e:
            logging.debug(f"Elemento não clicável: {locator} - {str(e)}")
            return False

    def wait_for_element(self, locator, locator_type=By.ID, timeout=10):
        """Aguarda por um elemento"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((locator_type, locator))
            )
            return True
        except Exception as e:
            logging.debug(f"Elemento não encontrado: {locator} - {str(e)}")
            return False

    def run(self):
        """Executa o script principal"""
        try:
            self.init_performance_log()

            if not self.start_driver():
                return False

            result = self.execute_flow()

            return result
        except KeyboardInterrupt:
            logging.info("Execução interrompida pelo usuário")
            return False
        except Exception as e:
            logging.error(f"Erro não tratado: {str(e)}")
            return False
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logging.info("Navegador fechado")
                except Exception as e:
                    logging.error(f"Erro ao fechar navegador: {str(e)}")

            self.save_performance_log()
            self.print_performance_report()


if __name__ == "__main__":
    automation = LatamAutomation()
    success = automation.run()
    exit(0 if success else 1)
