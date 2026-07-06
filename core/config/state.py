import os
import json

ESTADO_FILE = "estado.json"

def carregar_estado():
    if not os.path.exists(ESTADO_FILE):
        return {"historico": [], "ultimos_temas": [], "ultimo_carousel": 3}
    try:
        with open(ESTADO_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar {ESTADO_FILE}: {e}")
        return {"historico": [], "ultimos_temas": [], "ultimo_carousel": 3}

def salvar_estado(estado):
    try:
        with open(ESTADO_FILE, "w", encoding="utf-8") as f:
            json.dump(estado, f, indent=4, ensure_ascii=False)
    except Exception as e:
        print(f"⚠️ Erro ao salvar {ESTADO_FILE}: {e}")

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
