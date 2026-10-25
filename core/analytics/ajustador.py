import os
import json
import requests
import time
from datetime import datetime, timezone

RECOMENDACOES_FILE = "analytics/dados/recomendacoes.json"

# Pesos dos ciclos temporais (mantidos para o sistema matemático e para o Dashboard)
PESOS_CICLO = {
    "anual":      0.35,
    "semestral":  0.25,
    "trimestral": 0.20,
    "mensal":     0.13,
    "semanal":    0.07,
}

# ─────────────────────────────────────────────────────────────────────
# SISTEMA MATEMÁTICO (mantido para o Dashboard e como contexto para a IA)
# ─────────────────────────────────────────────────────────────────────

def _combinar_distribuicoes(analises_por_periodo, chave="distribuicao_temas"):
    """Combina as distribuições de múltiplos ciclos usando os pesos ponderados."""
    peso_total_usado = 0.0
    combinado = {}
    for ciclo, peso in PESOS_CICLO.items():
        analise = analises_por_periodo.get(ciclo)
        if not analise or "aviso" in analise:
            continue
        dist = analise.get(chave, {})
        for chave_val, proporcao in dist.items():
            combinado[chave_val] = combinado.get(chave_val, 0.0) + (proporcao * peso)
        peso_total_usado += peso
    if peso_total_usado > 0:
        combinado = {k: round(v / peso_total_usado, 4) for k, v in combinado.items()}
    return dict(sorted(combinado.items(), key=lambda x: x[1], reverse=True))


def _combinar_icc(analises_por_periodo):
    """Combina os ICC de múltiplos ciclos com os mesmos pesos."""
    peso_total_usado = 0.0
    combinado = {}
    for ciclo, peso in PESOS_CICLO.items():
        analise = analises_por_periodo.get(ciclo)
        if not analise or "aviso" in analise:
            continue
        icc = analise.get("icc_por_tema", {})
        for tema, valor in icc.items():
            combinado[tema] = combinado.get(tema, 0.0) + (valor * peso)
        peso_total_usado += peso
    if peso_total_usado > 0:
        combinado = {k: round(v / peso_total_usado, 4) for k, v in combinado.items()}
    return dict(sorted(combinado.items(), key=lambda x: x[1], reverse=True))


def _melhor_por_growth(analises_por_periodo, chave_stats):
    """Retorna a dimensão com maior growth_score médio ponderado pelos ciclos."""
    combinado = {}
    peso_total_usado = 0.0
    for ciclo, peso in PESOS_CICLO.items():
        analise = analises_por_periodo.get(ciclo)
        if not analise or "aviso" in analise:
            continue
        stats = analise.get(chave_stats, {})
        for k, v in stats.items():
            gs = v.get("growth_score", 0)
            combinado[k] = combinado.get(k, 0.0) + (gs * peso)
        peso_total_usado += peso
    if peso_total_usado > 0 and combinado:
        combinado = {k: round(v / peso_total_usado, 4) for k, v in combinado.items()}
        return max(combinado, key=combinado.get), combinado
    return None, {}


def _growth_score_referencia(analises_por_periodo):
    """Calcula o growth_score médio de referência ponderado pelos ciclos disponíveis."""
    gs_total = 0.0
    peso_total = 0.0
    for ciclo, peso in PESOS_CICLO.items():
        analise = analises_por_periodo.get(ciclo)
        if not analise or "aviso" in analise:
            continue
        temas = analise.get("temas_stats", {})
        if temas:
            gs_medio = sum(v.get("growth_score", 0) for v in temas.values()) / len(temas)
            gs_total += gs_medio * peso
            peso_total += peso
    return round(gs_total / peso_total, 4) if peso_total > 0 else 0.0


# ─────────────────────────────────────────────────────────────────────
# NOVO CÉREBRO: separação 80/20 + chamada à IA
# ─────────────────────────────────────────────────────────────────────

