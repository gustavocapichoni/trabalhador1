import os
import requests
import feedparser
from datetime import datetime, timezone, timedelta
from loguru import logger
from urllib.parse import quote



def coletar_rss(dias=7):
    """
    Lê os feeds RSS de notícias e retorna as principais manchetes da semana.
    """
    logger.info("📰 [Olhos da Rede] Lendo RSS de Notícias (Infomoney, Exame)...")
    feeds = [
        "https://www.infomoney.com.br/feed/",
        "https://exame.com/feed/"
    ]
    
    manchetes_relevantes = []
    agora = datetime.now(timezone.utc)
    limite_data = agora - timedelta(days=dias)
    
    try:
        for url in feeds:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]: # Analisa as 15 últimas de cada feed
                # Verifica data
                try:
                    from time import mktime
                    dt_pub = datetime.fromtimestamp(mktime(entry.published_parsed), tz=timezone.utc)
                    if dt_pub < limite_data:
                        continue
                except Exception:
                    pass
                
                # Verifica se a notícia é relevante para o nicho (tem termos ou é destaque)
                titulo = entry.title
                manchetes_relevantes.append(titulo)
                
        # Retorna uma amostra das melhores (ex: 5 aleatórias para dar diversidade)
        import random
        if len(manchetes_relevantes) > 5:
            manchetes_relevantes = random.sample(manchetes_relevantes, 5)
            
        return manchetes_relevantes
    except Exception as e:
        logger.warning(f"⚠️ Erro ao ler RSS: {e}")
        return []

def coletar_trends():
    """
    Lê o feed RSS diário do Google Trends Brasil.
    """
    logger.info("📈 [Olhos da Rede] Lendo Google Trends Brasil...")
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=BR"
    trends_encontrados = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]: # Pega o Top 5 do Brasil hoje
            trends_encontrados.append(entry.title)
        return trends_encontrados
    except Exception as e:
        logger.warning(f"⚠️ Erro ao ler Google Trends: {e}")
        return []

def coletar_youtube(dias=7, tema_especifico=None):
    """
    Usa a API do YouTube para buscar os vídeos mais assistidos da semana no nosso nicho.
    Cobre todos os 8 temas do projeto para capturar tendências em qualquer área.
    """
    logger.info("🎥 [Olhos da Rede] Espionando YouTube (Top vídeos da semana)...")
    api_key = os.getenv("YOUTUBE_API_KEY")
    if not api_key:
        logger.warning("⚠️ Chave YOUTUBE_API_KEY não encontrada. Pulando YouTube.")
        return []
        
    agora = datetime.now(timezone.utc)
    limite_data = agora - timedelta(days=dias)
    data_formatada = limite_data.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    # Cobre todos os 8 temas do projeto + o tema específico do dia (se houver)
    # para capturar o que está bombando em qualquer um dos nossos nichos nesta semana
    query_base = (
        "desenvolvimento pessoal OR disciplina OR autossabotagem OR "
        "mentalidade financeira OR liberdade financeira OR relacionamentos OR "
        "proposito de vida OR psicologia comportamental OR habitos OR "
        "superacao pessoal OR inteligencia emocional OR "
        "fe OR espiritualidade OR crescimento espiritual OR filosofia de vida"
    )
    
    if tema_especifico:
        # Coloca o tema do dia em primeiro para dar mais peso a ele na busca
        query_final = f"{tema_especifico} OR {query_base}"
        logger.info(f"🔍 Buscando tendências com foco no tema do dia: {tema_especifico}")
    else:
        query_final = query_base
        logger.info("🔍 Buscando tendências nos 8 temas do projeto.")
    
    url = (f"https://www.googleapis.com/youtube/v3/search"
           f"?part=snippet"
           f"&q={quote(query_final)}"
           f"&type=video"
           f"&order=viewCount" # Traz os mais VISTOS
           f"&publishedAfter={data_formatada}" # Apenas desta semana!
           f"&relevanceLanguage=pt" # Foca em português
           f"&maxResults=7"
           f"&key={api_key}")
           
    titulos_youtube = []
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                titulo = item.get("snippet", {}).get("title", "")
                if titulo:
                    titulos_youtube.append(titulo)
        else:
            logger.warning(f"⚠️ Erro na API do YouTube: {response.text}")
    except Exception as e:
        logger.warning(f"⚠️ Falha de conexão com YouTube: {e}")
        
    return titulos_youtube


def gerar_contexto_mundo_real(dias=7, tema_especifico=None):
    """
    Compila todas as fontes de dados em um único texto para o Gemini ler.
    """
    logger.info(f"👁️ [Olhos da Rede] Iniciando varredura global (Últimos {dias} dias)...")
    
    noticias = coletar_rss(dias=dias)
    trends = coletar_trends()
    youtube = coletar_youtube(dias=dias, tema_especifico=tema_especifico)
    
    contexto = "🌍 O QUE ESTÁ ACONTECENDO NO MUNDO REAL NESTA SEMANA:\n\n"
    
    if youtube:
        contexto += "[YOUTUBE - VÍDEOS MAIS VISTOS DA SEMANA NO NICHO]:\n"
        for t in youtube:
            contexto += f"- {t}\n"
        contexto += "\n"
        
    if trends:
        contexto += "[GOOGLE TRENDS - ASSUNTOS MAIS BUSCADOS HOJE NO BRASIL]:\n"
        for t in trends:
            contexto += f"- {t}\n"
        contexto += "\n"
        
    if noticias:
        contexto += "[MERCADO & NOTÍCIAS - MANCHETES DA SEMANA]:\n"
        for t in noticias:
            contexto += f"- {t}\n"
        contexto += "\n"
        
    contexto += ("INSTRUÇÃO ESTRATÉGICA PARA A IA: Ao criar seu conteúdo, use essas "
                 "informações para se conectar com a urgência e o sentimento atual da audiência. "
                 "Não cite as notícias como um repórter, mas entenda a 'Vibe' da semana para ser "
                 "extremamente relevante e viral.\n")
                 
    return contexto
