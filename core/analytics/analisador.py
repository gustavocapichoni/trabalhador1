import os
import json
from datetime import datetime
from loguru import logger

METRICAS_FILE = "analytics/dados/metricas.json"

def calcular_score(metricas, tipo_post="feed"):
    """
    Calcula um score de performance considerando métricas específicas por tipo.
    Pesos: Retenção e Descoberta valem mais do que Likes simples.
    """
    likes    = metricas.get("likes", 0)
    comments = metricas.get("comments", 0)
    saved    = metricas.get("saved", 0)
    shares   = metricas.get("shares", 0)
    reach    = metricas.get("reach", metricas.get("impressions", 0))

    # Score base (todos os tipos)
    score = (saved * 3) + (shares * 2) + (comments * 2) + likes + (reach * 0.05)

    tipo_lower = str(tipo_post).lower()

    if "story" in tipo_lower:
        # Stories: penaliza Exits (pessoas que saíram), valoriza Taps Back (quem voltou para reler)
        taps_back    = metricas.get("taps_back", 0)
        exits        = metricas.get("exits", 0)
        replies      = metricas.get("replies", 0)
        follows      = metricas.get("follows", 0)
        score += (taps_back * 4) + (replies * 3) + (follows * 5) - (exits * 1)

    elif "reel" in tipo_lower or "pexels" in tipo_lower:
        # Reels: valoriza tempo assistido e repetições (plays > 1 = assistiu de novo)
        plays            = metricas.get("plays", 0)
        avg_watch_time   = metricas.get("ig_reels_avg_watch_time", 0)
        total_watch_time = metricas.get("ig_reels_video_view_total_time", 0)
        score += (plays * 2) + (avg_watch_time * 0.01) + (total_watch_time * 0.001)

    else:
        # Feed/Carrossel: valoriza visitas ao perfil e novos seguidores gerados
        profile_visits = metricas.get("profile_visits", 0)
        follows        = metricas.get("follows", 0)
        score += (profile_visits * 2) + (follows * 5)

    return round(score, 2)

def _calcular_distribuicao(stats_dict):
    """Transforma scores médios em uma distribuição percentual (roleta viciada)"""
    soma_medias = sum(stat["media"] for stat in stats_dict.values() if stat["media"] > 0)
    if soma_medias == 0:
        return {}
    
    distribuicao = {}
    for chave, stat in stats_dict.items():
        if stat["media"] > 0:
            distribuicao[chave] = round(stat["media"] / soma_medias, 3)
    return distribuicao

def analisar_padroes(dados_metricas, dias_limite=7):
    logger.info(f"🧠 Analisando padrões das métricas (Últimos {dias_limite} dias)...")
    posts = dados_metricas.get("posts", {})
    
    if not posts:
        return {"aviso": "Sem dados suficientes para análise"}
        
    temas_stats = {}
    formatos_stats = {}
    estilos_stats = {}
    
    total_reach = 0
    total_saves = 0
    total_posts = 0
    
    agora = datetime.now()
    
    for post_id, dados in posts.items():
        info = dados.get("info_post", {})
        mets = dados.get("metricas", {})
        
        # Filtro de data
        data_str = info.get("data")
        if not data_str: continue
        try:
            post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
            dias_passados = (agora - post_dt).days
            if dias_passados > dias_limite:
                continue
        except:
            continue
            
        tema = info.get("tema", "desconhecido")
        formato = info.get("tipo", "desconhecido")
        estilo = info.get("estilo_copy", "desconhecido")
        
        score = calcular_score(mets, tipo_post=formato)
        reach = mets.get("reach", mets.get("impressions", 0))
        saves = mets.get("saved", 0)
        
        total_reach += reach
        total_saves += saves
        total_posts += 1
        
        # Tema stats
        if tema not in temas_stats: temas_stats[tema] = {"score": 0, "count": 0}
        temas_stats[tema]["score"] += score
        temas_stats[tema]["count"] += 1
        
        # Formato stats
        if formato not in formatos_stats: formatos_stats[formato] = {"score": 0, "count": 0}
        formatos_stats[formato]["score"] += score
        formatos_stats[formato]["count"] += 1
        
        # Estilo stats (se existir)
        if estilo and estilo != "desconhecido":
            if estilo not in estilos_stats: estilos_stats[estilo] = {"score": 0, "count": 0}
            estilos_stats[estilo]["score"] += score
            estilos_stats[estilo]["count"] += 1
            
    if total_posts == 0:
        return {"aviso": f"Nenhum post encontrado nos últimos {dias_limite} dias."}
        
    # Calcula médias
    for stat in temas_stats.values():
        stat["media"] = stat["score"] / stat["count"]
    for stat in formatos_stats.values():
        stat["media"] = stat["score"] / stat["count"]
    for stat in estilos_stats.values():
        stat["media"] = stat["score"] / stat["count"]
            
    dist_temas = _calcular_distribuicao(temas_stats)
    dist_formatos = _calcular_distribuicao(formatos_stats)
    dist_estilos = _calcular_distribuicao(estilos_stats)

    resultado = {
        "periodo_dias": dias_limite,
        "distribuicao_temas": dist_temas,
        "distribuicao_formatos": dist_formatos,
        "distribuicao_estilos": dist_estilos,
        "alcance_medio": total_reach / total_posts,
        "saves_medio": total_saves / total_posts,
        "total_posts_analisados": total_posts
    }
    
    logger.success(f"✅ Análise concluída ({dias_limite} dias). Posts: {total_posts}")
    return resultado

if __name__ == "__main__":
    if os.path.exists(METRICAS_FILE):
        with open(METRICAS_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            analisar_padroes(dados)