def _separar_grupos_posts(metricas):
    """
    Separa os posts em dois grupos com base no growth_score:
    - bombaram: acima de 2x a média  → peso 80%
    - top_10:   10 melhores restantes → peso 20%
    """
    posts = metricas.get("posts", {})
    posts_com_gs = []

    for pid, dados in posts.items():
        gs = dados.get("metricas", {}).get("growth_score", 0)
        info = dados.get("info_post", {})
        if gs > 0 and info:
            frase = info.get("frase_visual", "")
            if isinstance(frase, list):
                frase = frase[0] if frase else ""
            posts_com_gs.append({
                "post_id":        pid,
                "growth_score":   gs,
                "tipo":           info.get("tipo", ""),
                "tema":           info.get("tema", ""),
                "estilo_copy":    info.get("estilo_copy", ""),
                "tom_emocional":  info.get("tom_emocional", ""),
                "gancho_categoria": info.get("gancho_categoria", ""),
                "tipo_cta":       info.get("tipo_cta", ""),
                "frase_visual":   str(frase)[:120],
                "legenda":        str(info.get("legenda", ""))[:150],
                "metricas": {
                    "views":   dados.get("metricas", {}).get("views", dados.get("metricas", {}).get("plays", 0)),
                    "saves":   dados.get("metricas", {}).get("saved",   0),
                    "shares":  dados.get("metricas", {}).get("shares",  0),
                    "follows": dados.get("metricas", {}).get("follows", 0),
                },
            })

    if not posts_com_gs:
        return [], [], 0.0

    growth_medio = sum(p["growth_score"] for p in posts_com_gs) / len(posts_com_gs)
    limite_viral = growth_medio * 2.0

    bombaram = [p for p in posts_com_gs if p["growth_score"] >= limite_viral]
    restantes = sorted(
        [p for p in posts_com_gs if p["growth_score"] < limite_viral],
        key=lambda x: x["growth_score"], reverse=True
    )
    top_10 = restantes[:10]

    print(f"  Growth médio: {growth_medio:.4f} | Limite viral (2x): {limite_viral:.4f}")
    print(f"  Posts que BOMBARAM: {len(bombaram)} | Top 10 consistentes: {len(top_10)}")
    return bombaram, top_10, growth_medio


def _formatar_post_para_prompt(post, indice):
    """Formata um post em texto legível para o prompt da IA."""
    return (
        f"Post #{indice} — {post.get('tipo','').upper()} | Tema: {post.get('tema','')} | Estilo: {post.get('estilo_copy','')}\n"
        f"  Tom: {post.get('tom_emocional','')} | Gancho: {post.get('gancho_categoria','')} | CTA: {post.get('tipo_cta','')}\n"
        f"  Slide 1 (gancho): \"{post.get('frase_visual','—')}\"\n"
        f"  Legenda: \"{post.get('legenda','—')}\"\n"
        f"  Views: {post['metricas']['views']:,} | Saves: {post['metricas']['saves']} | "
        f"Shares: {post['metricas']['shares']} | Follows: {post['metricas']['follows']}\n"
        f"  Growth Score: {post['growth_score']:.4f}"
    )


def _obter_hipoteses_validadas():
    """Busca as hipóteses confirmadas do Motor de Hipóteses para enriquecer o prompt."""
    try:
        from core.analytics.motor_hipoteses import obter_hipoteses_confirmadas
        confirmadas = obter_hipoteses_confirmadas()
        if not confirmadas:
            return ""
        linhas = ["[CONHECIMENTO VALIDADO — Motor de Hipóteses]:"]
        for h in confirmadas[:5]:
            linhas.append(f"CONFIRMADO ({h.get('confianca', 0):.0%} confianca): {h.get('hipotese', '')}")
        return "\n".join(linhas)
    except Exception as e:
        print(f"  ⚠️ Aviso ao buscar hipóteses confirmadas: {e}")
        return ""


