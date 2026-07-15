import os
import json
from datetime import datetime, timezone

RECOMENDACOES_FILE = "analytics/dados/recomendacoes.json"

# Pesos dos ciclos temporais (do mais longo para o mais curto)
# O ciclo mais longo ancora a estratégia; o mais curto refina as táticas.
PESOS_CICLO = {
    "anual":      0.35,
    "semestral":  0.25,
    "trimestral": 0.20,
    "mensal":     0.13,
    "semanal":    0.07,
}

def _combinar_distribuicoes(analises_por_periodo, chave="distribuicao_temas"):
    """Combina as distribuições de múltiplos ciclos usando os pesos ponderados.
    Ciclos com mais histórico têm maior influência sobre a estratégia final.
    """
    peso_total_usado = 0.0
    combinado = {}

    for ciclo, peso in PESOS_CICLO.items():
        analise = analises_por_periodo.get(ciclo)
        if not analise or "aviso" in analise:
            continue  # Ciclo sem dados suficientes é ignorado

        dist = analise.get(chave, {})
        for chave_val, proporcao in dist.items():
            combinado[chave_val] = combinado.get(chave_val, 0.0) + (proporcao * peso)
        peso_total_usado += peso

    # Normaliza para que a soma seja 1.0 (independente dos ciclos disponíveis)
    if peso_total_usado > 0:
        combinado = {k: round(v / peso_total_usado, 4) for k, v in combinado.items()}

    # Ordena por peso decrescente para facilitar leitura
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


def gerar_recomendacoes_cruzadas(analises_por_periodo):
    """
    Gera recomendações ponderadas por todos os ciclos disponíveis.
    Ordem de importância: Anual (35%) > Semestral (25%) > Trimestral (20%) > Mensal (13%) > Semanal (7%).
    Ciclos sem dados suficientes são ignorados e o peso é redistribuído automaticamente.
    """
    print("Gerando recomendacoes cruzadas ponderadas pelos ciclos disponíveis...")

    ciclos_disponiveis = [c for c in PESOS_CICLO if c in analises_por_periodo and "aviso" not in analises_por_periodo[c]]
    if not ciclos_disponiveis:
        print("Aviso: Nenhuma analise valida encontrada.")
        return None

    # --- Combinações Ponderadas ---
    peso_final_temas    = _combinar_distribuicoes(analises_por_periodo, "distribuicao_temas")
    peso_final_formatos = _combinar_distribuicoes(analises_por_periodo, "distribuicao_formatos")
    peso_final_estilos  = _combinar_distribuicoes(analises_por_periodo, "distribuicao_estilos")
    icc_combinado       = _combinar_icc(analises_por_periodo)
    gs_referencia       = _growth_score_referencia(analises_por_periodo)

    tema_lider, ganchos_lider = _melhor_por_growth(analises_por_periodo, "ganchos_stats")
    _, ctas_lider = _melhor_por_growth(analises_por_periodo, "ctas_stats")

    # --- Identifica o tema com maior ICC (melhor conversor de seguidores) ---
    tema_maior_icc = max(icc_combinado, key=icc_combinado.get) if icc_combinado else None

    # --- Monta o contexto textual para o Gemini ---
    ciclos_str = ", ".join(c.upper() for c in ciclos_disponiveis)
    contexto = f"CONTEXTO ESTRATEGICO (Baseado nos ciclos: {ciclos_str}):\n\n"

    contexto += "DISTRIBUICAO DE TEMAS (roleta ponderada — ciclos longos ancoram):\n"
    for tema, peso in peso_final_temas.items():
        icc_val = icc_combinado.get(tema)
        icc_str = f" | ICC: {icc_val:.1%}" if icc_val else ""
        contexto += f"  - {tema}: {peso:.1%}{icc_str}\n"

    if tema_maior_icc and icc_combinado.get(tema_maior_icc, 0) > 0:
        contexto += f"\nTEMA COM MAIOR ICC (converte mais curiosos em seguidores): {tema_maior_icc.upper()} ({icc_combinado[tema_maior_icc]:.1%})\n"
        contexto += "  -> Priorize este tema quando o objetivo for crescimento de seguidores.\n"

    if ganchos_lider:
        top_ganchos = sorted(ganchos_lider.items(), key=lambda x: x[1], reverse=True)[:3]
        contexto += f"\nGANCHOS COM MAIOR GROWTH SCORE (categorias que mais convertem):\n"
        for g, v in top_ganchos:
            contexto += f"  - {g}: {v:.4f}\n"

    if ctas_lider:
        top_ctas = sorted(ctas_lider.items(), key=lambda x: x[1], reverse=True)[:3]
        contexto += f"\nCTAs COM MAIOR GROWTH SCORE:\n"
        for c, v in top_ctas:
            contexto += f"  - {c}: {v:.4f}\n"

    contexto += f"\nGROWTH SCORE DE REFERENCIA (benchmark atual da conta): {gs_referencia:.4f}\n"
    contexto += "\nINSTRUCAO: Use a distribuicao de temas acima como roleta ponderada. Quando o objetivo for crescimento de seguidores, priorize o tema de maior ICC. Mantenha a estratégia de longo prazo mesmo que uma tendencia de curto prazo aponte em direcao diferente."

    recomendacoes = {
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "ciclos_utilizados": ciclos_disponiveis,
        "growth_score_referencia": gs_referencia,
        "icc_por_tema": icc_combinado,
        "tema_maior_icc": tema_maior_icc,
        "peso_final_temas":    peso_final_temas,
        "peso_final_formatos": peso_final_formatos,
        "peso_final_estilos":  peso_final_estilos,
        "ganchos_growth_score": ganchos_lider,
        "ctas_growth_score":   ctas_lider,
        "contexto_para_gemini": contexto,
        "analises_raw": analises_por_periodo,
    }

    os.makedirs(os.path.dirname(RECOMENDACOES_FILE), exist_ok=True)
    with open(RECOMENDACOES_FILE, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)

    print(f"Recomendacoes cruzadas geradas. Ciclos usados: {ciclos_str}. Growth Score de referencia: {gs_referencia:.4f}")
    return recomendacoes

if __name__ == "__main__":
    pass
