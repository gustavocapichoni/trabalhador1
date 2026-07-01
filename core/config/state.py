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
