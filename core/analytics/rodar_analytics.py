import os
import sys

# Garante que as importações da pasta analytics funcionem se chamado da raiz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from core.analytics.coletor import rodar_coleta, carregar_metricas_local
from core.analytics.analisador import analisar_padroes
from core.analytics.ajustador import gerar_recomendacoes_cruzadas

def principal():
    print("=== INICIANDO SISTEMA DE ANALYTICS CRUZADO E AUTO-AJUSTE ===")
    
    # 1. Coleta e Carrega os Dados
    metricas = carregar_metricas_local()
    
    # 2. Analisar por Períodos
    if metricas and "posts" in metricas and len(metricas["posts"]) > 0:
        analises_por_periodo = {}
        
        # Mapeia nome do período para dias
        periodos = {
            "semanal": 7,
            "mensal": 30,
            "trimestral": 90,
            "semestral": 180,
            "anual": 365
        }
        
        for nome, dias in periodos.items():
            resultado = analisar_padroes(metricas, dias_limite=dias)
            if "aviso" not in resultado:
                analises_por_periodo[nome] = resultado
        
        # 3. Cruzamento e Ajuste
        gerar_recomendacoes_cruzadas(analises_por_periodo)
    else:
        print("Métricas insuficientes para gerar recomendações cruzadas.")
        
    print("=== PROCESSO DE ANALYTICS CONCLUÍDO ===")

if __name__ == "__main__":
    principal()
