import os
import json
from datetime import datetime, timezone

RECOMENDACOES_FILE = "analytics/dados/recomendacoes.json"

def gerar_recomendacoes(analise):
    print("Gerando recomendações baseadas na análise...")
    
    if "aviso" in analise:
        print("Aviso na análise. Pulando geração de recomendações.")
        return
        
    melhor_tema = analise.get("melhor_tema")
    pior_tema = analise.get("pior_tema")
    melhor_formato = analise.get("melhor_formato")
    melhor_estilo = analise.get("melhor_estilo")
    alcance_medio = int(analise.get("alcance_medio", 0))
    saves_medio = int(analise.get("saves_medio", 0))
    
    contexto = f"CONTEXTO DE PERFORMANCE: Seus últimos posts tiveram alcance médio de {alcance_medio} contas e {saves_medio} salvamentos em média. "
    
    if melhor_tema and pior_tema and melhor_tema != pior_tema:
        contexto += f"Posts sobre o tema '{melhor_tema}' têm performado significativamente melhor que '{pior_tema}'. "
        
    if melhor_formato:
        contexto += f"O formato '{melhor_formato}' é atualmente o que traz mais resultados. "
        
    if melhor_estilo:
        contexto += f"O público está respondendo extremamente bem à abordagem de estilo de copy: '{melhor_estilo}'. "
        
    contexto += "\nINSTRUÇÃO DE AUTO-AJUSTE: Leve essas métricas em consideração. Tente incorporar a energia do formato e tema que estão dando certo, evite abordagens que não estão convertendo. Se for escrever sobre o tema de melhor performance, tente extrair um ângulo inédito."

    recomendacoes = {
        "atualizado_em": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "contexto_para_gemini": contexto,
        "tema_recomendado": melhor_tema,
        "formato_recomendado": melhor_formato,
        "estilo_recomendado": melhor_estilo,
        "metricas_resumo": analise
    }
    
    os.makedirs(os.path.dirname(RECOMENDACOES_FILE), exist_ok=True)
    with open(RECOMENDACOES_FILE, "w", encoding="utf-8") as f:
        json.dump(recomendacoes, f, indent=4, ensure_ascii=False)
        
    print("Recomendações geradas e salvas com sucesso.")
    return recomendacoes

if __name__ == "__main__":
    pass
