import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from core.config.settings import SMTP_EMAIL, SMTP_PASSWORD, NOTIFY_EMAIL

def enviar_email_notificacao(assunto, mensagem, dry_run=False):
    """Envia um e-mail de monitoramento SMTP se configurado."""
    if not SMTP_EMAIL or not SMTP_PASSWORD or not NOTIFY_EMAIL:
        print("⚠️ Configurações de e-mail SMTP incompletas no arquivo .env. Pulando envio de e-mail.")
        return
        
    print(f"📧 Preparando envio de e-mail: '{assunto}'...")
    if dry_run:
        print(f"[DRY-RUN] E-mail simulado para {NOTIFY_EMAIL}:\nAssunto: {assunto}\nMensagem: {mensagem}")
        return
        
    try:
        msg = MIMEText(mensagem, 'plain', 'utf-8')
        msg['Subject'] = Header(assunto, 'utf-8')
        msg['From'] = SMTP_EMAIL
        msg['To'] = NOTIFY_EMAIL

        # Conecta ao servidor SMTP do Gmail usando SSL
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=15)
        server.login(SMTP_EMAIL, SMTP_PASSWORD)
        server.sendmail(SMTP_EMAIL, [NOTIFY_EMAIL], msg.as_string())
        server.quit()
        print("✅ E-mail enviado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao enviar e-mail por SMTP: {e}")


def verificar_expiracao_token():
    """Consulta a API do Facebook para obter o status e expiração do Token."""
    if not IG_ACCESS_TOKEN:
        print("⚠️ IG_ACCESS_TOKEN não configurado no arquivo .env. Pulando checagem de expiração.")
        return None
        
    print("🔑 Verificando status e validade do token de acesso...")
    try:
        url = f"https://graph.facebook.com/debug_token?input_token={IG_ACCESS_TOKEN}&access_token={IG_ACCESS_TOKEN}"
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            data = response.json().get("data", {})
            expires_at = data.get("expires_at")
            is_valid = data.get("is_valid", False)
            
            if not is_valid:
                erro_msg = "🚨 AVISO CRÍTICO: O token de acesso do Instagram é INVÁLIDO ou já expirou!"
                print(erro_msg)
                enviar_email_notificacao("🚨 Erro do Bot - Token Inválido/Expirado", erro_msg)
                raise ValueError(erro_msg)
                
            if expires_at:
                from datetime import datetime, timezone
                exp_date = datetime.fromtimestamp(expires_at, tz=timezone.utc)
                dias_restantes = (exp_date - datetime.now(timezone.utc)).days
                
                info_msg = f"🔑 Validação do Token: O token expira em {exp_date.strftime('%d/%m/%Y %H:%M:%S UTC')} ({dias_restantes} dias restantes)."
                print(info_msg)
                
                if dias_restantes <= 10:
                    alerta_msg = (
                        f"{'⚠️' * 30}\n"
                        f"⚠️ ALERTA DE EXPIRAÇÃO DE CHAVE: Seu token do Instagram expira em breve ({dias_restantes} dias)!\n"
                        f"Por favor, atualize os Repository Secrets no GitHub com o novo token de longa duração do Facebook.\n"
                        f"{'⚠️' * 30}"
                    )
                    print(alerta_msg)
                    enviar_email_notificacao("⚠️ Alerta de Expiração - Token Instagram", alerta_msg)
                return dias_restantes
            else:
                print("🔑 Validação do Token: Token sem expiração definida (provavelmente token perpétuo ou de página).")
                return 999
        else:
            print(f"⚠️ Não foi possível verificar o token. Resposta da API: {response.text}")
    except Exception as e:
        print(f"⚠️ Falha de rede ao consultar status do token na Meta: {e}")
    return None

