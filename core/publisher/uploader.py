import requests
import time
import os

def _upload_catbox(caminho_arquivo):
    """Tenta fazer upload no catbox.moe (permanente, até 200MB)."""
    with open(caminho_arquivo, 'rb') as f:
        payload = {'reqtype': 'fileupload'}
        files = {'fileToUpload': f}
        response = requests.post(
            "https://catbox.moe/user/api.php",
            data=payload, files=files, timeout=120
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
            data=payload, files=files, timeout=180
        )
    if response.status_code == 200:
        url = response.text.strip()
        if url.startswith("http"):
            return url
    raise Exception(f"litterbox falhou (HTTP {response.status_code}): {response.text.strip()[:200]}")

def upload_temporario(caminho_arquivo):
    """
    Envia o arquivo para um servidor temporário e retorna a URL pública.
    
    Ordem de tentativas:
    1. catbox.moe — permanente, até 200MB
    2. litterbox.catbox.moe — 72h de validade, até 1GB (ideal para vídeos longos)
    """
    tamanho_mb = os.path.getsize(caminho_arquivo) / (1024 * 1024)
    print(f"📤 Enviando {caminho_arquivo} ({tamanho_mb:.1f}MB) para catbox.moe...")

    # --- Tentativa 1: catbox.moe ---
    try:
        url = _upload_catbox(caminho_arquivo)
        print(f"🔗 Link direto gerado (catbox.moe): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e:
        print(f"⚠️ catbox.moe falhou: {e}")
        print("🔄 Tentando fallback: litterbox.catbox.moe (aceita até 1GB, válido por 72h)...")

    # --- Tentativa 2: litterbox.catbox.moe (fallback) ---
    try:
        url = _upload_litterbox(caminho_arquivo)
        print(f"🔗 Link direto gerado (litterbox): {url}")
        print("⏳ Aguardando 10s para o arquivo ficar disponível globalmente...")
        time.sleep(10)
        return url
    except Exception as e2:
        print(f"❌ litterbox também falhou: {e2}")
        raise Exception(
            f"Falha em todos os serviços de upload.\n"
            f"catbox.moe: ver log acima\n"
            f"litterbox: {e2}"
        )
