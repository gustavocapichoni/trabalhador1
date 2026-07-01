import os
import json
from datetime import datetime

METRICAS_FILE = "analytics/dados/metricas.json"

def calcular_score(metricas):
    """
    Calcula um score de performance usando pesos arbitrários, priorizando 
    Saves e Comments sobre Likes, e Reach como multiplicador base.
    """
    likes = metricas.get("likes", 0)
    comments = metricas.get("comments", 0)
    saved = metricas.get("saved", 0)
    shares = metricas.get("shares", 0) # Pode não existir dependendo da API
    reach = metricas.get("reach", metricas.get("impressions", 0))
    
    score = (saved * 3) + (shares * 2) + (comments * 2) + likes + (reach * 0.05)
    return score

def analisar_padroes(dados_metricas):
    print("Analisando padrões das métricas...")
    posts = dados_metricas.get("posts", {})
    
    if not posts:
        return {"aviso": "Sem dados suficientes para análise"}
        
    temas_stats = {}
    formatos_stats = {}
    estilos_stats = {}
    
    total_reach = 0
    total_saves = 0
    total_posts = 0
    
    for post_id, dados in posts.items():
        info = dados.get("info_post", {})
        mets = dados.get("metricas", {})
        
        tema = info.get("tema", "desconhecido")
        formato = info.get("tipo", "desconhecido")
        estilo = info.get("estilo_copy", "desconhecido")
        
        score = calcular_score(mets)
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
            
    # Calcula médias
    melhor_tema = None
    maior_media_tema = -1
    pior_tema = None
    menor_media_tema = float('inf')
    
    for tema, stat in temas_stats.items():
        media = stat["score"] / stat["count"]
        stat["media"] = media
        if media > maior_media_tema:
            maior_media_tema = media
            melhor_tema = tema
        if media < menor_media_tema:
            menor_media_tema = media
            pior_tema = tema
            
    melhor_formato = None
    maior_media_formato = -1
    for formato, stat in formatos_stats.items():
        media = stat["score"] / stat["count"]
        stat["media"] = media
        if media > maior_media_formato:
            maior_media_formato = media
            melhor_formato = formato
            
    melhor_estilo = None
    maior_media_estilo = -1
    for estilo, stat in estilos_stats.items():
        media = stat["score"] / stat["count"]
        stat["media"] = media
        if media > maior_media_estilo:
            maior_media_estilo = media
            melhor_estilo = estilo

    resultado = {
        "melhor_tema": melhor_tema,
        "pior_tema": pior_tema,
        "melhor_formato": melhor_formato,
        "melhor_estilo": melhor_estilo,
        "alcance_medio": total_reach / total_posts if total_posts > 0 else 0,
        "saves_medio": total_saves / total_posts if total_posts > 0 else 0,
        "total_posts_analisados": total_posts
    }
    
    print(f"Padrões identificados: Melhor tema: {melhor_tema}, Melhor formato: {melhor_formato}")
    return resultado

if __name__ == "__main__":
    if os.path.exists(METRICAS_FILE):
        with open(METRICAS_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            analisar_padroes(dados)
