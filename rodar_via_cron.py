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
    minuto = brt_now.minute
    dia_semana = brt_now.weekday()  # 0 = Segunda-feira
    dia_mes = brt_now.day
    mes = brt_now.month

    print(f"🕒 Hora atual no Brasil: {brt_now.strftime('%Y-%m-%d %H:%M:%S')} (Dia da semana: {dia_semana})")

    # ─────────────────────────────────────────────────────────────────────────
    # PROTEÇÃO CRÍTICA: o schedule interno do GitHub NUNCA posta conteúdo.
    # Postagens são feitas EXCLUSIVAMENTE pelo cron-job.org via --manual.
    #
    # Usamos JANELAS DE TOLERÂNCIA ao invés de horas fixas:
    #   - Analytics diário (04h BRT): aceita atraso até as 07h59 BRT (3h59 de tolerância)
    #   - Relatório de segunda (08h-08h30 BRT): aceita atraso até as 10h59 BRT
    #   - Qualquer outra hora: nenhuma tarefa de analytics → apenas encerra silenciosamente
    #
    # Isso garante: atraso do GitHub não perde analytics, mas NUNCA aciona postagem.
    # ─────────────────────────────────────────────────────────────────────────

    # ── JANELA 1: Analytics diário (04h BRT, tolerância até 07h59) ──────────
    if 4 <= hora <= 7:
        print(f"📥 [ANALYTICS] Executando coleta diária (hora atual: {hora}h BRT)")
        subprocess.run(["python", "core/analytics/rodar_analytics.py", "--only-collect"])

        # Fechamento semanal e relatório: só no Domingo
        if dia_semana == 6:  # Domingo
            print("🚀 [DOMINGO] Executando: Fechamento Semanal, Relatório")
            subprocess.run(["python", "-c", "import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"])
            subprocess.run(["python", "core/reports/weekly.py"])
            print("🔬 [DOMINGO] Executando: Cientista de Dados + Formulador de Hipóteses")
            subprocess.run(["python", "core/analytics/rodar_analytics.py", "--ciclo", "semanal"])

        # PDF semanal: só Domingo (gerado na janela das 4h-7h, substituindo a lógica das 5h)
        if dia_semana == 6 and hora in (5, 6, 7):
            print("🚀 [DOMINGO] Executando: Geração do PDF da Semana")
            subprocess.run(["python", "gerador_pdf/gerador.py"])

    # ── JANELA 2: Relatórios de segunda-feira (08h BRT, tolerância até 10h59) ──
    elif 8 <= hora <= 10 and dia_semana == 0:  # Segunda-feira
        print(f"📊 [SEGUNDA] Executando relatório semanal (hora atual: {hora}h BRT)")
        # Olhos da Rede (08h00-08h19 ou atrasado mas ainda segunda)
        if hora == 8 and minuto < 20:
            print("🚀 [SEGUNDA] Executando: Olhos da Rede Semanal")
            subprocess.run(["python", "-c", "import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); from core.ai.olhos_da_rede import coletar_e_salvar_semanal; coletar_e_salvar_semanal()"])
        else:
            # 08h20+ ou atrasado para 9h/10h: roda o Analisador (evita perder o relatório)
            print("🧠 [SEGUNDA] Executando: Analisador Semanal + IA Estrategista")
            subprocess.run(["python", "core/analytics/rodar_analytics.py", "--ciclo", "semanal"])

    # ── QUALQUER OUTRA HORA: encerra silenciosamente (sem postagem) ──────────
    else:
        print(f"💤 [SCHEDULE] Hora {hora}h BRT — nenhuma tarefa de analytics neste horário. Encerrando.")

    # ── Sempre: verifica solicitações pendentes do Studio de Criação ─────────
    # Roda a cada ciclo do schedule para não deixar nenhuma solicitação esperando
    try:
        print("📥 Verificando solicitações pendentes do Studio de Criação (Dashboard)...")
        subprocess.run(["python", "core/publisher/executor_usuario.py"])
    except Exception as e_req:
        print(f"⚠️ Aviso no processador do Studio de Criação: {e_req}")

    # ── Sempre: monitor de comentários ───────────────────────────────────────
    try:
        print("💬 Executando verificação e resposta automática de comentários...")
        subprocess.run(["python", "core/publisher/gerenciador_comentarios.py"])
    except Exception as e_comm:
        print(f"⚠️ Aviso no monitor de comentários: {e_comm}")



if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--manual":
        tipo = sys.argv[2] if len(sys.argv) > 2 else None
        if tipo == "comentarios":
            print("🚀 Executando manualmente: Monitor de Comentários")
            subprocess.run(["python", "core/publisher/gerenciador_comentarios.py"])
        elif tipo == "analytics":
            print("🚀 Executando manualmente: Analytics Diário")
            subprocess.run(["python", "core/analytics/rodar_analytics.py"])
        elif tipo == "weekly_report":
            print("Executando manualmente: Relatorio Semanal")
            subprocess.run(["python", "core/analytics/rodar_analytics.py", "--ciclo", "semanal"])
            subprocess.run(["python", "-c", "import sys, io; sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8'); from core.analytics.analisador_semanal import analisar_semana; analisar_semana()"])
            subprocess.run(["python", "core/reports/weekly.py"])
        elif tipo in ("mensal", "trimestral", "semestral", "anual"):
            print(f"Executando manualmente: Relatorio {tipo.upper()}")
            subprocess.run(["python", "core/reports/periodic.py", tipo])
        elif tipo == "gerador_pdf":
            print("🚀 Executando manualmente: Gerador de PDF Semanal")
            subprocess.run(["python", "gerador_pdf/gerador.py"])
        elif tipo == "user_requests":
            print("🚀 Executando manualmente: Processador do Studio de Criação")
            subprocess.run(["python", "core/publisher/executor_usuario.py"])
        elif tipo:
            print(f"Executando manualmente: {tipo}")
            subprocess.run(["python", "main.py", "--type", tipo])
        else:
            print("Tipo de post nao especificado para execucao manual.")
    else:
        rodar_agora()
