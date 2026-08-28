"""
Módulo de Resposta Automática a Comentários (core/publisher/gerenciador_comentarios.py)

Funcionalidades:
  1. Monitora comentários nos posts/Reels recentes usando a Instagram Graph API.
  2. Filtra comentários que contenham palavras-chave dinâmicas ativadoras de CTA
     (ex: FOCO, SABEDORIA, LIBERDADE, DISCIPLINA, CLAREZA, PAZ, LIVRO, PDF, QUERO).
  3. Responde o comentário publicamente: "Link na bio! Acessa lá 📲"
  4. Registra comentários já respondidos em arquivo local / Firebase para evitar respostas duplicadas.
"""

import os
import sys
import re
import json
import random
import requests
from loguru import logger

# Adiciona a raiz do projeto ao sys.path para garantir execução direta no terminal
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from core.config.settings import IG_ACCESS_TOKEN, IG_ACCOUNT_ID, IG_ACCESS_TOKEN_9, IG_ACCOUNT_ID_9

# Palavras-chave gerais ativas para disparar a resposta
PALAVRAS_CHAVE_PADRAO = [
    "SABEDORIA", "FOCO", "LIBERDADE", "DISCIPLINA", "CLAREZA", "PAZ", "LIVRO", "PDF", "QUERO", "LINK", "EBOOK", "BAIXAR"
]

# Variações de resposta — uma diferente a cada comentário respondido
MENSAGENS_RESPOSTA = [
    "Já te mandei no direct ✨ Espero que faça sentido pra você 🙏",
    "Enviado no direct pra você 📩 Aproveita bem esse material!",
    "Vai chegar no seu direct agora 🙌 Que bom que você pediu!",
    "Te mandei lá no direct 💬 Qualquer dúvida é só falar!",
    "Feito ✅ Chegou no seu direct. Boa leitura e bons insights!",
    "Acabei de te enviar no direct 📖 Espero que abra novas perspectivas!",
    "Pronto, foi pro seu direct 🤝 Esse material pode te surpreender!",
    "Já enviado 📩 Fique de olho no seu direct. Valeu pela interação!",
]


def _sortear_mensagem_resposta() -> str:
    """Retorna uma mensagem de resposta aleatória da lista de variações."""
    return random.choice(MENSAGENS_RESPOSTA)

ARQUIVO_HISTORICO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "midia_temp", "comentarios_respondidos.json"))


