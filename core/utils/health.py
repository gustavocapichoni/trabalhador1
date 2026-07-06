import os
import requests
import shutil
from loguru import logger

def verificar_health():
    """Realiza verificações críticas antes de rodar o bot."""
    logger.info("🩺 Realizando Health Check inicial...")
    
    # 1. Verifica Internet / Graph API
    try:
        requests.get("https://graph.facebook.com", timeout=7)
    except Exception as e:
        logger.error("❌ SEM CONEXÃO COM A INTERNET (ou Graph API do Facebook fora do ar).")
        raise Exception("Health Check Falhou: Sem internet ou API inacessível.")
        
    # 2. Verifica Espaço em Disco (mínimo 1GB para geração de vídeos pesados)
    # Pega o caminho do diretório atual
    caminho = os.getcwd()
    total, used, free = shutil.disk_usage(caminho)
    free_gb = free / (1024 ** 3)
    
    if free_gb < 1.0:
        logger.error(f"❌ ESPAÇO EM DISCO CRÍTICO: {free_gb:.2f} GB livres. Requer pelo menos 1GB para não quebrar a renderização.")
        raise Exception("Health Check Falhou: Espaço em disco insuficiente.")
        
    logger.success("✅ Health Check OK! Conexão e armazenamento validados.")
