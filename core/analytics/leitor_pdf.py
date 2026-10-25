import json
import os
from loguru import logger

def ler_resumo_ultimo_pdf():
    """
    Lê o ultimo_conteudo.json gerado pelo gerador_pdf e retorna um resumo conciso
    contendo o título, as dores e a solução abordadas no PDF.
    Isso serve de base para a criação do roteiro magnético reels_leads.
    """
    # Caminho do arquivo ultimo_conteudo.json na raiz do projeto
    bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    caminho_arquivo = os.path.join(bot_path, "gerador_pdf", "output", "ultimo_conteudo.json")
    
    if not os.path.exists(caminho_arquivo):
        logger.warning(f"⚠️ Arquivo não encontrado: {caminho_arquivo}")
        return None
        
    try:
        with open(caminho_arquivo, "r", encoding="utf-8") as f:
            dados = json.load(f)
            
        titulo = dados.get("titulo_pdf", "Material Exclusivo")
        subtitulo = dados.get("subtitulo_pdf", "")
        
        # Puxa a dor principal (geralmente detalhada nos primeiros parágrafos do capítulo 1 ou 2)
        capitulos = dados.get("capitulos", [])
        dor_principal = ""
        if capitulos and len(capitulos) > 0:
            for cap in capitulos[:2]: # Olha os 2 primeiros capítulos
                if "paragrafos" in cap and len(cap["paragrafos"]) > 1:
                    dor_principal += cap["paragrafos"][1] + " "
                
        # Puxa o resumo do método/solução (Plano de Ação)
        plano = dados.get("plano_acao", {})
        solucao = plano.get("subtitulo", "")
        if "passos" in plano and len(plano["passos"]) > 0:
            solucao += " | Passos principais: " + ", ".join([p.get("titulo", "") for p in plano["passos"][:3]])
        
        resumo = f"TÍTULO DO PDF: {titulo}\n"
        resumo += f"SUBTÍTULO: {subtitulo}\n"
        
        if dor_principal:
            # Limita o tamanho para não estourar muito o prompt
            dor_str = dor_principal.strip()[:600]
            resumo += f"DOR/PROBLEMA ABORDADO NO PDF: {dor_str}...\n"
            
        if solucao:
            resumo += f"SOLUÇÃO/MÉTODO DO PDF: {solucao}\n"
            
        logger.info(f"📄 Resumo do último PDF carregado com sucesso: '{titulo}'")
        return resumo
        
    except Exception as e:
        logger.error(f"❌ Erro ao ler ultimo_conteudo.json: {e}")
        return None
