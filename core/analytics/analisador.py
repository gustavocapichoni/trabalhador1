import os
import json
from datetime import datetime
from loguru import logger

METRICAS_FILE = "analytics/dados/metricas.json"

def calcular_score(metricas, tipo_post="feed"):
    """
    Score de engajamento legado (mantido para compatibilidade).
    Pesos: Salvamentos e Compartilhamentos valem mais que Likes simples.
    """
    likes    = metricas.get("likes", 0)
    comments = metricas.get("comments", 0)
    saved    = metricas.get("saved", 0)
    shares   = metricas.get("shares", 0)
    reach    = metricas.get("reach", metricas.get("impressions", 0))

    score = (saved * 3) + (shares * 2) + (comments * 2) + likes + (reach * 0.05)

    tipo_lower = str(tipo_post).lower()

    if "story" in tipo_lower:
        taps_back = metricas.get("taps_back", 0)
        exits     = metricas.get("exits", 0)
        replies   = metricas.get("replies", 0)
        follows   = metricas.get("follows", 0)
        score += (taps_back * 4) + (replies * 3) + (follows * 5) - (exits * 1)

    elif "reel" in tipo_lower or "pexels" in tipo_lower:
        plays            = metricas.get("plays", 0)
        avg_watch_time   = metricas.get("ig_reels_avg_watch_time", 0)
        total_watch_time = metricas.get("ig_reels_video_view_total_time", 0)
        profile_visits   = metricas.get("profile_visits", 0)
        follows          = metricas.get("follows", 0)
        score += (plays * 2) + (avg_watch_time * 0.01) + (total_watch_time * 0.001) + (profile_visits * 2) + (follows * 5)

    else:
        profile_visits = metricas.get("profile_visits", 0)
        follows        = metricas.get("follows", 0)
        score += (profile_visits * 2) + (follows * 5)

    return round(score, 2)


def calcular_growth_score(metricas, info_post=None):
    """
    Growth Score: mede o potencial de crescimento real do perfil (KPI principal).
    Calculado dinamicamente a partir dos dados brutos do Instagram em tempo de analise.
    """

    # Fallback: recalcula a partir dos campos brutos
    views       = metricas.get("views", metricas.get("plays", 0))
    saves       = metricas.get("saved", 0)
    shares      = metricas.get("shares", 0)
    follows     = metricas.get("follows", 0)
    prof_visits = metricas.get("profile_visits", 0)
    avg_watch   = metricas.get("ig_reels_avg_watch_time", 0)  # em ms
    duracao     = (info_post or {}).get("duracao_video", 0)

    gs_conversao   = (follows / prof_visits) if prof_visits > 0 else 0
    gs_curiosidade = (prof_visits / views) if views > 0 else 0
    gs_retencao    = (avg_watch / 1000 / duracao) if (avg_watch > 0 and duracao > 0) else 0
    gs_share       = (shares / views) if views > 0 else 0
    gs_save        = (saves / views) if views > 0 else 0

    return round(
        0.35 * gs_conversao
        + 0.20 * gs_curiosidade
        + 0.20 * gs_retencao
        + 0.15 * gs_share
        + 0.10 * gs_save,
        4
    )


def _calcular_distribuicao(stats_dict, chave_score="growth_score"):
    """Transforma scores médios em uma distribuição percentual (roleta viciada)."""
    soma = sum(s[chave_score] for s in stats_dict.values() if s.get(chave_score, 0) > 0)
    if soma == 0:
        return {}
    return {
        k: round(v[chave_score] / soma, 3)
        for k, v in stats_dict.items()
        if v.get(chave_score, 0) > 0
    }


def _stats_vazio():
    return {
        "growth_score": 0.0,
        "engagement_score": 0.0,
        "ctr_feed": 0.0,
        "taxa_salvamento": 0.0,
        "taxa_compartilhamento": 0.0,
        "taxa_visita_perfil": 0.0,
        "conversao_perfil": 0.0,
        "count": 0,
    }