def _montar_prompt_estrategista(bombaram, top_10, growth_medio, contexto_matematico, olhos_da_rede, hipoteses_validadas):
    """Monta o prompt completo para a IA estrategista."""
    bloco_bombaram = "\n\n".join(
        _formatar_post_para_prompt(p, i + 1) for i, p in enumerate(bombaram)
    ) if bombaram else "Nenhum post atingiu o limiar viral neste período."

    bloco_top10 = "\n\n".join(
        _formatar_post_para_prompt(p, i + 1) for i, p in enumerate(top_10)
    ) if top_10 else "Dados insuficientes."

    bloco_hipoteses = hipoteses_validadas if hipoteses_validadas else "Nenhuma hipótese confirmada ainda."

    return f"""Você é o Estrategista Chefe de Conteúdo da conta @gustavo_8k_ no Instagram.
Nicho: desenvolvimento pessoal, mentalidade financeira, disciplina, espiritualidade, propósito de vida.
Missão: analisar os dados reais da semana e gerar as RECOMENDAÇÕES ESTRATÉGICAS que vão guiar TODAS as postagens da próxima semana.

[PESO 80%] POSTS QUE BOMBARAM (acima de 2x o growth médio: {growth_medio:.4f})
Estes são os mais importantes. Identifique os padrões que os tornaram virais.
{bloco_bombaram}

[PESO 20%] TOP 10 POSTS CONSISTENTES
Posts que performaram bem de forma constante (mas não viralizaram).
{bloco_top10}

TENDÊNCIAS DA SEMANA (Olhos da Rede):
{olhos_da_rede if olhos_da_rede else "Dados de tendências não disponíveis."}

CONHECIMENTO ACUMULADO (experimentos validados):
{bloco_hipoteses}

CONTEXTO HISTÓRICO (dados matemáticos — últimos 60 dias):
{contexto_matematico}

INSTRUÇÃO: Com base em TUDO acima, gere as recomendações em JSON válido com exatamente estas chaves:
{{
  "vibe_da_semana": "Tom e sentimento ideal para os posts desta semana (2-3 frases)",
  "padroes_campeoes": "O que os posts virais têm em comum que DEVE ser replicado (seja específico)",
  "temas_prioritarios": ["tema1", "tema2", "tema3"],
  "ganchos_exclusivos": ["gancho inédito 1 pronto para usar", "gancho inédito 2", "gancho inédito 3"],
  "ctas_testear": ["CTA novo 1", "CTA novo 2"],
  "ideias_de_narrativa": ["Ideia completa de post 1 (tema + gancho + desenvolvimento + CTA)", "Ideia completa de post 2"],
  "aviso_estrategico": "Algo crítico que os dados revelam que o bot deve evitar ou priorizar urgentemente",
  "contexto_para_gemini": "Resumo direto e poderoso (máximo 300 palavras) para injetar em CADA prompt de criação de post desta semana."
}}"""


