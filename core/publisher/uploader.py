import requests
import time
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def _upload_catbox(caminho_arquivo):
    """Tenta fazer upload no catbox.moe (permanente, até 200MB)."""
    with open(caminho_arquivo, 'rb') as f:
        payload = {'reqtype': 'fileupload'}
        files = {'fileToUpload': f}
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data=payload, files=files, headers=HEADERS, timeout=120
        )
    if response.status_code == 200:
        url = response.text.strip()
        if url.startswith("http"):
            return url
    raise Exception(f"catbox.moe falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def _upload_litterbox(caminho_arquivo):
    """
    Fallback: litterbox.catbox.moe (mesmo provedor, até 1GB, válido por 72h).
    Mais que suficiente para o fluxo de publicação do Instagram.
    """
    with open(caminho_arquivo, 'rb') as f:
        payload = {'reqtype': 'fileupload', 'time': '72h'}
        files = {'fileToUpload': f}
        response = requests.post(
            "https://litterbox.catbox.moe/resources/internals/api.php",
            data=payload, files=files, headers=HEADERS, timeout=180
        )
    if response.status_code == 200:
        url = response.text.strip()
        if url.startswith("http"):
            return url
    raise Exception(f"litterbox falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def _upload_file_io(caminho_arquivo):
    """
    Fallback 3: file.io (válido por 1 download ou até 14 dias, máximo 2GB).
    Retorna um link direto ideal para o Instagram.
    """
    with open(caminho_arquivo, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            "https://file.io",
            files=files, headers=HEADERS, timeout=120
        )
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("success"):
            return res_json.get("link")
    raise Exception(f"file.io falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def _upload_tmpfiles(caminho_arquivo):
    """
    Fallback 4: tmpfiles.org (arquivo temporário, link direto de download).
    Faz o upload, lê a página de visualização e extrai o link direto com o token dinâmico.
    """
    with open(caminho_arquivo, 'rb') as f:
        files = {'file': f}
        response = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files=files, headers=HEADERS, timeout=120
        )
    if response.status_code == 200:
        res_json = response.json()
        if res_json.get("status") == "success":
            url_original = res_json.get("data", {}).get("url")
            if url_original:
                try:
                    import re
                    # Faz uma requisição GET na página de visualização para extrair o link de download direto com token
                    page_res = requests.get(url_original, headers=HEADERS, timeout=20)
                    if page_res.status_code == 200:
                        # Busca href="https://tmpfiles.org/dl/...
                        match = re.search(r'href="(https://tmpfiles.org/dl/[^"]+)"', page_res.text)
                        if match:
                            url_direta = match.group(1)
                            return url_direta
                except Exception as ex:
                    print(f"⚠️ Erro ao tentar extrair link direto do tmpfiles: {ex}")
                
                # Fallback antigo caso o regex falhe
                if "tmpfiles.org/" in url_original:
                    return url_original.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    raise Exception(f"tmpfiles.org falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def _upload_transfer_sh(caminho_arquivo):
    """
    Fallback 5: transfer.sh (válido por 14 dias).
    Envia via PUT e retorna o link direto.
    """
    nome_arquivo = os.path.basename(caminho_arquivo)
    with open(caminho_arquivo, 'rb') as f:
        response = requests.put(
            f"https://transfer.sh/{nome_arquivo}",
            data=f, headers=HEADERS, timeout=180
        )
    if response.status_code == 200:
        url = response.text.strip()
        if url.startswith("http"):
            return url
    raise Exception(f"transfer.sh falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def obter_urls_temporarias(caminho_arquivo):
    """
    Gerador que realiza upload em múltiplos serviços em ordem de confiabilidade 
    (priorizando os mais amigáveis ao GitHub Actions e Instagram),
    produzindo uma URL por vez à medida que são solicitadas.
    """
    tamanho_mb = os.path.getsize(caminho_arquivo) / (1024 * 1024)
    
    # Lista de tuplas (Nome, Função de Upload) em ordem de prioridade
    servicos = [
        ("tmpfiles.org", _upload_tmpfiles),
        ("transfer.sh", _upload_transfer_sh),
        ("file.io", _upload_file_io),
        ("litterbox.catbox.moe", _upload_litterbox),
        ("catbox.moe", _upload_catbox)
    ]
    
    sucessos = 0
    for nome, func in servicos:
        print(f"📤 Enviando {caminho_arquivo} ({tamanho_mb:.1f}MB) para {nome}...")
        try:
            url = func(caminho_arquivo)
            print(f"🔗 Link direto gerado ({nome}): {url}")
            print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
            time.sleep(10)
            sucessos += 1
            yield url
        except Exception as e:
            print(f"⚠️ {nome} falhou: {e}")
            
    if sucessos == 0:
        raise Exception("Falha crítica: Todos os serviços de upload temporário falharam.")

def upload_temporario(caminho_arquivo):
    """
    Mantém compatibilidade com o resto do código.
    Retorna a primeira URL que funcionar de obter_urls_temporarias.
    """
    for url in obter_urls_temporarias(caminho_arquivo):
        return url
    raise Exception("Falha crítica: Nenhum serviço de upload retornou uma URL válida.")

