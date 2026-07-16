"""
Motor de Hipóteses — Sistema de Memória Estratégica

Transforma o bot de um publicador automático em um pesquisador autônomo.
Ele observa os padrões de dados, formula hipóteses, rastreia experimentos e
acumula conhecimento validado estatisticamente para orientar os próximos posts.

Fluxo:
  Observação → Cria Hipótese → Planeja Experimento → Executa (via posts) →
  Analisa Resultados → Confirma ou Rejeita → Atualiza Conhecimento → Cria Novas Hipóteses
"""
import os
import json
import uuid
from datetime import datetime, timezone
from loguru import logger

MEMORIA_FILE = "analytics/dados/memoria_estrategica.json"
AMOSTRA_MINIMA = 30          # Posts mínimos por grupo para considerar válido
DIFERENCA_MINIMA = 0.15      # 15% de diferença entre grupos A e B para confirmar
CONFIANCA_CONFIRMACAO = 0.75 # Confiança mínima para marcar como "confirmada"


def _get_db():
    """Obtém a conexão com o Firebase de forma segura."""
    try:
        from core.analytics.db import get_db
        return get_db()
    except Exception:
        return None


def _carregar_memoria():
    """Carrega a memória estratégica. Prioriza Firebase; usa arquivo local como fallback."""
    db = _get_db()
    if db:
        try:
            doc = db.collection("memoria_estrategica").document("hipoteses").get()
            if doc.exists:
                memoria = doc.to_dict()
                # Garante a estrutura correta
                if "hipoteses" not in memoria:
                    memoria["hipoteses"] = []
                # Sincroniza com o local
                os.makedirs(os.path.dirname(MEMORIA_FILE), exist_ok=True)
                with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
                    json.dump(memoria, f, indent=4, ensure_ascii=False)
                logger.info(f"Memória Estratégica carregada do Firebase ({len(memoria.get('hipoteses',[]))} hipóteses).")
                return memoria
        except Exception as e:
            logger.warning(f"Erro ao carregar memória do Firebase: {e}. Usando arquivo local.")

    # Fallback: arquivo local
    if os.path.exists(MEMORIA_FILE):
        try:
            with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Erro ao ler memoria_estrategica.json: {e}")
    return {"hipoteses": [], "conhecimento_consolidado": []}


def _salvar_memoria(memoria):
    """Salva a memória estratégica no arquivo local E no Firebase."""
    # Salva localmente
    os.makedirs(os.path.dirname(MEMORIA_FILE), exist_ok=True)
    with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
        json.dump(memoria, f, indent=4, ensure_ascii=False)

    # Sincroniza com o Firebase
    db = _get_db()
    if db:
        try:
            db.collection("memoria_estrategica").document("hipoteses").set(memoria, merge=True)
            logger.info("Memória Estratégica sincronizada com o Firebase.")
        except Exception as e:
            logger.warning(f"Erro ao sincronizar memória com Firebase: {e}")


def _calcular_confianca(grupo_a_gs, grupo_b_gs, n_a, n_b):
    """
    Calcula a confiança estatística de que o grupo A é superior ao grupo B.
    Usa uma aproximação simples baseada na diferença relativa e no tamanho da amostra.
    Uma implementação mais robusta pode usar teste t de Student no futuro.
    """
    if grupo_a_gs == 0 and grupo_b_gs == 0:
        return 0.0
    if grupo_b_gs == 0:
        return 0.95  # A é infinitamente melhor

    diferenca_relativa = (grupo_a_gs - grupo_b_gs) / max(grupo_b_gs, 0.0001)

    # Fator de confiança baseado no tamanho da amostra (mais amostras = mais confiança)
    # Começa em 0.5 (incerto) e cresce até próximo de 1.0 com muitas amostras
    n_min = min(n_a, n_b)
    fator_amostra = min(n_min / AMOSTRA_MINIMA, 1.0)  # 1.0 quando n >= 30

    # Confiança combinada
    confianca = 0.5 + (diferenca_relativa * 0.3 * fator_amostra)
    return round(max(0.0, min(1.0, confianca)), 3)


