import os
import json
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class LatamAPIMonitor:
    def __init__(self):
        self.chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        self.target_url = (
            "https://www.latamairlines.com/br/pt/oferta-voos"
            "?origin=BSB&outbound=2025-10-01T15%3A00%3A00.000Z"
            "&destination=CGH&adt=1&chd=0&inf=0&trip=OW"
            "&cabin=Economy&redemption=true&sort=RECOMMENDED"
        )
        self.target_endpoint = (
            "https://www.latamairlines.com/bff/air-offers/v2/offers/search/redemption"
        )
        self.driver = None
        self.profile_path = os.path.join(
            os.environ["USERPROFILE"],
            "AppData", "Local", "Google", "Chrome", "User Data", "Default"
        )

    def setup_driver(self):
        """Configura o ChromeDriver com perfil Default"""
        options = Options()
        
        # Configurações essenciais
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument("--profile-directory=Default")
        options.add_argument("--start-maximized")
        
        # Otimizações de performance
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Configurações para evitar detecção
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)
        
        if os.path.exists(self.chrome_path):
            options.binary_location = self.chrome_path

        # Habilita logs de rede
        options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

        logger.info("Iniciando navegador Chrome...")
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)
        self.driver.set_page_load_timeout(30)

    def wait_for_page_load(self):
        """Garante que a página foi carregada completamente"""
        try:
            logger.info(f"Carregando URL: {self.target_url}")
            self.driver.get(self.target_url)
            
            # Verificação adicional de carregamento
            start_time = time.time()
            while time.time() - start_time < 30:
                if self.driver.execute_script("return document.readyState") == "complete":
                    logger.info("Página carregada com sucesso")
                    return True
                time.sleep(0.5)
            
            logger.error("Timeout - Página não carregou completamente")
            return False
            
        except Exception as e:
            logger.error(f"Erro ao carregar página: {str(e)}")
            return False

    def get_api_response(self):
        """Obtém a resposta da API específica"""
        try:
            # Habilita monitoramento de rede
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            logger.info("Monitorando chamadas de rede...")
            start_time = time.time()
            
            while time.time() - start_time < 30:  # Timeout de 30 segundos
                logs = self.driver.get_log('performance')
                
                for entry in reversed(logs):  # Processa logs mais recentes primeiro
                    try:
                        message = json.loads(entry['message'])['message']
                        if message['method'] != 'Network.responseReceived':
                            continue
                            
                        url = message['params']['response']['url']
                        if not url.startswith(self.target_endpoint):
                            continue
                            
                        request_id = message['params']['requestId']
                        response = self.driver.execute_cdp_cmd(
                            'Network.getResponseBody',
                            {'requestId': request_id}
                        )
                        
                        api_response = json.loads(response['body'])
                        logger.info("✅ Resposta da API interceptada com sucesso!")
                        return api_response
                        
                    except Exception as e:
                        continue
                
                time.sleep(0.3)  # Intervalo curto entre verificações
            
            logger.error("Timeout - Não foi possível interceptar a resposta da API")
            return None
            
        except Exception as e:
            logger.error(f"Erro durante interceptação: {str(e)}")
            return None

    def run(self):
        """Execução principal"""
        try:
            self.setup_driver()
            
            if not self.wait_for_page_load():
                return False
                
            if api_response := self.get_api_response():
                print("\n" + "="*80)
                print("RESPOSTA DA API LATAM".center(80))
                print("="*80)
                print(json.dumps(api_response, indent=2, ensure_ascii=False))
                print("="*80 + "\n")
                return True
                
            return False
            
        except Exception as e:
            logger.error(f"Erro crítico: {str(e)}")
            return False
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Navegador encerrado com sucesso")
                except Exception as e:
                    logger.warning(f"Erro ao fechar navegador: {str(e)}")

if __name__ == "__main__":
    monitor = LatamAPIMonitor()
    success = monitor.run()
    exit(0 if success else 1)