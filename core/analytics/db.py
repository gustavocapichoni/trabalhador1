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

def get_db():
    global _db
    
    if _db is not None:
        return _db
        
    # 1. Tenta a credencial direta da memória do SO (GitHub Secrets)
    # 2. Tenta a credencial do .env
    firebase_creds_str = _direct_env_creds or os.getenv("FIREBASE_CREDENTIALS")
    
    # 3. Fallback: tenta buscar arquivos locais de credenciais
    if not firebase_creds_str or len(firebase_creds_str.strip()) < 20:
        for p in ["codigo da sabedoria/firebase-credentials.json", "firebase-credentials.json"]:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        firebase_creds_str = f.read()
                    break
                except Exception:
                    pass

    if not firebase_creds_str:
        logger.warning("FIREBASE_CREDENTIALS não encontrado no .env. O Analytics funcionará apenas localmente com avisos se chamado.")
        return None
        
    try:
        firebase_creds_str = firebase_creds_str.strip()
        if (firebase_creds_str.startswith("'") and firebase_creds_str.endswith("'")) or \
           (firebase_creds_str.startswith('"') and firebase_creds_str.endswith('"')):
            firebase_creds_str = firebase_creds_str[1:-1].strip()
            
        cred_dict = None
        try:
            cred_dict = json.loads(firebase_creds_str)
        except json.JSONDecodeError:
            # Caso venha com quebras de linha reais na chave RSA
            cleaned_str = firebase_creds_str.replace('\r\n', '\\n').replace('\n', '\\n').replace('\r', '')
            try:
                cred_dict = json.loads(cleaned_str)
            except json.JSONDecodeError:
                # Tenta fallback de arquivo local caso a string da secret tenha sido truncada no .env
                for p in ["codigo da sabedoria/firebase-credentials.json", "firebase-credentials.json"]:
                    if os.path.exists(p):
                        with open(p, "r", encoding="utf-8") as f:
                            cred_dict = json.load(f)
                        break

        if not cred_dict:
            logger.error("❌ Não foi possível decodificar as credenciais do Firebase.")
            return None
        
        # Conecta via Firebase Admin SDK
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            
        _db = firestore.client()
        logger.info("🔥 Google Cloud Firestore inicializado com sucesso!")
        return _db
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar FIREBASE_CREDENTIALS: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com o Firebase: {e}")
        return None
