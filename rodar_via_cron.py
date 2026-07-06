import sys
import time
import datetime
import subprocess
import io

# Forçar UTF-8 no Windows para suportar emojis no print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def rodar_agora():
    # Calcula a hora no Brasil (UTC-3)
    utc_now = datetime.datetime.utcnow()
    brt_now = utc_now - datetime.timedelta(hours=3)
    hora = brt_now.hour
    dia_semana = brt_now.weekday()  # 0 = Segunda-feira

    print(f"🕒 Hora atual no Brasil: {brt_now.strftime('%Y-%m-%d %H:%M:%S')} (Dia da semana: {dia_semana})")

    if hora == 4:
        print("🚀 Executando: Analytics Diário")
        subprocess.run(["python", "core/analytics/rodar_analytics.py"])

    elif hora == 6:
        print("🚀 Executando: Reels e Story da Manhã")
        subprocess.run(["python", "main.py", "--type", "reels"])
        time.sleep(10)
        subprocess.run(["python", "main.py", "--type", "story_manha"])

    elif hora == 7:
        if dia_semana == 0:
            print("🚀 Executando: Analytics Semanal")
            subprocess.run(["python", "-c", "import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"])
        print("🚀 Executando: Pexels Story")
        subprocess.run(["python", "main.py", "--type", "pexels_story"])

    elif hora == 8:
        if dia_semana == 0:
            print("🚀 Executando: Relatório Semanal")
            subprocess.run(["python", "core/reports/weekly.py"])

    elif hora == 9:
        print("🚀 Executando: Carousel")
        subprocess.run(["python", "main.py", "--type", "carousel"])

    elif hora == 12:
        print("🚀 Executando: Reels do almoço")
        subprocess.run(["python", "main.py", "--type", "reels"])

    elif hora == 17:
        print("🚀 Executando: Story da Tarde")
        subprocess.run(["python", "main.py", "--type", "story_tarde"])

    elif hora == 18:
        print("🚀 Executando: Reels da noite (narrativo)")
        subprocess.run(["python", "main.py", "--type", "reels_noite"])

    elif hora == 19:
        print("🚀 Executando: Pexels Story da noite (cinematógrafico)")
        subprocess.run(["python", "main.py", "--type", "pexels_story_noite"])

    elif hora == 22:
        print("🚀 Executando: Reels Conquistador (Atração de Público)")
        subprocess.run(["python", "main.py", "--type", "reels_conquistador"])

    else:
        print(f"💤 Nenhuma tarefa agendada para as {hora}:00 BRT.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        tipo = sys.argv[2] if len(sys.argv) > 2 else None
        if tipo == "analytics":
            print("🚀 Executando manualmente: Analytics Diário")
            subprocess.run(["python", "core/analytics/rodar_analytics.py"])
        elif tipo == "weekly_report":
            print("🚀 Executando manualmente: Relatório Semanal")
            subprocess.run(["python", "-c", "import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"])
            subprocess.run(["python", "core/reports/weekly.py"])
        elif tipo:
            print(f"🚀 Executando manualmente: {tipo}")
            subprocess.run(["python", "main.py", "--type", tipo])
        else:
            print("⚠️ Tipo de post não especificado para execução manual.")
    else:
        rodar_agora()
