"""
Script de limpeza da Memória Estratégica no Firebase e nos arquivos locais.
Zera os documentos 'hipoteses' e 'recomendacoes' da coleção 'memoria_estrategica'
e reseta os arquivos JSON locais em 'analytics/dados/'.
NÃO apaga posts, métricas, leads ou qualquer outro dado.
"""
import sys
import os
import json

# Garante que o projeto está no path (caminho de busca do Python)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from loguru import logger

def limpar_memoria_firebase():
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            logger.error("❌ Não foi possível conectar ao Firebase. Verifique as credenciais.")
        else:
            # Estrutura zerada para hipóteses
            memoria_zerada = {
                "hipoteses": [],
                "conhecimento_consolidado": []
            }

            # Zera o documento de hipóteses
            db.collection("memoria_estrategica").document("hipoteses").set(memoria_zerada)
            logger.success("✅ Firebase: 'memoria_estrategica/hipoteses' zerado com sucesso.")

            # Zera o documento de recomendações
            recomendacoes_zeradas = {
                "ranking_temas": [],
                "ranking_ganchos": [],
                "ranking_ctas": [],
                "contexto_para_gemini": "",
                "zerado_em": "Memória zerada para reformulação com nova estrutura de comunicação (ganchos psicológicos)."
            }
            db.collection("memoria_estrategica").document("recomendacoes").set(recomendacoes_zeradas)
            logger.success("✅ Firebase: 'memoria_estrategica/recomendacoes' zerado com sucesso.")

        # --- Limpeza dos arquivos locais em analytics/dados/ ---
        bot_path = os.path.dirname(os.path.abspath(__file__))
        dados_dir = os.path.join(bot_path, "analytics", "dados")

        rec_file = os.path.join(dados_dir, "recomendacoes.json")
        rec_json = {
            "atualizado_em": None,
            "ciclos_utilizados": [],
            "growth_score_referencia": 0.0,
            "icc_por_tema": {},
            "tema_maior_icc": None,
            "peso_final_temas": {},
            "peso_final_formatos": {},
            "peso_final_estilos": {},
            "contexto_para_gemini": ""
        }
        with open(rec_file, "w", encoding="utf-8") as f:
            json.dump(rec_json, f, indent=4, ensure_ascii=False)
        logger.success("✅ Arquivo local 'analytics/dados/recomendacoes.json' zerado com sucesso.")

        mem_file = os.path.join(dados_dir, "memoria_estrategica.json")
        mem_json = {
            "conhecimento_consolidado": [],
            "hipoteses": []
        }
        with open(mem_file, "w", encoding="utf-8") as f:
            json.dump(mem_json, f, indent=4, ensure_ascii=False)
        logger.success("✅ Arquivo local 'analytics/dados/memoria_estrategica.json' zerado com sucesso.")

        rec_sem_file = os.path.join(dados_dir, "recomendacoes_semanais.json")
        if os.path.exists(rec_sem_file):
            rec_sem_json = {
                "atualizado_em": None,
                "contexto_para_gemini": ""
            }
            with open(rec_sem_file, "w", encoding="utf-8") as f:
                json.dump(rec_sem_json, f, indent=4, ensure_ascii=False)
            logger.success("✅ Arquivo local 'analytics/dados/recomendacoes_semanais.json' zerado com sucesso.")

        logger.success("\n🧹 Limpeza completa concluída! O Analytics começará do zero na próxima semana.")
        logger.info("📌 Dados de posts, métricas e leads: INTACTOS.")

    except Exception as e:
        logger.error(f"❌ Erro ao limpar memória estratégica: {e}")

if __name__ == "__main__":
    limpar_memoria_firebase()
