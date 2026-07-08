import os
import json
from loguru import logger
from core.analytics.db import get_db

ESTADO_FILE = "estado_migrado.json"
MIGRADO_FILE = "estado_migrado.json"
DEFAULT_STATE = {"historico": [], "ultimos_temas": [], "ultimo_carousel": 3}

def carregar_estado():
    db = get_db()
    
    # Fallback caso o Firebase não esteja configurado
    if not db:
        if os.path.exists(ESTADO_FILE):
            try:
                with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Erro ao carregar {ESTADO_FILE}: {e}")
        return DEFAULT_STATE.copy()

    try:
        doc_ref = db.collection("bot_config").document("app_state")
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        else:
            # Migração local -> nuvem
            if os.path.exists(ESTADO_FILE):
                logger.info("Migrando estado_migrado.json local para o Firebase...")
                with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                    local_state = json.load(f)
                
                # Faz o save no firebase
                doc_ref.set(local_state, merge=True)
                os.rename(ESTADO_FILE, MIGRADO_FILE)
                logger.success("Migração do estado concluída com sucesso!")
                return local_state
            
            return DEFAULT_STATE.copy()
            
    except Exception as e:
        logger.warning(f"Erro ao carregar estado do Firebase: {e}")
        # Recuperação de emergência (falta de rede)
        if os.path.exists(ESTADO_FILE):
             with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                  return json.load(f)
        elif os.path.exists(MIGRADO_FILE):
             with open(MIGRADO_FILE, "r", encoding="utf-8") as f:
                  return json.load(f)
        return DEFAULT_STATE.copy()

def salvar_estado(estado):
    db = get_db()
    if not db:
        try:
            with open(ESTADO_FILE, "w", encoding="utf-8") as f:
                json.dump(estado, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Erro ao salvar {ESTADO_FILE}: {e}")
        return

    try:
        doc_ref = db.collection("bot_config").document("app_state")
        doc_ref.set(estado, merge=True)
    except Exception as e:
        logger.error(f"Erro ao salvar estado no Firebase: {e}")

def verificar_midia_recente(midia_id):
    """Verifica se uma mídia (URL ou ID) foi usada recentemente (últimas 15 postagens)."""
    if not midia_id:
        return False
    estado = carregar_estado()
    historico = estado.get("historico_midia", [])
    return midia_id in historico

def registrar_midia_usada(midia_id):
    """Registra uma mídia (URL ou ID) no histórico para evitar repetição."""
    if not midia_id:
        return
    estado = carregar_estado()
    if "historico_midia" not in estado:
        estado["historico_midia"] = []
    
    estado["historico_midia"].insert(0, midia_id)
    # Mantém apenas as últimas 15 mídias na memória
    estado["historico_midia"] = estado["historico_midia"][:15]
    salvar_estado(estado)
