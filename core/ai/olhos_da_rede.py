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


def _montar_texto_contexto(youtube, trends, noticias):
    """Monta o texto de contexto a partir das listas coletadas."""
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


def gerar_contexto_mundo_real(dias=7, tema_especifico=None):
    """
    Primeiro tenta carregar o contexto semanal já salvo no Firestore (modo novo).
    Se não encontrar, faz a coleta ao vivo como fallback (comportamento original).
    """
    contexto_salvo = carregar_contexto_semanal()
    if contexto_salvo:
        logger.info("✅ [Olhos da Rede] Contexto semanal carregado do Firestore (sem chamadas externas).")
        return contexto_salvo

    # Fallback: coleta ao vivo
    logger.info("👁️ [Olhos da Rede] Contexto semanal não encontrado. Coletando ao vivo...")
    noticias = coletar_rss(dias=dias)
    trends = coletar_trends()
    youtube = coletar_youtube(dias=dias, tema_especifico=tema_especifico)
    return _montar_texto_contexto(youtube, trends, noticias)


# ─────────────────────────────────────────────────────────────────────
# MODO NOVO: coleta semanal + persistência no Firestore
# ─────────────────────────────────────────────────────────────────────

def coletar_e_salvar_semanal():
    """
    Coleta todos os dados externos da semana (YouTube, Google Trends, RSS)
    e salva na coleção 'olhos_da_rede_semanal' no Firestore.
    Deve rodar UMA VEZ por semana (toda segunda-feira às 08:00 BRT).
    """
    logger.info("🗓️ [Olhos da Rede SEMANAL] Iniciando coleta e salvamento semanal...")

    noticias = coletar_rss(dias=7)
    trends = coletar_trends()
    youtube = coletar_youtube(dias=7)
    contexto_texto = _montar_texto_contexto(youtube, trends, noticias)

    agora = datetime.now(timezone.utc)
    semana_iso = agora.strftime("%Y-W%W")

    doc = {
        "semana": semana_iso,
        "coletado_em": agora.isoformat(),
        "youtube": youtube,
        "trends": trends,
        "noticias": noticias,
        "contexto_texto": contexto_texto,
    }

    try:
        from core.analytics.db import get_db
        db = get_db()
        if db:
            db.collection("olhos_da_rede_semanal").document(semana_iso).set(doc)
            logger.success(f"✅ [Olhos da Rede] Dados da semana {semana_iso} salvos no Firestore!")
        else:
            logger.warning("⚠️ Firebase indisponível. Dados da semana não foram salvos.")
    except Exception as e:
        logger.error(f"❌ Erro ao salvar Olhos da Rede no Firestore: {e}")

    return doc


def carregar_contexto_semanal():
    """
    Carrega o contexto dos Olhos da Rede da semana atual do Firestore.
    Retorna o texto pronto para injetar no prompt, ou None se não encontrar.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return None

        agora = datetime.now(timezone.utc)
        semana_iso = agora.strftime("%Y-W%W")

        doc = db.collection("olhos_da_rede_semanal").document(semana_iso).get()
        if doc.exists:
            dados = doc.to_dict()
            contexto = dados.get("contexto_texto", "")
            if contexto:
                return contexto
        return None
    except Exception as e:
        logger.warning(f"⚠️ Erro ao carregar contexto semanal do Firestore: {e}")
        return None
