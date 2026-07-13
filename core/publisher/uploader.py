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
    Retorna um link que modificamos para '/dl/' para servir o arquivo bruto.
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
            # Converte 'https://tmpfiles.org/123/arq' em 'https://tmpfiles.org/dl/123/arq'
            if url_original and "tmpfiles.org/" in url_original:
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

def upload_temporario(caminho_arquivo):
    """
    Envia o arquivo para um servidor temporário e retorna a URL pública.
    Tenta múltiplos serviços em sequência caso ocorra alguma falha.
    """
    tamanho_mb = os.path.getsize(caminho_arquivo) / (1024 * 1024)
    
    # 1. Catbox
    print(f"📤 Enviando {caminho_arquivo} ({tamanho_mb:.1f}MB) para catbox.moe...")
    try:
        url = _upload_catbox(caminho_arquivo)
        print(f"🔗 Link direto gerado (catbox.moe): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"⚠️ catbox.moe falhou: {e}")
    
    # 2. Litterbox
    print("🔄 Tentando fallback 1: litterbox.catbox.moe...")
    try:
        url = _upload_litterbox(caminho_arquivo)
        print(f"🔗 Link direto gerado (litterbox): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"⚠️ litterbox falhou: {e}")

    # 3. Tmpfiles.org
    print("🔄 Tentando fallback 2: tmpfiles.org...")
    try:
        url = _upload_tmpfiles(caminho_arquivo)
        print(f"🔗 Link direto gerado (tmpfiles.org): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"⚠️ tmpfiles.org falhou: {e}")

    # 4. File.io (Uso único - apenas 1 download permitido)
    print("🔄 Tentando fallback 3: file.io...")
    try:
        url = _upload_file_io(caminho_arquivo)
        print(f"🔗 Link direto gerado (file.io): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"⚠️ file.io falhou: {e}")

    # 5. Transfer.sh
    print("🔄 Tentando fallback 4: transfer.sh...")
    try:
        url = _upload_transfer_sh(caminho_arquivo)
        print(f"🔗 Link direto gerado (transfer.sh): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"❌ transfer.sh falhou: {e}")
        
    raise Exception(
        "Falha crítica: Todos os serviços de upload temporário falharam."
    )