def _acumular(acum, metricas, info_post, tipo_post):
    """Acumula as metricas de um post nos dicionarios de agregacao."""
    gs = calcular_growth_score(metricas, info_post)
    es = calcular_score(metricas, tipo_post=tipo_post)

    views       = metricas.get("views", metricas.get("plays", 0))
    impressions = metricas.get("impressions", metricas.get("reach", 0))
    saves       = metricas.get("saved", 0)
    shares      = metricas.get("shares", 0)
    follows     = metricas.get("follows", 0)
    prof_visits = metricas.get("profile_visits", 0)

    ctr_feed = (views / impressions) if impressions > 0 else 0
    taxa_salvamento = (saves / views) if views > 0 else 0
    taxa_compartilhamento = (shares / views) if views > 0 else 0
    taxa_visita_perfil = (prof_visits / views) if views > 0 else 0
    conversao_perfil = (follows / prof_visits) if prof_visits > 0 else 0

    acum["growth_score"]          += gs
    acum["engagement_score"]      += es
    acum["ctr_feed"]              += ctr_feed
    acum["taxa_salvamento"]       += taxa_salvamento
    acum["taxa_compartilhamento"] += taxa_compartilhamento
    acum["taxa_visita_perfil"]    += taxa_visita_perfil
    acum["conversao_perfil"]      += conversao_perfil
    acum["count"]                 += 1


def _medias(acum):
    """Calcula médias para todos os campos acumulados."""
    n = acum["count"]
    if n == 0:
        return acum
    return {k: round(v / n, 4) if k != "count" else v for k, v in acum.items()}