def _extrair_json_da_resposta(texto):
    """Extrai o JSON da resposta da IA, lidando com markdown e texto extra."""
    import re
    texto = re.sub(r"```(?:json)?", "", texto).strip()
    try:
        return json.loads(texto)
    except Exception:
        pass
    match = re.search(r"\{.*\}", texto, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _chamar_ia_estrategista(prompt):
    """Chama a IA para gerar as recomendações. Ordem: Gemini → Groq → OpenRouter."""
    from core.config.settings import GEMINI_KEYS, GROQ_KEYS, OPENROUTER_KEY

    for idx, key in enumerate(GEMINI_KEYS):
        try:
            print(f"  🤖 Tentando Gemini (chave {idx + 1}/{len(GEMINI_KEYS)})...")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent?key={key}"
            payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.7, "maxOutputTokens": 2048}}
            resp = requests.post(url, json=payload, timeout=60)
            if resp.status_code == 200:
                texto = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                dados = _extrair_json_da_resposta(texto)
                if dados:
                    print("  ✅ Gemini: recomendações geradas com sucesso!")
                    return dados
            elif resp.status_code == 429:
                print(f"  ⚠️ Gemini chave {idx + 1}: cota esgotada.")
                time.sleep(2)
            else:
                print(f"  ⚠️ Gemini chave {idx + 1}: erro {resp.status_code} — {resp.text[:120]}")
        except Exception as e:
            print(f"  ⚠️ Gemini chave {idx + 1} falhou: {str(e)[:80]}")

    for idx, key in enumerate(GROQ_KEYS):
        try:
            print(f"  🤖 Tentando Groq (chave {idx + 1}/{len(GROQ_KEYS)})...")
            resp = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2048},
                timeout=60
            )
            if resp.status_code == 200:
                texto = resp.json()["choices"][0]["message"]["content"]
                dados = _extrair_json_da_resposta(texto)
                if dados:
                    print("  ✅ Groq: recomendações geradas com sucesso!")
                    return dados
            elif resp.status_code == 429:
                print(f"  ⚠️ Groq chave {idx + 1}: cota esgotada.")
        except Exception as e:
            print(f"  ⚠️ Groq chave {idx + 1} falhou: {str(e)[:80]}")

    if OPENROUTER_KEY:
        try:
            print("  🤖 Tentando OpenRouter...")
            resp = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "temperature": 0.7, "max_tokens": 2048},
                timeout=60
            )
            if resp.status_code == 200:
                texto = resp.json()["choices"][0]["message"]["content"]
                dados = _extrair_json_da_resposta(texto)
                if dados:
                    print("  ✅ OpenRouter: recomendações geradas com sucesso!")
                    return dados
        except Exception as e:
            print(f"  ⚠️ OpenRouter falhou: {str(e)[:80]}")

    print("  ❌ Todas as IAs falharam. Usando fallback matemático.")
    return None


# ─────────────────────────────────────────────────────────────────────
# PONTO DE ENTRADA PRINCIPAL
# ─────────────────────────────────────────────────────────────────────

