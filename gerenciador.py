import schedule
import time
import subprocess
import argparse
import sys
from loguru import logger

# ============================================================
# CONFIGURAÇÃO GLOBAL DE LOGS
# Escreve no terminal E em arquivo com rotação diária
# ============================================================
logger.remove()  # Remove o handler padrão
logger.add(sys.stdout, colorize=True, format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}")
logger.add(
    "bot_diario.log",
    rotation="00:00",       # Rotaciona a cada meia-noite (cria um arquivo novo por dia)
    retention="30 days",    # Guarda os últimos 30 dias de logs
    compression="zip",      # Comprime os logs antigos
    format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {message}",
    encoding="utf-8"
)

def run_post(job_type):
    logger.info(f"🚀 Iniciando tarefa: {job_type}")
    try:
        subprocess.run(["python", "main.py", "--type", job_type], check=True)
        logger.success(f"✅ Tarefa {job_type} concluída.")
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Erro ao executar {job_type}: o script retornou erro {e.returncode}.")
    except Exception as e:
        logger.error(f"❌ Erro inesperado ao executar {job_type}: {e}")

def run_analytics_semanal():
    logger.info("📊 Iniciando analytics SEMANAL (7 dias de dados)...")
    try:
        subprocess.run(["python", "-c", "from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"], check=True)
    except Exception as e:
        logger.error(f"Erro ao executar analytics semanal: {e}")

def run_report():
    logger.info("📋 Iniciando relatório semanal...")
    try:
        subprocess.run(["python", "core/reports/weekly.py"], check=True)
    except Exception as e:
        logger.error(f"Erro ao executar relatório: {e}")

def run_coleta_diaria():
    logger.info("📥 Iniciando coleta de métricas diária (sem análise)...")
    try:
        subprocess.run(["python", "-c", "from core.analytics.coletor import rodar_coleta; rodar_coleta()"], check=True)
    except Exception as e:
        logger.error(f"Erro ao executar coleta: {e}")

def run_cruzamento_dados():
    logger.info("📈 Iniciando Cruzamento de Dados (Macro vs Micro)...")
    try:
        subprocess.run(["python", "core/analytics/rodar_analytics.py"], check=True)
    except Exception as e:
        logger.error(f"Erro ao cruzar dados: {e}")

def run_token_check():
    """Verifica diáriamente a validade do token do Instagram e notifica por e-mail se perto de expirar."""
    logger.info("🔑 Verificando validade do token do Instagram...")
    try:
        from core.publisher.email_notifier import verificar_expiracao_token
        dias_restantes = verificar_expiracao_token()
        if dias_restantes is not None and dias_restantes != 999:
            logger.info(f"🔑 Token válido. {dias_restantes} dias restantes até a expiração.")
            if dias_restantes <= 10:
                logger.warning(f"⚠️ ALERTA: Token expira em {dias_restantes} dias! Renove o token no GitHub Secrets.")
        elif dias_restantes == 999:
            logger.info("🔑 Token sem data de expiração definida (token de página permanente).")
    except Exception as e:
        logger.error(f"❌ Erro ao verificar token: {e}")

def run_inicial():
    """
    Executa TODAS as postagens uma vez ao iniciar o bot, em sequência.
    Útil para testar se tudo está funcionando antes de entrar no modo automático.
    """
    SEQUENCIA_INICIAL = [
        "reels",        # 06:00 - Reels matinal
        "story_manha",  # 06:05 - Stories da manhã
        "pexels_story", # 07:00 - B-roll manhã
        "carousel",     # 09:00 - Carrossel
        "reels",        # 12:00 - Reels do almoço
        "story_tarde",  # 17:00 - Stories da tarde
        "reels",        # 18:00 - Reels da noite
        "pexels_story", # 19:00 - B-roll noite
    ]
    # Tipos de vídeo demoram mais para renderizar (MoviePy)
    ESPERA_VIDEO = 120  # 2 minutos para reels e pexels_story
    ESPERA_IMAGEM = 60  # 1 minuto para stories e carrossel

    logger.info("\n" + "="*60)
    logger.info("🔥 MODO INICIAL: Executando todas as postagens uma vez...")
    logger.info("="*60 + "\n")
    for tipo in SEQUENCIA_INICIAL:
        logger.info(f"\n▶️  Postando: {tipo.upper()}")
        run_post(tipo)
        espera = ESPERA_VIDEO if tipo in ["reels", "pexels_story"] else ESPERA_IMAGEM
        logger.info(f"⏳ Aguardando {espera} segundos antes da próxima postagem...")
        time.sleep(espera)
    logger.success("\n✅ Sequência inicial concluída! Entrando no modo automático.")

# ==========================================
# CRONOGRAMA DE POSTAGENS
# ==========================================
schedule.every().day.at("06:00").do(run_post, "reels")
schedule.every().day.at("06:05").do(run_post, "story_manha")
schedule.every().day.at("07:00").do(run_post, "pexels_story")
schedule.every().day.at("09:00").do(run_post, "carousel")
schedule.every().day.at("12:00").do(run_post, "reels")
schedule.every().day.at("17:00").do(run_post, "story_tarde")
schedule.every().day.at("18:00").do(run_post, "reels")
schedule.every().day.at("19:00").do(run_post, "pexels_story") # B-roll sem narração no horário da noite
schedule.every().day.at("22:00").do(run_post, "reels_conquistador") # Conquistador de Público (VSL)

# ==========================================
# TAREFAS DE MANUTENÇÃO (MADRUGADA/MANHÃ)
# ==========================================
# 04:00 - Apenas COLETA as métricas (não toma decisões)
schedule.every().day.at("04:00").do(run_coleta_diaria)

# Toda segunda-feira: 04:30 cruza os dados, 07:30 gera a análise da semana inteira, 08:00 manda o relatório
schedule.every().monday.at("04:30").do(run_cruzamento_dados)
schedule.every().monday.at("07:30").do(run_analytics_semanal)
schedule.every().monday.at("08:00").do(run_report)

# Verificação diária do token do Instagram (07:00) — avisa por e-mail se perto de expirar
schedule.every().day.at("07:00").do(run_token_check)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerenciador Autônomo do Bot de Instagram")
    parser.add_argument(
        "--initial-run",
        action="store_true",
        help="Executa todas as postagens uma vez ao iniciar, antes de entrar no modo automático."
    )
    args = parser.parse_args()

    logger.info("🤖 Gerenciador de postagens autônomo iniciado!")

    if args.initial_run:
        run_inicial()

    logger.info("📅 Entrando no modo automático. Pressione Ctrl+C para parar.")
    logger.info("   Próximas tarefas agendadas:")
    for job in schedule.jobs:
        logger.info(f"   → {job}")

    # Loop infinito que verifica o horário a cada 60 segundos
    while True:
        schedule.run_pending()
        time.sleep(60)

