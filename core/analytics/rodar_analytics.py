import os
import sys
import argparse
from datetime import datetime, timedelta
import io

# Forçar UTF-8 no Windows para suportar emojis no print
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except AttributeError:
    pass

# Garante que as importações da pasta analytics funcionem se chamado da raiz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from core.analytics.coletor import rodar_coleta, carregar_metricas_local
from core.analytics.analisador import analisar_padroes
from core.analytics.ajustador import gerar_recomendacoes_cruzadas
from core.analytics.coletor_youtube import rodar_coleta_youtube, carregar_metricas_local as carregar_metricas_youtube_local

# Mapeamento de ciclo para janela de dias
JANELA_CICLOS = {
    "semanal":    7,
    "mensal":     30,
    "trimestral": 90,
    "semestral":  180,
    "anual":      365,
}

def enviar_email_coleta_diaria(metricas):
    """Gera um e-mail resumo com as métricas diárias coletadas e envia."""
    try:
        from core.publisher.email_notifier import enviar_email_notificacao
    except Exception as e:
        print(f"⚠️ Não foi possível importar enviar_email_notificacao: {e}")
        return

    if not metricas or "posts" not in metricas:
        print("⚠️ Sem métricas válidas para enviar por e-mail.")
        return

    agora = datetime.now()
    data_str = agora.strftime("%d/%m/%Y às %H:%M")

    # 1. Dados da Conta
    dados_conta = metricas.get("conta", {})
    reach_30d = dados_conta.get("reach_30d", 0)
    views_30d = dados_conta.get("impressions_30d", 0)
    profile_views_30d = dados_conta.get("profile_views_30d", 0)
    followers_30d = dados_conta.get("follower_count_30d", 0)

    linhas = []
    linhas.append("📊 BOT INSTAGRAM: RELATÓRIO DE COLETA DIÁRIA 📊")
    linhas.append("=" * 50)
    linhas.append(f"Data da Coleta: {data_str} (BRT)")
    linhas.append("=" * 50)
    linhas.append("")
    linhas.append("📈 DESEMPENHO DA CONTA (ÚLTIMOS 30 DIAS)")
    linhas.append("-" * 40)
    linhas.append(f"  • Alcance (Reach):           {reach_30d:,}")
    linhas.append(f"  • Visualizações/Impressões:  {views_30d:,}")
    linhas.append(f"  • Visitas ao Perfil:         {profile_views_30d:,}")
    linhas.append(f"  • Novos Seguidores:          {followers_30d:,}")
    linhas.append("")

    # 2. Resumo de Posts
    posts = metricas.get("posts", {})
    posts_ordenados = []
    for pid, info in posts.items():
        info_post = info.get("info_post", {})
        data_post_str = info_post.get("data", "")
        try:
            dt = datetime.strptime(data_post_str, "%Y-%m-%d %H:%M:%S")
            posts_ordenados.append((dt, pid, info))
        except:
            continue

    posts_ordenados.sort(key=lambda x: x[0], reverse=True)

    linhas.append("📝 ÚLTIMAS PUBLICAÇÕES ATUALIZADAS")
    linhas.append("-" * 40)

    if posts_ordenados:
        # Pega as 5 mais recentes
        for dt, pid, info in posts_ordenados[:5]:
            info_post = info.get("info_post", {})
            mets = info.get("metricas", {})
            tipo = info_post.get("tipo", "feed").upper()
            tema = info_post.get("tema", "Desconhecido")
            likes = mets.get("likes", 0)
            comments = mets.get("comments", 0)
            views = mets.get("views", mets.get("plays", mets.get("impressions", 0)))
            growth = mets.get("growth_score", 0.0)

            linhas.append(f"  • [{dt.strftime('%d/%m %H:%M')}] {tipo} - Tema: {tema}")
            linhas.append(f"    Views: {views:,} | Curtidas: {likes} | Comentários: {comments}")
            linhas.append(f"    Growth Score: {growth}")
            if mets.get("permalink"):
                linhas.append(f"    Link: {mets.get('permalink')}")
            linhas.append("")
    else:
        linhas.append("  Nenhum post recente encontrado na base de dados.")
        linhas.append("")

    linhas.append("=" * 50)
    linhas.append("Bot automático de postagens Instagram - Monitoramento Ativo")

    corpo_email = "\n".join(linhas)

    try:
        enviar_email_notificacao(
            assunto="📊 Relatório Diário de Coleta - Instagram Bot",
            mensagem=corpo_email
        )
        print("✅ E-mail de coleta diária enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao disparar o e-mail de coleta: {e}")

def apenas_coletar():
    """Fase de ingestão pura: coleta dados da API do Instagram e YouTube e salva no Firebase.
    Nenhuma recomendação nova é gerada. Roda todo dia às 4h."""
    print("=== [INGESTÃO DIÁRIA] Coletando métricas frescas da API do Instagram ===")
    metricas = rodar_coleta()
    print("=== [INGESTÃO DIÁRIA] Coletando métricas frescas da API do YouTube ===")
    try:
        rodar_coleta_youtube()
    except Exception as e:
        print(f"⚠️ Coleta YouTube com erro (não crítico): {e}")
    
    # Envia e-mail de notificação diária
    enviar_email_coleta_diaria(metricas)
    print("=== [INGESTÃO DIÁRIA] Coleta finalizada. Nenhuma recomendação foi alterada. ===")