def gerar_recomendacoes_cruzadas(analises_por_periodo, metricas=None):
    """
    Gera recomendações estratégicas combinando:
    1. Sistema matemático (mantido para o Dashboard)
    2. Nova IA estrategista com lógica 80/20 (posts que bombaram)
    """
    print("🧠 Gerando recomendações com IA estrategista (regra 80/20)...")

    ciclos_disponiveis = [c for c in PESOS_CICLO if c in analises_por_periodo and "aviso" not in analises_por_periodo[c]]

    # Sistema matemático (mantido para Dashboard)
    peso_final_temas    = _combinar_distribuicoes(analises_por_periodo, "distribuicao_temas")
    peso_final_formatos = _combinar_distribuicoes(analises_por_periodo, "distribuicao_formatos")
    peso_final_estilos  = _combinar_distribuicoes(analises_por_periodo, "distribuicao_estilos")
    icc_combinado       = _combinar_icc(analises_por_periodo)
    gs_referencia       = _growth_score_referencia(analises_por_periodo)
    _, ganchos_lider    = _melhor_por_growth(analises_por_periodo, "ganchos_stats")
    _, ctas_lider       = _melhor_por_growth(analises_por_periodo, "ctas_stats")
    tema_maior_icc      = max(icc_combinado, key=icc_combinado.get) if icc_combinado else None

    ciclos_str = ", ".join(c.upper() for c in ciclos_disponiveis)
    contexto_matematico = f"Ciclos: {ciclos_str}\n"
    contexto_matematico += "Temas (ponderados):\n"
    for tema, peso in list(peso_final_temas.items())[:5]:
        icc_val = icc_combinado.get(tema)
        icc_str = f" | ICC: {icc_val:.1%}" if icc_val else ""
        contexto_matematico += f"  - {tema}: {peso:.1%}{icc_str}\n"
    if ganchos_lider:
        top_g = sorted(ganchos_lider.items(), key=lambda x: x[1], reverse=True)[:3]
        contexto_matematico += "Ganchos líderes: " + " | ".join(f"{g} ({v:.4f})" for g, v in top_g) + "\n"
    if ctas_lider:
        top_c = sorted(ctas_lider.items(), key=lambda x: x[1], reverse=True)[:3]
        contexto_matematico += "CTAs líderes: " + " | ".join(f"{c} ({v:.4f})" for c, v in top_c) + "\n"
    contexto_matematico += f"Growth Score de referência: {gs_referencia:.4f}\n"

    # Lógica 80/20
    bombaram, top_10, growth_medio = [], [], gs_referencia
    if metricas:
        bombaram, top_10, growth_medio = _separar_grupos_posts(metricas)

    # Olhos da Rede (do Firestore)
    olhos_da_rede = ""
    try:
        from core.ai.olhos_da_rede import carregar_contexto_semanal
        olhos_da_rede = carregar_contexto_semanal() or ""
    except Exception as e:
        print(f"  ⚠️ Aviso Olhos da Rede: {e}")

    # Hipóteses validadas
    hipoteses_validadas = _obter_hipoteses_validadas()

    # Chamada à IA
    recomendacoes_ia = None
    if bombaram or top_10:
        prompt = _montar_prompt_estrategista(bombaram, top_10, growth_medio, contexto_matematico, olhos_da_rede, hipoteses_validadas)
        recomendacoes_ia = _chamar_ia_estrategista(prompt)

    if recomendacoes_ia:
        contexto_final = recomendacoes_ia.get("contexto_para_gemini", contexto_matematico)
        print("✅ Recomendações geradas pela IA estrategista!")
    else:
        contexto_final = f"CONTEXTO ESTRATÉGICO (ciclos: {ciclos_str}):\n{contexto_matematico}"
        recomendacoes_ia = {}
        print("⚠️ Usando contexto matemático como fallback.")

    recomendacoes = {
        "atualizado_em":        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "ciclos_utilizados":    ciclos_disponiveis,
        "growth_score_referencia": gs_referencia,
        "icc_por_tema":         icc_combinado,
        "tema_maior_icc":       tema_maior_icc,
        "peso_final_temas":     peso_final_temas,
        "peso_final_formatos":  peso_final_formatos,
        "peso_final_estilos":   peso_final_estilos,
        "ganchos_growth_score": ganchos_lider,
        "ctas_growth_score":    ctas_lider,
        # Novos campos da IA (não quebram o Dashboard)
        "vibe_da_semana":       recomendacoes_ia.get("vibe_da_semana", ""),
        "padroes_campeoes":     recomendacoes_ia.get("padroes_campeoes", ""),
        "temas_prioritarios":   recomendacoes_ia.get("temas_prioritarios", []),
        "ganchos_exclusivos":   recomendacoes_ia.get("ganchos_exclusivos", []),
        "ctas_testear":         recomendacoes_ia.get("ctas_testear", []),
        "ideias_de_narrativa":  recomendacoes_ia.get("ideias_de_narrativa", []),
        "aviso_estrategico":    recomendacoes_ia.get("aviso_estrategico", ""),
        "posts_que_bombaram":   len(bombaram),
        "top_10_consistentes":  len(top_10),
        # Campo principal injetado em cada postagem
        "contexto_para_gemini": contexto_final,
        "analises_raw":         analises_por_periodo,
    }

    os.makedirs(os.path.dirname(RECOMENDACOES_FILE), exist_ok=True)
    with open(RECOMENDACOES_FILE, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)

    # Envia para a coleção 'memoria_estrategica/recomendacoes' do Firestore
    try:
        from core.analytics.db import get_db
        db = get_db()
        if db:
            # Omitimos 'analises_raw' para evitar estourar o limite de 1MB de documento do Firestore
            doc_firestore = {k: v for k, v in recomendacoes.items() if k != "analises_raw"}
            db.collection("memoria_estrategica").document("recomendacoes").set(doc_firestore)
            print("🚀 Recomendações estratégicas enviadas com sucesso para o Firestore!")
        else:
            print("⚠️ Conexão com Firestore indisponível para salvar as recomendações.")
    except Exception as db_err:
        print(f"❌ Erro ao enviar recomendações para o Firestore: {db_err}")

    print(f"✅ Recomendações salvas. Ciclos: {ciclos_str} | Virais: {len(bombaram)} | Top 10: {len(top_10)}")
    return recomendacoes


if __name__ == "__main__":
    pass