def carregar_historico_respondidos() -> set:
    """Carrega IDs de comentários que já foram respondidos anteriormente."""
    if os.path.exists(ARQUIVO_HISTORICO):
        try:
            with open(ARQUIVO_HISTORICO, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception as e:
            logger.warning(f"⚠️ Erro ao carregar histórico de comentários: {e}")
    return set()


def salvar_historico_respondidos(respondidos: set):
    """Salva os IDs de comentários respondidos no histórico local."""
    try:
        os.makedirs(os.path.dirname(ARQUIVO_HISTORICO), exist_ok=True)
        with open(ARQUIVO_HISTORICO, "w", encoding="utf-8") as f:
            json.dump(list(respondidos), f, indent=2)
    except Exception as e:
        logger.warning(f"⚠️ Erro ao salvar histórico de comentários: {e}")


def obter_posts_recentes(limit: int = 5) -> list[dict]:
    """Busca os últimos posts publicados na conta do Instagram."""
    if not IG_ACCESS_TOKEN or not IG_ACCOUNT_ID:
        logger.error("❌ Credenciais do Instagram (IG_ACCESS_TOKEN / IG_ACCOUNT_ID) não configuradas.")
        return []

    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,permalink,timestamp,comments_count",
        "limit": limit,
        "access_token": IG_ACCESS_TOKEN,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            dados = res.json().get("data", [])
            logger.info(f"📸 {len(dados)} posts recentes encontrados para monitoramento de comentários.")
            return dados
        else:
            logger.warning(f"⚠️ Erro ao buscar posts recentes (HTTP {res.status_code}): {res.text[:150]}")
    except Exception as e:
        logger.error(f"❌ Exceção ao buscar posts recentes: {e}")
    return []


def buscar_comentarios_do_post(media_id: str) -> list[dict]:
    """Busca os comentários de um post específico incluindo respostas já existentes."""
    if not IG_ACCESS_TOKEN:
        return []

    url = f"https://graph.facebook.com/v19.0/{media_id}/comments"
    params = {
        "fields": "id,text,username,timestamp,from,replies{id,username}",
        "access_token": IG_ACCESS_TOKEN,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            return res.json().get("data", [])
        else:
            logger.warning(f"⚠️ Erro ao buscar comentários do post {media_id}: {res.text[:120]}")
    except Exception as e:
        logger.error(f"❌ Exceção ao buscar comentários do post {media_id}: {e}")
    return []


def responder_comentario_publico(comment_id: str, mensagem: str | None = None) -> bool:
    """Responde a um comentário publicamente no post com uma mensagem amigável variada."""
    if not IG_ACCESS_TOKEN:
        return False

    mensagem_final = mensagem or _sortear_mensagem_resposta()

    url = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
    params = {
        "message": mensagem_final,
        "access_token": IG_ACCESS_TOKEN,
    }
    try:
        res = requests.post(url, params=params, timeout=15)
        if res.status_code in (200, 201):
            logger.success(f"💬 Comentário {comment_id} respondido: '{mensagem_final}'")
            return True
        else:
            logger.warning(f"⚠️ Erro ao responder comentário (HTTP {res.status_code}): {res.text[:120]}")
    except Exception as e:
        logger.error(f"❌ Exceção ao responder comentário: {e}")
    return False


def _monitorar_conta(token: str, account_id: str, palavras: list, historico: set, limite_posts: int) -> dict:
    """
    Monitora e responde comentários de UMA conta específica.
    Recebe token e account_id para suportar múltiplas contas.
    """
    stats = {"posts_analisados": 0, "comentarios_lidos": 0, "respostas_enviadas": 0}

    if not token or not account_id:
        logger.warning("⚠️ Token ou Account ID não configurados para esta conta. Pulando...")
        return stats

    url = f"https://graph.facebook.com/v19.0/{account_id}/media"
    params = {
        "fields": "id,caption,permalink,timestamp,comments_count",
        "limit": limite_posts,
        "access_token": token,
    }
    try:
        res = requests.get(url, params=params, timeout=15)
        if res.status_code == 200:
            posts = res.json().get("data", [])
        else:
            logger.warning(f"⚠️ Erro ao buscar posts (HTTP {res.status_code}): {res.text[:150]}")
            return stats
    except Exception as e:
        logger.error(f"❌ Exceção ao buscar posts: {e}")
        return stats

    stats["posts_analisados"] = len(posts)
    logger.info(f"📸 {len(posts)} posts encontrados para a conta {account_id}.")

    for post in posts:
        media_id = post.get("id")
        if not media_id:
            continue

        # Busca comentários usando o token da conta correta
        url_c = f"https://graph.facebook.com/v19.0/{media_id}/comments"
        params_c = {
            "fields": "id,text,username,timestamp,from,replies{id,username}",
            "access_token": token,
        }
        try:
            res_c = requests.get(url_c, params=params_c, timeout=15)
            comentarios = res_c.json().get("data", []) if res_c.status_code == 200 else []
        except Exception as e:
            logger.error(f"❌ Erro ao buscar comentários do post {media_id}: {e}")
            comentarios = []

        stats["comentarios_lidos"] += len(comentarios)

        for c in comentarios:
            comment_id = c.get("id")
            if not comment_id or comment_id in historico:
                continue

            replies = c.get("replies", {}).get("data", [])
            if replies:
                historico.add(comment_id)
                continue

            texto_c = c.get("text", "").upper()
            user_info = c.get("from", {})
            username = c.get("username") or user_info.get("username", "usuario_instagram")

            palavra_encontrada = next((p for p in palavras if re.search(r'\b' + re.escape(p) + r'\b', texto_c)), None)

            if palavra_encontrada:
                logger.info(f"🎯 '{palavra_encontrada}' detectada no comentário de @{username} (conta {account_id})!")

                mensagem_variada = _sortear_mensagem_resposta()
                url_r = f"https://graph.facebook.com/v19.0/{comment_id}/replies"
                params_r = {"message": mensagem_variada, "access_token": token}
                try:
                    res_r = requests.post(url_r, params=params_r, timeout=15)
                    if res_r.status_code in (200, 201):
                        logger.success(f"💬 Comentário {comment_id} respondido: '{mensagem_variada}'")
                        historico.add(comment_id)
                        stats["respostas_enviadas"] += 1
                    else:
                        logger.warning(f"⚠️ Erro ao responder (HTTP {res_r.status_code}): {res_r.text[:120]}")
                except Exception as e:
                    logger.error(f"❌ Exceção ao responder comentário: {e}")

    return stats


def monitorar_e_responder_comentarios(palavras_chave: list[str] | None = None, limite_posts: int = 5) -> dict:
    """
    Monitora posts recentes e responde automaticamente nas DUAS contas do Instagram.
    Evita responder duas vezes o mesmo comentário usando um histórico compartilhado.
    """
    base_palavras = list(palavras_chave) if palavras_chave else list(PALAVRAS_CHAVE_PADRAO)
    
    # Tenta carregar a palavra-chave dinâmica do direct a partir do último PDF da semana
    try:
        dir_atual = os.path.dirname(os.path.abspath(__file__))
        caminho_pdf = os.path.abspath(os.path.join(dir_atual, "..", "..", "gerador_pdf", "output", "ultimo_conteudo.json"))
        if os.path.exists(caminho_pdf):
            with open(caminho_pdf, "r", encoding="utf-8") as f:
                dados_pdf = json.load(f)
            titulo_pdf = dados_pdf.get("titulo_pdf", "").lower()
            if titulo_pdf:
                tema_pdf = "sabedoria"
                if any(x in titulo_pdf for x in ["finance", "salário", "dinheiro", "riqueza", "economia", "riquezas", "pobre", "rico"]):
                    tema_pdf = "liberdade"
                elif any(x in titulo_pdf for x in ["hábito", "rotina", "disciplina", "ação", "foco", "atômicos"]):
                    tema_pdf = "foco"
                elif any(x in titulo_pdf for x in ["mente", "cérebro", "psicologia", "pensar", "mental", "pensamento"]):
                    tema_pdf = "clareza"
                elif any(x in titulo_pdf for x in ["relacionamento", "família", "amor", "laços", "pertencimento", "amizade"]):
                    tema_pdf = "lacos"
                
                mapa_palavras = {
                    "liberdade": "MAPA",
                    "foco": "ROTINA",
                    "clareza": "MENTE",
                    "lacos": "CONEXAO",
                    "sabedoria": "SABEDORIA"
                }
                palavra_dinamica = mapa_palavras.get(tema_pdf, "SABEDORIA")
                if palavra_dinamica not in base_palavras:
                    base_palavras.append(palavra_dinamica)
                    logger.info(f"✨ Palavra-chave dinâmica da semana detectada e adicionada: {palavra_dinamica}")
    except Exception as e:
        logger.warning(f"⚠️ Erro leve ao ler último PDF no gerenciador de comentários: {e}")

    palavras = [p.upper() for p in base_palavras]
    logger.info(f"🔎 Iniciando monitoramento nas 2 contas com palavras-chave: {palavras}")

    historico_respondidos = carregar_historico_respondidos()

    # Definição das contas a monitorar
    contas = [
        {"nome": "@gustavo_8k_",          "token": IG_ACCESS_TOKEN,   "id": IG_ACCOUNT_ID},
        {"nome": "@codigo.da.sabedoria_", "token": IG_ACCESS_TOKEN_9, "id": IG_ACCOUNT_ID_9},
    ]

    stats_total = {"posts_analisados": 0, "comentarios_lidos": 0, "respostas_enviadas": 0}

    for conta in contas:
        logger.info(f"\n📲 Monitorando conta: {conta['nome']}")
        s = _monitorar_conta(conta["token"], conta["id"], palavras, historico_respondidos, limite_posts)
        stats_total["posts_analisados"]  += s["posts_analisados"]
        stats_total["comentarios_lidos"] += s["comentarios_lidos"]
        stats_total["respostas_enviadas"] += s["respostas_enviadas"]

    salvar_historico_respondidos(historico_respondidos)
    logger.info(f"📊 Resumo total (2 contas): {stats_total}")
    return stats_total


# ---------------------------------------------------------------------------
# Bloco de execução direta no terminal
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("MONITOR DE COMENTARIOS INSTAGRAM (2 CONTAS)")
    print("=" * 60)
    res = monitorar_e_responder_comentarios(limite_posts=5)
    print(f"\nConcluido! Respostas enviadas no total: {res['respostas_enviadas']}")
