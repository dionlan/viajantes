import requests
import json
import time
import hashlib
import random
from urllib.parse import urlencode

class SmilesUltimateBypass:
    def __init__(self, use_proxy=False):
        self.session = requests.Session()
        self.api_key = self._get_fresh_api_key()
        self.base_url = "https://api-air-flightsearch-green.smiles.com.br/v1/airlines/search"
        self.use_proxy = use_proxy
        self._init_session()

    def _get_fresh_api_key(self):
        """Obtém a API key mais recente (atualize manualmente)"""
        return "aJqPU7xNHl9qN3NVZnPaJ208aPo2Bh2p2ZV844tw"

    def _init_session(self):
        """Configuração de sessão com proteções contra detecção"""
        self.headers = {
            'authority': 'api-air-flightsearch-green.smiles.com.br',
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'cache-control': 'no-cache',
            'origin': 'https://www.smiles.com.br',
            'referer': 'https://www.smiles.com.br/',
            'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': self._generate_user_agent(),
            'x-api-key': self.api_key,
            'x-request-id': self._generate_request_id(),
            'x-forwarded-for': self._generate_random_ip()
        }

        # Configura proxy se necessário
        self.proxies = {
            'http': 'http://usuario:senha@proxy.residencial.com:3128',
            'https': 'http://usuario:senha@proxy.residencial.com:3128'
        } if self.use_proxy else None

        # Cookies críticos (obter manualmente)
        self._refresh_cookies()

    def _refresh_cookies(self):
        """Atualiza cookies com valores válidos"""
        self.session.cookies.update({
            'bm_sv': self._generate_bm_sv(),
            'bm_sz': self._generate_bm_sz(),
            '_abck': self._generate_abck(),
            'ak_bmsc': self._generate_ak_bmsc()
        })

    def _generate_user_agent(self):
        """Gera user-agent realista"""
        chrome_versions = [
            ('138.0.0.0', '537.36'),
            ('137.0.0.0', '537.36'),
            ('136.0.0.0', '537.36')
        ]
        version, webkit = random.choice(chrome_versions)
        return f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/{webkit} (KHTML, like Gecko) Chrome/{version} Safari/{webkit}'

    def _generate_request_id(self):
        """Gera ID de requisição único"""
        return hashlib.md5(f"{time.time()}{random.randint(10000,99999)}".encode()).hexdigest()

    def _generate_random_ip(self):
        """Gera IP aleatório para headers"""
        return f"{random.randint(11,255)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}"

    def _generate_bm_sv(self):
        """Gera cookie bm_sv dinâmico"""
        part1 = hashlib.sha256(str(time.time()).encode()).hexdigest()[:32].upper()
        return f"{part1}~1"

    def _generate_bm_sz(self):
        """Gera cookie bm_sz dinâmico"""
        part1 = hashlib.sha256(str(time.time()).encode()).hexdigest()[:32].upper()
        return f"{part1}~4342326~4276529"

    def _generate_abck(self):
        """Gera cookie _abck dinâmico"""
        part1 = hashlib.md5(str(random.randint(1,100000)).encode()).hexdigest().upper()[:16]
        return f"{part1}~-1~YAAQ{random.randint(1000,9999)}~-1~-1~-1"

    def _generate_ak_bmsc(self):
        """Gera cookie ak_bmsc dinâmico"""
        part1 = hashlib.md5(str(time.time()).encode()).hexdigest().upper()[:32]
        return f"{part1}~000000000000000000000000000000~YAAQ..."

    def _simulate_browser_behavior(self):
        """Simula comportamento de navegador real"""
        try:
            # 1. Acesso inicial
            self.session.get(
                "https://www.smiles.com.br",
                headers={'User-Agent': self.headers['user-agent']},
                timeout=10,
                proxies=self.proxies
            )
            
            # 2. Requisições secundárias
            endpoints = ["/api/config", "/api/session"]
            for endpoint in endpoints:
                self.session.get(
                    f"https://www.smiles.com.br{endpoint}",
                    headers={'Referer': 'https://www.smiles.com.br/'},
                    timeout=5,
                    proxies=self.proxies
                )
                time.sleep(random.uniform(0.5, 1.5))
            
            return True
        except:
            return False

    def search_flights(self, origin, destination, date):
        """Busca de voos com técnicas anti-detecção"""
        if not self._simulate_browser_behavior():
            print("Falha na simulação do navegador")
            return None

        params = {
            "cabin": "ECONOMIC",
            "originAirportCode": origin,
            "destinationAirportCode": destination,
            "departureDate": date,
            "memberNumber": "",
            "adults": "1",
            "children": "0",
            "infants": "0",
            "forceCongener": "false",
            "cookies": "_gid=undefined;",
            "_": str(int(time.time() * 1000))
        }

        try:
            # Primeira tentativa
            response = self._make_api_request(params)
            
            if response.status_code == 200:
                return response.json()
            
            # Segunda tentativa com headers reforçados
            if response.status_code == 406:
                print("Ativando modo de segurança avançado...")
                self.headers.update({
                    'x-bm-srv': hashlib.md5(str(time.time()).encode()).hexdigest(),
                    'x-defender-id': hashlib.md5(str(time.time()).encode()).hexdigest()
                })
                self._refresh_cookies()
                response = self._make_api_request(params)
                
                if response.status_code == 200:
                    return response.json()
            
            print(f"Erro {response.status_code}: {response.text}")
            return None

        except Exception as e:
            print(f"Falha crítica: {str(e)}")
            return None

    def _make_api_request(self, params):
        """Executa requisição à API com tratamento de erros"""
        try:
            return self.session.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=15,
                proxies=self.proxies
            )
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição: {str(e)}")
            raise

if __name__ == "__main__":
    print("Iniciando busca premium...")
    
    # Configuração (True para usar proxy)
    api = SmilesUltimateBypass(use_proxy=False)
    
    # Execução
    result = api.search_flights("BSB", "CGH", "2025-08-01")
    
    if result:
        print("\nResultado obtido com sucesso!")
        print(json.dumps(result, indent=2, ensure_ascii=False))
        
        with open('voos_smiles.json', 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\nDados salvos em 'voos_smiles.json'")
    else:
        print("\nFalha na obtenção dos dados. Execute:")
        print("1. Obtenha cookies MANUALMENTE do site")
        print("2. Atualize o API_KEY no código")
        print("3. Use um proxy residencial de qualidade")
        print("4. Tente em horários alternativos")