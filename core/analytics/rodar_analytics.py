import os
import sys

# Garante que as importações da pasta analytics funcionem se chamado da raiz
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.coletor import rodar_coleta
from analytics.analisador import analisar_padroes
from analytics.ajustador import gerar_recomendacoes

def principal():
    print("=== INICIANDO SISTEMA DE ANALYTICS E AUTO-AJUSTE ===")
    
    # 1. Coletar
    metricas = rodar_coleta()
    
    # 2. Analisar
    if metricas and "posts" in metricas and len(metricas["posts"]) > 0:
        analise = analisar_padroes(metricas)
        
        # 3. Ajustar
        gerar_recomendacoes(analise)
    else:
        print("Métricas insuficientes para gerar recomendações.")
        
    print("=== PROCESSO DE ANALYTICS CONCLUÍDO ===")

if __name__ == "__main__":
    principal()
