import os
import json
from datetime import datetime, timezone, timedelta

METRICAS_FILE = "analytics/dados/metricas.json"
RECOMENDACOES_SEMANAIS_FILE = "analytics/dados/recomendacoes_semanais.json"

def analisar_semana():
    """
    Analisa os últimos 7 dias de posts e gera recomendações estratégicas profundas.
    Diferente do analisador diário, este olha padrões de tendência, não só o melhor do dia.
    """
    print("=== ANALYTICS SEMANAL: Iniciando análise dos últimos 7 dias ===")

    if not os.path.exists(METRICAS_FILE):
        print("⚠️ Arquivo de métricas não encontrado. Pulando analytics semanal.")
        return

    with open(METRICAS_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)

    posts = dados.get("posts", {})
    if not posts:
        print("⚠️ Sem posts para analisar.")
        return

    # Filtra apenas os posts dos últimos 7 dias
    sete_dias_atras = datetime.now(timezone.utc) - timedelta(days=7)
    posts_semana = {}
    for post_id, dados_post in posts.items():
        data_str = dados_post.get("info_post", {}).get("data", "")
        if data_str:
            try:
                data_post = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                if data_post >= sete_dias_atras:
                    posts_semana[post_id] = dados_post
            except Exception:
                pass

    total = len(posts_semana)
    if total == 0:
        # fallback: usa todos os posts disponíveis
        posts_semana = posts
        total = len(posts_semana)
        print(f"⚠️ Sem posts com data nos últimos 7 dias. Usando todos os {total} posts disponíveis.")
    else:
        print(f"📊 {total} posts encontrados nos últimos 7 dias.")

    # ==========================================
    # AGREGAÇÃO PROFUNDA
    # ==========================================
    temas = {}
    formatos = {}
    estilos = {}
    horarios = {}  # hora do dia → performance
    dias_semana = {} # dia da semana → performance
    total_reach = 0
    total_saves = 0
    total_comments = 0

    for post_id, dados_post in posts_semana.items():
        info = dados_post.get("info_post", {})
        mets = dados_post.get("metricas", {})

        tema = info.get("tema", "desconhecido")
        formato = info.get("tipo", "desconhecido")
        estilo = info.get("estilo_copy", "desconhecido")
        data_str = info.get("data", "")

        likes = mets.get("likes", 0)
        comments = mets.get("comments", 0)
        saved = mets.get("saved", 0)
        shares = mets.get("shares", 0)
        reach = mets.get("reach", mets.get("impressions", 0))

        score = (saved * 3) + (shares * 2) + (comments * 2) + likes + (reach * 0.05)

        total_reach += reach
        total_saves += saved
        total_comments += comments

        for bucket, key in [(temas, tema), (formatos, formato), (estilos, estilo)]:
            if key and key != "desconhecido":
                if key not in bucket:
                    bucket[key] = {"score": 0, "count": 0, "saves": 0, "reach": 0}
                bucket[key]["score"] += score
                bucket[key]["count"] += 1
                bucket[key]["saves"] += saved
                bucket[key]["reach"] += reach

        # Horário e Dia de melhor performance
        if data_str:
            try:
                dt_obj = datetime.fromisoformat(data_str.replace("Z", "+00:00"))
                hora = dt_obj.hour
                dia_idx = dt_obj.weekday() # 0 = Segunda, 6 = Domingo
                
                # Mapeamento para nomes em português
                nomes_dias = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
                dia_nome = nomes_dias[dia_idx]

                if hora not in horarios:
                    horarios[hora] = {"score": 0, "count": 0}
                horarios[hora]["score"] += score
                horarios[hora]["count"] += 1

                if dia_nome not in dias_semana:
                    dias_semana[dia_nome] = {"score": 0, "count": 0}
                dias_semana[dia_nome]["score"] += score
                dias_semana[dia_nome]["count"] += 1
            except Exception:
                pass


    # ==========================================
    # RANKINGS
    # ==========================================
    def ranking(bucket):
        return sorted(
            [(k, v["score"] / v["count"]) for k, v in bucket.items() if v["count"] > 0],
            key=lambda x: x[1], reverse=True
        )

    rank_temas = ranking(temas)
    rank_formatos = ranking(formatos)
    rank_estilos = ranking(estilos)
    rank_horarios = sorted(
        [(h, v["score"] / v["count"]) for h, v in horarios.items() if v["count"] > 0],
        key=lambda x: x[1], reverse=True
    )
    rank_dias = sorted(
        [(d, v["score"] / v["count"]) for d, v in dias_semana.items() if v["count"] > 0],
        key=lambda x: x[1], reverse=True
    )

    melhor_tema = rank_temas[0][0] if rank_temas else None
    pior_tema = rank_temas[-1][0] if len(rank_temas) > 1 else None
    melhor_formato = rank_formatos[0][0] if rank_formatos else None
    melhor_estilo = rank_estilos[0][0] if rank_estilos else None
    melhor_horario = rank_horarios[0][0] if rank_horarios else None
    melhor_dia = rank_dias[0][0] if rank_dias else None

    # ==========================================
    # CONTEXTO ESTRATÉGICO PARA O GEMINI
    # ==========================================
    alcance_medio = int(total_reach / total) if total > 0 else 0
    saves_medio = int(total_saves / total) if total > 0 else 0
    comments_medio = int(total_comments / total) if total > 0 else 0

    contexto = (
        f"ANÁLISE ESTRATÉGICA DA SEMANA ({total} posts analisados):\n"
        f"- Alcance médio: {alcance_medio} contas | Salvamentos médios: {saves_medio} | Comentários médios: {comments_medio}\n"
    )

    if rank_temas:
        top3_temas = ", ".join([f"'{t}'" for t, _ in rank_temas[:3]])
        contexto += f"- Os 3 temas que mais engajaram esta semana: {top3_temas}.\n"

    if pior_tema and pior_tema != melhor_tema:
        contexto += f"- Tema com menor performance: '{pior_tema}' — evite ângulos já usados nele.\n"

    if melhor_formato:
        contexto += f"- Formato com maior retenção de audiência: '{melhor_formato}'.\n"

    if melhor_estilo:
        contexto += f"- Estilo de copy com maior conversão: '{melhor_estilo}' — priorize esta abordagem narrativa.\n"

    if melhor_horario is not None:
        contexto += f"- Horário de pico de engajamento: {melhor_horario}h.\n"

    if melhor_dia is not None:
        contexto += f"- Melhor dia da semana para engajamento: {melhor_dia}.\n"

    contexto += (
        "\nINSTRUÇÃO ESTRATÉGICA: Com base nesses 7 dias de dados reais, "
        "priorize os temas e estilos que estão funcionando. "
        "Inove nos ângulos dos temas de alta performance para evitar repetição. "
        "Evite replicar abordagens dos temas de baixa performance."
    )

    # ==========================================
    # SALVAR RECOMENDAÇÕES
    # ==========================================
    recomendacoes = {
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "periodo_analisado": "7 dias",
        "total_posts_analisados": total,
        "contexto_para_gemini": contexto,
        "tema_recomendado": melhor_tema,
        "pior_tema": pior_tema,
        "formato_recomendado": melhor_formato,
        "estilo_recomendado": melhor_estilo,
        "melhor_horario": melhor_horario,
        "metricas_resumo": {
            "alcance_medio": alcance_medio,
            "saves_medio": saves_medio,
            "comments_medio": comments_medio
        },
        "rankings": {
            "temas": rank_temas,
            "formatos": rank_formatos,
            "estilos": rank_estilos
        }
    }

    os.makedirs(os.path.dirname(RECOMENDACOES_SEMANAIS_FILE), exist_ok=True)
    with open(RECOMENDACOES_SEMANAIS_FILE, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)

    print(f"✅ Recomendações semanais salvas em '{RECOMENDACOES_SEMANAIS_FILE}'")
    print(f"   Melhor tema: {melhor_tema} | Melhor formato: {melhor_formato} | Melhor estilo: {melhor_estilo}")
    print("=== ANALYTICS SEMANAL CONCLUÍDO ===")
    return recomendacoes

if __name__ == "__main__":
    analisar_semana()
