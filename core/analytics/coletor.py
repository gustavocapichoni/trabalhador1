import os
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")
ESTADO_FILE = "estado.json"
METRICAS_FILE = "analytics/dados/metricas.json"

def carregar_estado():
    if os.path.exists(ESTADO_FILE):
        try:
            with open(ESTADO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler estado.json: {e}")
    return {"historico": []}

def carregar_metricas():
    if os.path.exists(METRICAS_FILE):
        try:
            with open(METRICAS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Erro ao ler metricas.json: {e}")
    return {"posts": {}}

def salvar_metricas(metricas):
    os.makedirs(os.path.dirname(METRICAS_FILE), exist_ok=True)
    with open(METRICAS_FILE, "w", encoding="utf-8") as f:
        json.dump(metricas, f, indent=4, ensure_ascii=False)

def buscar_metricas_api(post_id):
    if not IG_ACCESS_TOKEN or post_id.startswith("DRY_RUN") or post_id == "ID_TESTE_LOCAL":
        return None
        
    metricas = {}
    
    try:
        # 1. Busca os campos diretos da mídia (likes e comentários)
        url_media = f"https://graph.facebook.com/v19.0/{post_id}?fields=like_count,comments_count,media_type&access_token={IG_ACCESS_TOKEN}"
        res_media = requests.get(url_media, timeout=15)
        if res_media.status_code == 200:
            data = res_media.json()
            metricas["likes"] = data.get("like_count", 0)
            metricas["comments"] = data.get("comments_count", 0)
            media_type = data.get("media_type")
        else:
            print(f"Erro ao buscar campos diretos da mídia {post_id}: {res_media.text}")
            return None
            
        # 2. Busca os insights (reach, saved, shares, views)
        # Os nomes das métricas mudaram recentemente na API do Facebook
        metrics_query = "reach,saved,shares,views"
            
        url_insights = f"https://graph.facebook.com/v19.0/{post_id}/insights?metric={metrics_query}&access_token={IG_ACCESS_TOKEN}"
        res_insights = requests.get(url_insights, timeout=15)
        
        if res_insights.status_code == 200:
            data = res_insights.json()
            for insight in data.get("data", []):
                name = insight.get("name")
                # Pega o total_value se existir (pode estar dentro de values[0])
                values = insight.get("values", [])
                if values:
                    val = values[0].get("value", 0)
                    metricas[name] = val
        else:
            print(f"Aviso: Não foi possível obter insights para {post_id}. Pode ser uma mídia muito recente, expirada (stories) ou erro: {res_insights.text}")
            
        return metricas
    except Exception as e:
        print(f"Erro ao coletar métricas para o post {post_id}: {e}")
        return None

def rodar_coleta():
    print("Iniciando coleta de métricas...")
    estado = carregar_estado()
    historico = estado.get("historico", [])
    metricas_salvas = carregar_metricas()
    
    agora = datetime.now(timezone.utc)
    posts_processados = 0
    
    for post in historico:
        post_id = post.get("post_id")
        data_str = post.get("data")
        
        if not post_id or post_id == "ID_TESTE_LOCAL" or post_id.startswith("DRY_RUN"):
            continue
            
        # Pular se já tem métricas atualizadas hoje
        # Na prática, num sistema mais completo, poderíamos verificar há quanto tempo a métrica foi atualizada
        # Mas aqui, como vamos rodar 1x por dia, vamos sempre atualizar os posts dos últimos 7 dias.
        
        try:
            # Data está salva como "YYYY-MM-DD HH:MM:SS" local, vamos assumir como UTC ou converter.
            post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        except:
            continue
            
        # Pular posts com menos de 24h (métricas não estabilizadas)
        if agora - post_dt < timedelta(hours=24):
            continue
            
        # Pular posts muito antigos (mais de 14 dias), para economizar chamadas de API
        if agora - post_dt > timedelta(days=14):
            continue
            
        print(f"Coletando métricas para o post {post_id} ({post.get('tipo')} - {post.get('tema')})...")
        novas_metricas = buscar_metricas_api(post_id)
        
        if novas_metricas:
            if post_id not in metricas_salvas["posts"]:
                metricas_salvas["posts"][post_id] = {}
                
            metricas_salvas["posts"][post_id]["info_post"] = post
            metricas_salvas["posts"][post_id]["metricas"] = novas_metricas
            metricas_salvas["posts"][post_id]["ultima_atualizacao"] = agora.strftime("%Y-%m-%d %H:%M:%S")
            posts_processados += 1
            
        time.sleep(2) # Respeitar limites da API
        
    salvar_metricas(metricas_salvas)
    print(f"Coleta finalizada. {posts_processados} posts atualizados.")
    return metricas_salvas

if __name__ == "__main__":
    rodar_coleta()