def analisar_padroes(dados_metricas, dias_limite=7):
    logger.info(f"Analisando padroes das metricas (Ultimos {dias_limite} dias)...")
    posts = dados_metricas.get("posts", {})

    if not posts:
        return {"aviso": "Sem dados suficientes para analise"}

    temas_stats     = {}
    formatos_stats  = {}
    estilos_stats   = {}
    ganchos_stats   = {}   # Nivel 8: eficiencia por categoria de gancho
    ctas_stats      = {}   # Nivel 9: eficiencia por tipo de CTA
    
    # --- Novas Dimensões Analíticas ---
    imagens_stats       = {}
    musicas_stats       = {}
    tons_stats          = {}
    estruturas_stats    = {}
    complexidades_stats = {}

    total_reach = 0
    total_saves = 0
    total_posts = 0

    # ICC: acumula follows e visitas por tema para calcular ao final
    icc_por_tema = {}  # tema -> {"follows": X, "visitas": Y}

    agora = datetime.now()

    for post_id, dados in posts.items():
        info = dados.get("info_post", {})
        mets = dados.get("metricas", {})

        # Filtro de data
        data_str = info.get("data")
        if not data_str:
            continue
        try:
            post_dt = datetime.strptime(data_str, "%Y-%m-%d %H:%M:%S")
            if (agora - post_dt).days > dias_limite:
                continue
        except Exception:
            continue

        tema          = info.get("tema", "desconhecido")
        formato       = info.get("tipo", "desconhecido")
        estilo        = info.get("estilo_copy", "desconhecido")
        gancho_cat    = info.get("gancho_categoria", "")
        tipo_cta      = info.get("tipo_cta", "")
        
        imagem_cat    = info.get("categoria_imagem", "")
        musica_cat    = info.get("categoria_musica", "")
        tom_emocional = info.get("tom_emocional", "")
        estrutura     = info.get("estrutura_narrativa", "")
        complexidade  = info.get("complexidade", "")

        # --- Agregação por Tema ---
        if tema not in temas_stats:
            temas_stats[tema] = _stats_vazio()
        _acumular(temas_stats[tema], mets, info, formato)

        # --- Agregação por Formato ---
        if formato not in formatos_stats:
            formatos_stats[formato] = _stats_vazio()
        _acumular(formatos_stats[formato], mets, info, formato)

        # --- Agregação por Estilo de Copy ---
        if estilo and estilo != "desconhecido":
            if estilo not in estilos_stats:
                estilos_stats[estilo] = _stats_vazio()
            _acumular(estilos_stats[estilo], mets, info, formato)

        # --- Nivel 8: Eficiencia por Categoria de Gancho ---
        if gancho_cat:
            if gancho_cat not in ganchos_stats:
                ganchos_stats[gancho_cat] = _stats_vazio()
            _acumular(ganchos_stats[gancho_cat], mets, info, formato)

        # --- Nivel 9: Eficiencia por Tipo de CTA ---
        if tipo_cta:
            if tipo_cta not in ctas_stats:
                ctas_stats[tipo_cta] = _stats_vazio()
            _acumular(ctas_stats[tipo_cta], mets, info, formato)

        # --- Novas Agregações ---
        if imagem_cat:
            if imagem_cat not in imagens_stats:
                imagens_stats[imagem_cat] = _stats_vazio()
            _acumular(imagens_stats[imagem_cat], mets, info, formato)

        if musica_cat:
            if musica_cat not in musicas_stats:
                musicas_stats[musica_cat] = _stats_vazio()
            _acumular(musicas_stats[musica_cat], mets, info, formato)

        if tom_emocional:
            if tom_emocional not in tons_stats:
                tons_stats[tom_emocional] = _stats_vazio()
            _acumular(tons_stats[tom_emocional], mets, info, formato)

        if estrutura:
            if estrutura not in estruturas_stats:
                estruturas_stats[estrutura] = _stats_vazio()
            _acumular(estruturas_stats[estrutura], mets, info, formato)

        if complexidade:
            if complexidade not in complexidades_stats:
                complexidades_stats[complexidade] = _stats_vazio()
            _acumular(complexidades_stats[complexidade], mets, info, formato)

        # --- ICC: acumula follows e visitas por tema ---
        follows_post  = mets.get("follows", 0)
        visitas_post  = mets.get("profile_visits", 0)
        if tema not in icc_por_tema:
            icc_por_tema[tema] = {"follows": 0, "visitas": 0}
        icc_por_tema[tema]["follows"]  += follows_post
        icc_por_tema[tema]["visitas"]  += visitas_post

        total_reach += mets.get("reach", mets.get("impressions", 0))
        total_saves += mets.get("saved", 0)
        total_posts += 1

    if total_posts == 0:
        return {"aviso": f"Nenhum post encontrado nos ultimos {dias_limite} dias."}

    # Calcula médias
    for d in [temas_stats, formatos_stats, estilos_stats, ganchos_stats, ctas_stats, imagens_stats, musicas_stats, tons_stats, estruturas_stats, complexidades_stats]:
        for k in d:
            d[k] = _medias(d[k])

    # Distribuições baseadas em Growth Score (KPI principal)
    dist_temas    = _calcular_distribuicao(temas_stats)
    dist_formatos = _calcular_distribuicao(formatos_stats)
    dist_estilos  = _calcular_distribuicao(estilos_stats)

    # ICC por tema: Seguidores / Visitas ao Perfil (segmentado por tema)
    icc_calculado = {}
    for tema, vals in icc_por_tema.items():
        if vals["visitas"] > 0:
            icc_calculado[tema] = round(vals["follows"] / vals["visitas"], 4)

    resultado = {
        "periodo_dias": dias_limite,
        "total_posts_analisados": total_posts,
        "alcance_medio": round(total_reach / total_posts, 2),
        "saves_medio": round(total_saves / total_posts, 2),
        # Distribuições para roleta de seleção (baseadas em Growth Score)
        "distribuicao_temas":    dist_temas,
        "distribuicao_formatos": dist_formatos,
        "distribuicao_estilos":  dist_estilos,
        # KPIs detalhados por dimensão
        "temas_stats":    temas_stats,
        "formatos_stats": formatos_stats,
        "estilos_stats":  estilos_stats,
        "ganchos_stats":  ganchos_stats,
        "ctas_stats":     ctas_stats,
        "imagens_stats":  imagens_stats,
        "musicas_stats":  musicas_stats,
        "tons_stats":     tons_stats,
        "estruturas_stats": estruturas_stats,
        "complexidades_stats": complexidades_stats,
        # Santo Graal: ICC por tema
        "icc_por_tema": icc_calculado,
    }

    logger.success(f"Analise concluida ({dias_limite} dias). Posts: {total_posts}")
    return resultado


if __name__ == "__main__":
    if os.path.exists(METRICAS_FILE):
        with open(METRICAS_FILE, "r", encoding="utf-8") as f:
            dados = json.load(f)
            analisar_padroes(dados)
