import os
import json
from loguru import logger
from google.cloud import firestore
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()

_db = None

def get_db():
    global _db
    
    if _db is not None:
        return _db
        
    firebase_creds_str = os.getenv("FIREBASE_CREDENTIALS")
    
    if not firebase_creds_str:
        logger.warning("FIREBASE_CREDENTIALS não encontrado no .env. O Analytics funcionará apenas localmente com avisos se chamado.")
        return None
        
    try:
        # Se a string veio com aspas simples extras nas pontas, nós limpamos
        if firebase_creds_str.startswith("'") and firebase_creds_str.endswith("'"):
            firebase_creds_str = firebase_creds_str[1:-1]
            
        cred_dict = json.loads(firebase_creds_str)
        
        # Conecta diretamente via Google Cloud Firestore client nativo
        _db = firestore.Client.from_service_account_info(cred_dict)
        logger.info("🔥 Google Cloud Firestore inicializado com sucesso!")
        return _db
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar FIREBASE_CREDENTIALS: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com o Firebase: {e}")
        return None
