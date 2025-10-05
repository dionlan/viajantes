import requests

# Cabeçalho para simular um navegador real
headers = {"User-Agent": "Mozilla/5.0"}

# URL base
base_url = "https://cdn.cebraspe.org.br/concursos/PF_25/arquivos/"

# Gera números de 094 até 200
numeros = [str(i).zfill(3) for i in range(000, 999)]

# Lista para armazenar os arquivos encontrados
found = []

print(f"🔍 Verificando {len(numeros)} arquivos possíveis...\n")

# Loop principal
for numero in numeros:
    # nome_arquivo = f"{numero}_PF_001_01.pdf"
    nome_arquivo = f"{numero}_PF_CB1_01.pdf"
    url = base_url + nome_arquivo
    print(url)
    try:
        response = requests.head(url, headers=headers, timeout=5)
        if response.status_code == 200:
            print(f"✔️ Encontrado: {url}")
            found.append(url)
    except requests.RequestException as e:
        print(f"⚠️ Erro ao verificar {url}: {e}")

# Resultado final
print("\n📄 Arquivos encontrados:")
for f in found:
    print(f)
