import os
import sys
import argparse
from datetime import datetime

# Garante que as importações da pasta analytics funcionem se chamado da raiz
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

from core.analytics.coletor import rodar_coleta, carregar_metricas_local
from core.analytics.analisador import analisar_padroes
from core.analytics.ajustador import gerar_recomendacoes_cruzadas

# Mapeamento de ciclo para janela de dias
JANELA_CICLOS = {
    "semanal":    7,
    "mensal":     30,
    "trimestral": 90,
    "semestral":  180,
    "anual":      365,
}

def apenas_coletar():
    """Fase de ingestão pura: coleta dados da API do Instagram e salva no Firebase.
    Nenhuma recomendação nova é gerada. Roda todo dia às 4h."""
    print("=== [INGESTÃO DIÁRIA] Coletando métricas frescas da API do Instagram ===")
    rodar_coleta()
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
    print("Sincronizando metricas do Firebase...")
    rodar_coleta()
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
    gerar_recomendacoes_cruzadas(analises_por_periodo)

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
        metricas = carregar_metricas_local()
        if metricas and "posts" in metricas and len(metricas["posts"]) > 0:
            analises_por_periodo = {}
            periodos = {"semanal": 7, "mensal": 30, "trimestral": 90, "semestral": 180, "anual": 365}
            for nome, dias in periodos.items():
                resultado = analisar_padroes(metricas, dias_limite=dias)
                if "aviso" not in resultado:
                    analises_por_periodo[nome] = resultado
            gerar_recomendacoes_cruzadas(analises_por_periodo)
        else:
            print("Metricas insuficientes para gerar recomendacoes cruzadas.")
        print("=== PROCESSO DE ANALYTICS CONCLUIDO ===")

if __name__ == "__main__":
    principal()