def _atualizar_hipoteses_existentes(memoria, dados_posts):
    """
    Reavalia todas as hipóteses em observação com os dados atuais.
    Confirma ou rejeita baseado nos critérios de confiança e amostra mínima.
    """
    posts = dados_posts.get("posts", {})
    atualizacoes = 0

    for hipotese in memoria["hipoteses"]:
        if hipotese["status"] not in ["em_observacao", "planejada"]:
            continue

        var = hipotese.get("variaveis_testadas", [])
        grupo_a_nome = hipotese.get("grupo_a", "")
        grupo_b_nome = hipotese.get("grupo_b", "")
        metrica_alvo = hipotese.get("metrica_alvo", "growth_score")

        gs_a, n_a = 0.0, 0
        gs_b, n_b = 0.0, 0

        for post_id, dados in posts.items():
            info = dados.get("info_post", {})
            mets = dados.get("metricas", {})

            if not var:
                continue

            campo = var[0]
            valor_post = str(info.get(campo, mets.get(campo, "")))

            valor_metrica = mets.get(metrica_alvo, 0)

            if valor_post == grupo_a_nome:
                gs_a += valor_metrica
                n_a += 1
            elif valor_post == grupo_b_nome:
                gs_b += valor_metrica
                n_b += 1

        if n_a == 0 and n_b == 0:
            continue

        media_a = gs_a / n_a if n_a > 0 else 0
        media_b = gs_b / n_b if n_b > 0 else 0

        confianca = _calcular_confianca(media_a, media_b, n_a, n_b)
        amostra = n_a + n_b

        hipotese["confianca"] = confianca
        hipotese["amostra"]   = amostra
        hipotese["media_grupo_a"] = round(media_a, 4)
        hipotese["media_grupo_b"] = round(media_b, 4)
        hipotese["atualizada_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Avalia se pode confirmar ou rejeitar
        diferenca = abs(media_a - media_b) / max(media_b, 0.0001) if media_b > 0 else 0

        if amostra >= AMOSTRA_MINIMA and confianca >= CONFIANCA_CONFIRMACAO:
            if diferenca >= DIFERENCA_MINIMA:
                if media_a > media_b:
                    hipotese["status"] = "confirmada"
                    hipotese["concluida_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    logger.success(f"Hipotese CONFIRMADA: {hipotese['hipotese'][:60]}...")
                else:
                    hipotese["status"] = "rejeitada"
                    hipotese["concluida_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                    logger.info(f"Hipotese rejeitada: {hipotese['hipotese'][:60]}...")
            else:
                hipotese["status"] = "inconclusiva"
                hipotese["concluida_em"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        else:
            hipotese["status"] = "em_observacao"

        atualizacoes += 1

    return atualizacoes


def _formular_novas_hipoteses(memoria, analises_por_periodo):
    """
    Observa os dados e formula novas hipóteses automaticamente.
    Só cria uma hipótese se ela ainda não existir na memória.
    """
    hipoteses_existentes = {h["hipotese"] for h in memoria["hipoteses"]}
    novas = []

    # Obtém dados do ciclo mais recente disponível
    analise_ref = None
    for ciclo in ["semanal", "mensal", "trimestral"]:
        if ciclo in analises_por_periodo and "aviso" not in analises_por_periodo.get(ciclo, {}):
            analise_ref = analises_por_periodo[ciclo]
            break

    if not analise_ref:
        return novas

    # --- Hipótese automática: Categoria de gancho com maior growth_score ---
    ganchos = analise_ref.get("ganchos_stats", {})
    if len(ganchos) >= 2:
        ordenados = sorted(ganchos.items(), key=lambda x: x[1].get("growth_score", 0), reverse=True)
        melhor, pior = ordenados[0], ordenados[-1]
        hipotese_txt = f"Ganchos do tipo '{melhor[0]}' convertem mais seguidores do que '{pior[0]}'."
        if hipotese_txt not in hipoteses_existentes:
            novas.append({
                "id": f"h{uuid.uuid4().hex[:6]}",
                "hipotese": hipotese_txt,
                "variaveis_testadas": ["gancho_categoria"],
                "grupo_a": melhor[0],
                "grupo_b": pior[0],
                "metrica_alvo": "growth_score",
                "confianca": 0.5,
                "amostra": melhor[1].get("count", 0) + pior[1].get("count", 0),
                "status": "em_observacao",
                "criada_em": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

    # --- Hipótese automática: Tipo de CTA com maior growth_score ---
    ctas = analise_ref.get("ctas_stats", {})
    if len(ctas) >= 2:
        ordenados = sorted(ctas.items(), key=lambda x: x[1].get("growth_score", 0), reverse=True)
        melhor, pior = ordenados[0], ordenados[-1]
        hipotese_txt = f"CTA do tipo '{melhor[0]}' gera mais conversão de seguidores do que '{pior[0]}'."
        if hipotese_txt not in hipoteses_existentes:
            novas.append({
                "id": f"h{uuid.uuid4().hex[:6]}",
                "hipotese": hipotese_txt,
                "variaveis_testadas": ["tipo_cta"],
                "grupo_a": melhor[0],
                "grupo_b": pior[0],
                "metrica_alvo": "growth_score",
                "confianca": 0.5,
                "amostra": melhor[1].get("count", 0) + pior[1].get("count", 0),
                "status": "em_observacao",
                "criada_em": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

    # --- Hipótese automática: Tema com maior ICC vs. tema com menor ICC ---
    icc = analise_ref.get("icc_por_tema", {})
    if len(icc) >= 2:
        ordenados = sorted(icc.items(), key=lambda x: x[1], reverse=True)
        melhor, pior = ordenados[0], ordenados[-1]
        hipotese_txt = f"O tema '{melhor[0]}' converte mais curiosos em seguidores (ICC) do que '{pior[0]}'."
        if hipotese_txt not in hipoteses_existentes:
            novas.append({
                "id": f"h{uuid.uuid4().hex[:6]}",
                "hipotese": hipotese_txt,
                "variaveis_testadas": ["tema"],
                "grupo_a": melhor[0],
                "grupo_b": pior[0],
                "metrica_alvo": "conversao_perfil",
                "confianca": 0.5,
                "amostra": 0,
                "status": "em_observacao",
                "criada_em": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            })

    return novas


def obter_hipoteses_confirmadas():
    """Retorna as hipóteses confirmadas para injetar no contexto da IA."""
    memoria = _carregar_memoria()
    return [h for h in memoria["hipoteses"] if h["status"] == "confirmada"]


def rodar_motor(dados_posts, analises_por_periodo=None):
    """Ponto de entrada principal do Motor de Hipóteses."""
    logger.info("Motor de Hipoteses: iniciando ciclo...")
    memoria = _carregar_memoria()

    # 1. Atualiza hipóteses existentes com dados atuais
    atualizacoes = _atualizar_hipoteses_existentes(memoria, dados_posts)

    # 2. Formula novas hipóteses baseadas nos padrões observados
    if analises_por_periodo:
        novas = _formular_novas_hipoteses(memoria, analises_por_periodo)
        if novas:
            memoria["hipoteses"].extend(novas)
            logger.info(f"  {len(novas)} nova(s) hipotese(s) formulada(s).")

    # 3. Salva memória atualizada
    _salvar_memoria(memoria)

    confirmadas = sum(1 for h in memoria["hipoteses"] if h["status"] == "confirmada")
    em_obs = sum(1 for h in memoria["hipoteses"] if h["status"] == "em_observacao")
    logger.success(f"Motor de Hipoteses concluido. Total: {len(memoria['hipoteses'])} | Confirmadas: {confirmadas} | Em observacao: {em_obs}")

    return memoria
