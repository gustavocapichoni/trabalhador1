import os
import json
from datetime import datetime, timezone

RECOMENDACOES_FILE = "analytics/dados/recomendacoes.json"

def gerar_recomendacoes_cruzadas(analises_por_periodo):
    """
    Recebe um dicionário com análises de diferentes períodos e gera 
    o contexto de recomendação cruzada.
    Ordem de importância (Macro > Micro): anual > semestral > trimestral > mensal > semanal
    """
    print("Gerando recomendações baseadas no cruzamento de dados...")
    
    contexto = "🎯 CONTEXTO DE PERFORMANCE (MACRO VS MICRO):\n"
    distribuicoes_finais = {
        "temas": {},
        "formatos": {},
        "estilos": {}
    }
    
    # Hierarquia (do Macro pro Micro). O Micro é executado por último, então se ele existir, 
    # as descrições podem dar um sabor atual, mas os PESOS finais vêm de uma combinação.
    # Na verdade, a "sobrescrita" de peso significa que o Macro dita a maior parte do peso.
    # Vamos compor os pesos pegando o Macro disponível.
    
    # Encontra a análise mais "Macro" disponível e a mais "Micro" disponível
    periodos_macro_micro = ["anual", "semestral", "trimestral", "mensal", "semanal"]
    analise_macro = None
    analise_micro = None
    
    for p in periodos_macro_micro:
        if p in analises_por_periodo and "aviso" not in analises_por_periodo[p]:
            if not analise_macro:
                analise_macro = (p, analises_por_periodo[p])
            analise_micro = (p, analises_por_periodo[p]) # Vai atualizando até a última (mais micro)

    if not analise_macro:
        print("Aviso: Nenhuma análise válida encontrada.")
        return None
        
    contexto += f"Sua estratégia fundamental de LONGO PRAZO é ditada pelo panorama {analise_macro[0].upper()}.\n"
    if analise_macro[0] != analise_micro[0]:
        contexto += f"No entanto, sua tática de CURTO PRAZO é ditada pelo panorama {analise_micro[0].upper()}.\n"
        
    # Os pesos reais da "Roleta" vêm do MACRO para garantir a Estratégia
    distribuicoes_finais["temas"] = analise_macro[1].get("distribuicao_temas", {})
    distribuicoes_finais["formatos"] = analise_macro[1].get("distribuicao_formatos", {})
    distribuicoes_finais["estilos"] = analise_macro[1].get("distribuicao_estilos", {})

    contexto += "\n⚖️ DISTRIBUIÇÃO PROPORCIONAL DE TEMAS (ROLETA VICIADA):\n"
    for tema, peso in distribuicoes_finais["temas"].items():
        contexto += f"- {tema}: {peso*100:.1f}%\n"

    contexto += "\nINSTRUÇÃO DE AUTO-AJUSTE: Leve essa distribuição em consideração. Quando for escolher o tema, baseie-se nas proporções acima para manter o mix de conteúdo perfeito, garantindo que o tema macro vencedor domine o grid, mas que outros temas continuem sendo testados."

    recomendacoes = {
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "contexto_para_gemini": contexto,
        "distribuicoes": distribuicoes_finais,
        "analises_raw": analises_por_periodo
    }
    
    os.makedirs(os.path.dirname(RECOMENDACOES_FILE), exist_ok=True)
    with open(RECOMENDACOES_FILE, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)
        
    print("Recomendações cruzadas geradas e salvas com sucesso.")
    return recomendacoes

if __name__ == "__main__":
    pass
