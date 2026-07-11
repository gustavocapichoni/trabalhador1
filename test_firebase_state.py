import sys
from loguru import logger
from core.config.state import carregar_estado, salvar_estado

def testar():
    logger.info("Iniciando teste de migração de estado para Firebase...")
    estado = carregar_estado()
    
    if "historico" in estado:
        logger.info(f"Sucesso! Estado carregado. Histórico possui {len(estado['historico'])} posts salvos.")
    else:
        logger.warning("Estado carregado não possui a chave 'historico'. Verifique o dicionário de fallback.")
        
    logger.info("Testando gravação (salvar_estado)...")
    estado["teste_firebase"] = "Teste de conexao concluido com sucesso!"
    salvar_estado(estado)
    logger.info("Fim do teste. Verifique os logs acima para falhas de Firebase.")

if __name__ == "__main__":
    testar()
