import os
import json
import urllib.parse
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

# Salva a credencial vinda diretamente das Secrets do SO (antes do load_dotenv corromper a string multilinha)
_direct_env_creds = os.environ.get("FIREBASE_CREDENTIALS")

# Proteção cirúrgica contra o bug do Firestore REST client no Linux:
# Impede a conversão de '(default)' para '%28default%29' nas requisições HTTP do Google Cloud API
_orig_quote = urllib.parse.quote
urllib.parse.quote = lambda string, safe='', encoding=None, errors=None: '(default)' if string == '(default)' else _orig_quote(string, safe=safe, encoding=encoding, errors=errors)

# Carrega as variáveis de ambiente
load_dotenv()

_db = None

def _parse_credentials_universal(raw_str):
    """
    Parser universal extremamente resiliente para FIREBASE_CREDENTIALS.
    Cobre: JSON direto, JSON com double-quote, Base64, multilinhas e chave RSA com Enters reais.
    """
    if not raw_str:
        return None
    raw_str = raw_str.strip()
    if (raw_str.startswith("'") and raw_str.endswith("'")) or \
       (raw_str.startswith('"') and raw_str.endswith('"')):
        raw_str = raw_str[1:-1].strip()

    # 1. Tenta JSON direct ou double-encoded JSON
    try:
        data = json.loads(raw_str)
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict) and "project_id" in data:
            return data
    except Exception:
        pass

    # 2. Tenta Base64 decode
    try:
        import base64
        decoded = base64.b64decode(raw_str).decode('utf-8')
        data = json.loads(decoded)
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, dict) and "project_id" in data:
            return data
    except Exception:
        pass

    # 3. Tenta sanitizar multilinhas com substituição de quebras reais em private_key
    try:
        import re
        def fix_key(match):
            key_content = match.group(1).replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '')
            return f'"private_key": "{key_content}"'
        
        fixed_str = re.sub(r'"private_key"\s*:\s*"(.*?)"', fix_key, raw_str, flags=re.DOTALL)
        data = json.loads(fixed_str)
        if isinstance(data, dict) and "project_id" in data:
            return data
    except Exception:
        pass

    # 4. Tenta substituição global simples de Enters
    try:
        cleaned_str = raw_str.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '')
        data = json.loads(cleaned_str)
        if isinstance(data, dict) and "project_id" in data:
            return data
    except Exception:
        pass

    return None


def get_db():
    global _db
    
    if _db is not None:
        return _db
        
    # 1. Tenta a credencial direta da memória do SO (GitHub Secrets)
    # 2. Tenta a credencial do .env
    firebase_creds_str = _direct_env_creds or os.getenv("FIREBASE_CREDENTIALS")
    
    cred_dict = _parse_credentials_universal(firebase_creds_str)

    # 3. Fallback: tenta buscar arquivos locais de credenciais se não conseguiu pelo ambiente
    if not cred_dict:
        for p in [
            "sistema-op-marketing-firebase-adminsdk-fbsvc-0fabd9a6bc.json",
            "codigo da sabedoria/firebase-credentials.json",
            "firebase-credentials.json"
        ]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        cred_dict = json.load(f)
                    if cred_dict:
                        break
                except Exception:
                    pass

    if not cred_dict:
        logger.warning("FIREBASE_CREDENTIALS não pôde ser decodificado do ambiente nem dos arquivos locais.")
        return None
        
    try:
        # Garante que as quebras de linha literais '\\n' na private_key sejam convertidas em '\n' real do PEM
        if isinstance(cred_dict, dict) and "private_key" in cred_dict and isinstance(cred_dict["private_key"], str):
            cred_dict["private_key"] = cred_dict["private_key"].replace("\\n", "\n")

        # Conecta via Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
        _db = firestore.client()
        logger.info("🔥 Google Cloud Firestore inicializado com sucesso!")
        return _db
        
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com o Firebase: {e}")
        return None
