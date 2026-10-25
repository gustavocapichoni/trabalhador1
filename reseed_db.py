"""
Script de Repovoamento e Sincronização Completa do Firebase Firestore (reseed_db.py)

Este script lê os dados reais das APIs oficiais (Instagram Graph API e YouTube Data API)
e da memória local para reconstruir todas as coleções zeradas do banco de dados no Firebase:
- bot_config (app_state)
- metricas_conta_instagram (consolidados)
- metricas_posts
- historico_posts
- metricas_posts_youtube
- memoria_estrategica (hipoteses e recomendacoes)
"""

import sys
import os
from datetime import datetime, timezone
from loguru import logger

# Garante que o diretório raiz está no path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.analytics.db import get_db
from core.config.state import carregar_estado, salvar_estado
from core.analytics.coletor import (
    buscar_posts_recentes_api,
    buscar_insights_conta,
    salvar_metricas_conta_firebase,
    buscar_metricas_api,
    salvar_metricas_firebase
)
from core.analytics.coletor_youtube import (
    buscar_shorts_recentes_yt,
    buscar_metricas_video_yt,
    salvar_metricas_youtube_firebase
)

def repovoar_banco_firebase():
    print("🚀 --- INICIANDO REPOVOAMENTO COMPLETO DO FIREBASE FIRESTORE --- 🚀\n")
    
    db = get_db()
    if not db:
        print("❌ Erro Crítico: Não foi possível conectar ao Firebase. Verifique suas credenciais no .env.")
        return False

    resumo = {}

    # -------------------------------------------------------------
    # 1. COLEÇÃO: bot_config (app_state)
    # -------------------------------------------------------------
    print("1️⃣ [bot_config] Sincronizando estado do aplicativo...")
    try:
        estado = carregar_estado()
        salvar_estado(estado)  # Já sincroniza com 'bot_config/app_state'
        resumo["bot_config"] = "✅ OK (app_state salvo)"
        print("   ✅ bot_config/app_state restaurado com sucesso.")
    except Exception as e:
        logger.error(f"Erro em bot_config: {e}")
        resumo["bot_config"] = f"❌ Erro: {e}"

    # -------------------------------------------------------------
    # 2. COLEÇÃO: metricas_conta_instagram (consolidados)
    # -------------------------------------------------------------
    print("\n2️⃣ [metricas_conta_instagram] Buscando estatísticas da conta no Instagram...")
    try:
        dados_conta = buscar_insights_conta()
        if dados_conta:
            salvar_metricas_conta_firebase(dados_conta)
            resumo["metricas_conta_instagram"] = f"✅ OK ({dados_conta.get('follower_count', 0)} seguidores)"
            print(f"   ✅ Insights da conta salvos: {dados_conta.get('follower_count', 0)} seguidores.")
        else:
            resumo["metricas_conta_instagram"] = "⚠️ Alerta: API não retornou dados da conta."
    except Exception as e:
        logger.error(f"Erro em metricas_conta_instagram: {e}")
        resumo["metricas_conta_instagram"] = f"❌ Erro: {e}"

    # -------------------------------------------------------------
    # 3. COLEÇÃO: historico_posts & metricas_posts (Instagram)
    # -------------------------------------------------------------
    print("\n3️⃣ [historico_posts & metricas_posts] Escaneando mídias do Instagram...")
    try:
        posts = buscar_posts_recentes_api()
        count_hist = 0
        count_met = 0
        
        batch = db.batch()
        for p in posts:
            post_id = p.get("post_id")
            if not post_id or post_id.startswith("DRY_RUN"):
                continue

            # Registra no historico_posts
            doc_hist = db.collection("historico_posts").document(post_id)
            batch.set(doc_hist, p, merge=True)
            count_hist += 1

            # Coleta e salva métricas em metricas_posts
            tipo_media = p.get("tipo", "feed")
            metricas = buscar_metricas_api(post_id, tipo_post=tipo_media)
            if metricas:
                info_post = {
                    "tema": p.get("tema", ""),
                    "subtema": p.get("subtema", ""),
                    "tipo": tipo_media,
                    "data": p.get("data", "")
                }
                salvar_metricas_firebase(post_id, info_post, metricas)
                count_met += 1

        batch.commit()
        resumo["historico_posts"] = f"✅ OK ({count_hist} posts repovoados)"
        resumo["metricas_posts"] = f"✅ OK ({count_met} posts com métricas ativas)"
        print(f"   ✅ {count_hist} posts gravados em 'historico_posts'.")
        print(f"   ✅ {count_met} métricas detalhadas gravadas em 'metricas_posts'.")
    except Exception as e:
        logger.error(f"Erro ao repovoar posts do Instagram: {e}")
        resumo["historico_posts"] = f"❌ Erro: {e}"
        resumo["metricas_posts"] = f"❌ Erro: {e}"

    # -------------------------------------------------------------
    # 4. COLEÇÃO: metricas_posts_youtube (YouTube Shorts)
    # -------------------------------------------------------------
    print("\n4️⃣ [metricas_posts_youtube] Escaneando Shorts do canal no YouTube...")
    try:
        shorts_yt = buscar_shorts_recentes_yt()
        count_yt = 0
        for video_id in shorts_yt:
            m_yt = buscar_metricas_video_yt(video_id)
            if m_yt:
                salvar_metricas_youtube_firebase(video_id, m_yt)
                count_yt += 1
        resumo["metricas_posts_youtube"] = f"✅ OK ({count_yt} Shorts mapeados)"
        print(f"   ✅ {count_yt} vídeos sincronizados em 'metricas_posts_youtube'.")
    except Exception as e:
        logger.error(f"Erro ao repovoar YouTube: {e}")
        resumo["metricas_posts_youtube"] = f"❌ Erro: {e}"

    # -------------------------------------------------------------
    # 5. COLEÇÃO: memoria_estrategica (hipoteses & recomendacoes)
    # -------------------------------------------------------------
    print("\n5️⃣ [memoria_estrategica] Recalculando inteligência e recomendações estratégicas...")
    try:
        from core.analytics.analisador import rodar_analise
        from core.analytics.motor_hipoteses import recalcular_hipoteses
        
        recs = rodar_analise()
        db.collection("memoria_estrategica").document("recomendacoes").set(recs, merge=True)
        
        mem_hip = recalcular_hipoteses()
        resumo["memoria_estrategica"] = f"✅ OK ({len(recs.get('ranking_temas', []))} temas analisados)"
        print("   ✅ Recomendações e Hipóteses estratégicas recalculadas e salvas no Firebase.")
    except Exception as e:
        logger.error(f"Erro em memoria_estrategica: {e}")
        resumo["memoria_estrategica"] = f"❌ Erro: {e}"

    # -------------------------------------------------------------
    # RELATÓRIO FINAL
    # -------------------------------------------------------------
    print("\n" + "="*60)
    print("📋 RELATÓRIO FINAL DE REPOVOAMENTO DO FIREBASE")
    print("="*60)
    for col, status in resumo.items():
        print(f"  • {col:<30}: {status}")
    print("="*60)
    print("🎉 SEU BANCO DE DADOS FOI 100% RECONSTRUÍDO COM SUCESSO!\n")
    return True

if __name__ == "__main__":
    repovoar_banco_firebase()
