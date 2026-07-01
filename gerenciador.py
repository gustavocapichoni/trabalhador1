import schedule
import time
import subprocess
import argparse

def run_post(job_type):
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🚀 Iniciando tarefa: {job_type}")
    try:
        subprocess.run(["python", "main.py", "--type", job_type], check=True)
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ✅ Tarefa {job_type} concluída.")
    except subprocess.CalledProcessError as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Erro ao executar {job_type}: o script retornou erro {e.returncode}.")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] ❌ Erro inesperado ao executar {job_type}: {e}")

def run_analytics_semanal():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📊 Iniciando analytics SEMANAL (7 dias de dados)...")
    try:
        subprocess.run(["python", "-c", "from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"], check=True)
    except Exception as e:
        print(f"Erro ao executar analytics semanal: {e}")

def run_report():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📋 Iniciando relatório semanal...")
    try:
        subprocess.run(["python", "core/reports/weekly.py"], check=True)
    except Exception as e:
        print(f"Erro ao executar relatório: {e}")

def run_analytics():
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 📈 Iniciando analytics diário...")
    try:
        subprocess.run(["python", "core/analytics/rodar_analytics.py"], check=True)
    except Exception as e:
        print(f"Erro ao executar analytics: {e}")

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

    print("\n" + "="*60)
    print("🔥 MODO INICIAL: Executando todas as postagens uma vez...")
    print("="*60 + "\n")
    for tipo in SEQUENCIA_INICIAL:
        print(f"\n▶️  Postando: {tipo.upper()}")
        run_post(tipo)
        espera = ESPERA_VIDEO if tipo in ["reels", "pexels_story"] else ESPERA_IMAGEM
        print(f"⏳ Aguardando {espera} segundos antes da próxima postagem...")
        time.sleep(espera)
    print("\n" + "="*60)
    print("✅ Sequência inicial concluída! Entrando no modo automático.")
    print("="*60 + "\n")

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

# ==========================================
# TAREFAS DE MANUTENÇÃO (MADRUGADA/MANHÃ)
# ==========================================
schedule.every().day.at("04:00").do(run_analytics)
# Toda segunda-feira: 07:30 gera a análise da semana inteira, 08:00 manda o relatório
schedule.every().monday.at("07:30").do(run_analytics_semanal)
schedule.every().monday.at("08:00").do(run_report)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gerenciador Autônomo do Bot de Instagram")
    parser.add_argument(
        "--initial-run",
        action="store_true",
        help="Executa todas as postagens uma vez ao iniciar, antes de entrar no modo automático."
    )
    args = parser.parse_args()

    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] 🤖 Gerenciador de postagens autônomo iniciado!")

    if args.initial_run:
        run_inicial()

    print("📅 Entrando no modo automático. Pressione Ctrl+C para parar.")
    print("   Próximas tarefas agendadas:")
    for job in schedule.jobs:
        print(f"   → {job}")

    # Loop infinito que verifica o horário a cada 60 segundos
    while True:
        schedule.run_pending()
        time.sleep(60)