def rodar_ciclo(ciclo):
    """Fase de análise: lê o histórico acumulado no Firebase e gera/atualiza as recomendações
    ponderadas por todos os ciclos disponíveis (Semanal -> Anual)."""
    ciclo = ciclo.lower()
    if ciclo not in JANELA_CICLOS:
        print(f"Ciclo invalido: '{ciclo}'. Use: {list(JANELA_CICLOS.keys())}")
        sys.exit(1)

    print(f"=== [ANALYTICS] Iniciando ciclo {ciclo.upper()} ===")

    # 1. Garante que os dados do Firebase estao sincronizados localmente
    print("Sincronizando metricas do Firebase (Instagram + YouTube)...")
    rodar_coleta()
    try:
        rodar_coleta_youtube()
    except Exception as e:
        print(f"⚠️ Coleta YouTube com erro (não crítico): {e}")
    metricas = carregar_metricas_local()

    if not metricas or "posts" not in metricas or len(metricas["posts"]) == 0:
        print("Metricas insuficientes para gerar recomendacoes. Encerrando.")
        return

    # 2. Analisa todos os ciclos disponíveis (do menor ao maior)
    analises_por_periodo = {}
    for nome, dias in JANELA_CICLOS.items():
        resultado = analisar_padroes(metricas, dias_limite=dias)
        if "aviso" not in resultado:
            analises_por_periodo[nome] = resultado
            print(f"  Ciclo {nome.upper()} analisado: {resultado.get('total_posts_analisados', 0)} posts")
        else:
            print(f"  Ciclo {nome.upper()} ignorado: dados insuficientes ({resultado.get('aviso')})")

    if not analises_por_periodo:
        print("Nenhum ciclo pôde ser analisado. Aguardando mais dados.")
        return

    # 3. Gera recomendacoes cruzadas ponderadas por todos os ciclos disponíveis
    recs = gerar_recomendacoes_cruzadas(analises_por_periodo)
    try:
        from core.analytics.db import get_db
        db = get_db()
        if db:
            db.collection("memoria_estrategica").document("recomendacoes").set(recs, merge=True)
            print("Recomendacoes salvas no Firebase Firestore.")
    except Exception as e:
        print(f"Erro ao salvar recomendacoes no Firebase: {e}")

    # 4. Roda o Motor de Hipóteses para formular/atualizar hipóteses estratégicas
    try:
        from core.analytics.motor_hipoteses import rodar_motor
        rodar_motor(metricas, analises_por_periodo=analises_por_periodo)
        print("Motor de Hipoteses atualizado.")
    except ImportError:
        pass  # Motor ainda nao instalado (Fase 5)
    except Exception as e:
        print(f"Motor de Hipoteses com erro (nao critico): {e}")

    print(f"=== [ANALYTICS] Ciclo {ciclo.upper()} concluido. ===")

def principal():
    parser = argparse.ArgumentParser(description="Sistema de Analytics do Bot Instagram")
    parser.add_argument(
        "--only-collect",
        action="store_true",
        help="Apenas coleta dados da API do Instagram e grava no Firebase. Nao gera recomendacoes."
    )
    parser.add_argument(
        "--ciclo",
        choices=list(JANELA_CICLOS.keys()),
        default=None,
        help="Executa o pipeline analitico completo para o ciclo especificado."
    )
    args = parser.parse_args()

    if args.only_collect:
        apenas_coletar()
    elif args.ciclo:
        rodar_ciclo(args.ciclo)
    else:
        # Comportamento legado: coleta + análise completa (mantida para compatibilidade)
        print("=== INICIANDO SISTEMA DE ANALYTICS CRUZADO E AUTO-AJUSTE ===")
        rodar_coleta()
        try:
            rodar_coleta_youtube()
        except Exception as e:
            print(f"⚠️ Coleta YouTube com erro (não crítico): {e}")
        metricas = carregar_metricas_local()
        
        # Envia e-mail de notificação diária
        enviar_email_coleta_diaria(metricas)

        if metricas and "posts" in metricas and len(metricas["posts"]) > 0:
            analises_por_periodo = {}
            periodos = {"semanal": 7, "mensal": 30, "trimestral": 90, "semestral": 180, "anual": 365}
            for nome, dias in periodos.items():
                resultado = analisar_padroes(metricas, dias_limite=dias)
                if "aviso" not in resultado:
                    analises_por_periodo[nome] = resultado
            recs = gerar_recomendacoes_cruzadas(analises_por_periodo)
            try:
                from core.analytics.db import get_db
                db = get_db()
                if db:
                    db.collection("memoria_estrategica").document("recomendacoes").set(recs, merge=True)
                    print("Recomendacoes salvas no Firebase Firestore.")
            except Exception as e:
                print(f"Erro ao salvar recomendacoes no Firebase: {e}")
        else:
            print("Metricas insuficientes para gerar recomendacoes cruzadas.")
        print("=== PROCESSO DE ANALYTICS CONCLUIDO ===")

if __name__ == "__main__":
    principal()
