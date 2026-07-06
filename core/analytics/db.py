import os
import json
from loguru import logger
import firebase_admin
from firebase_admin import credentials, firestore
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
        
        # Inicializa o app do Firebase se ainda não foi inicializado
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            logger.info("🔥 Firebase Admin inicializado com sucesso!")
            
        _db = firestore.client()
        return _db
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Erro ao decodificar FIREBASE_CREDENTIALS: {e}")
        return None
    except Exception as e:
        logger.error(f"❌ Erro ao conectar com o Firebase: {e}")
        return None
