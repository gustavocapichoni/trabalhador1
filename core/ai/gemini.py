import json
import random
import time
import os
from google import genai
from datetime import datetime, timezone

from core.config.settings import GEMINI_KEYS, GROQ_KEYS, OPENROUTER_KEY
from core.ai.prompts import FONTES_SABEDORIA, montar_instrucoes_copy
from core.ai.styles import sortear_estilo
from core.ai.olhos_da_rede import gerar_contexto_mundo_real
from core.config.state import carregar_estado, salvar_estado
from core.analytics.leitor_pdf import ler_resumo_ultimo_pdf
from loguru import logger


def buscar_historico_por_tema(tema, tipo_post=None, limite=8):
    """
    Busca os últimos posts do mesmo TEMA no historico_posts do Firebase.
    Filtra e ordena NO PYTHON para evitar dependência de índices compostos
    do Firebase que geram erros 400 silenciosos e deixam a IA rodar cega.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return ""

        # Busca apenas pelo tema (índice simples — nunca gera erro 400)
        docs = db.collection("historico_posts") \
                 .where("tema", "==", tema) \
                 .limit(40).stream()
        todos = [doc.to_dict() for doc in docs]

        # Filtra por tipo no Python, sem depender do Firebase
        if tipo_post:
            todos = [p for p in todos if p.get("tipo") == tipo_post]

        # Ordena do mais recente ao mais antigo no Python
        todos.sort(key=lambda x: x.get("data", ""), reverse=True)
        posts_anteriores = todos[:limite]

        if not posts_anteriores:
            return ""

        msg = "\n        PROIBIDO REPETIR (HISTÓRICO DO TEMA):\n"
        msg += f"        O tema de hoje é '{tema}'. Veja abaixo o que já foi publicado nesse tema recentemente.\n"
        msg += "        Você DEVE criar algo completamente diferente — novas frases, novas metáforas, novos ângulos:\n"
        for i, p in enumerate(posts_anteriores):
            frase = p.get("frase_visual") or ""
            # frase_visual pode ser lista (slides) ou string
            if isinstance(frase, list):
                frase = " | ".join(str(s) for s in frase[:3])
            legenda_trecho = (p.get("legenda") or "")[:120]
            data = p.get("data", "")[:10]
            tipo_reg = p.get("tipo", "")
            if frase or legenda_trecho:
                msg += f"        * Post {i+1} ({data}) [{tipo_reg}]: Frase='{str(frase)[:150]}' | Legenda='{legenda_trecho}...'\n"
        msg += "        Qualquer semelhança com os textos acima é inaceitável. Seja 100% original.\n"
        return msg

    except Exception as e:
        logger.warning(f"Erro ao buscar histórico por tema '{tema}': {e}")
        return ""

def buscar_historico_reels_leads(limite=6):
    """
    Busca os últimos reels_leads gerados em 'historico_reels_leads' no Firebase.
    Ordena NO PYTHON para evitar o erro 400 de índice composto do Firebase.
    Retorna string de contexto para a IA não repetir os mesmos ganchos e frases.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return ""
        # Busca sem order_by para não precisar de índice composto no Firebase
        docs = db.collection("historico_reels_leads").limit(30).stream()
        posts = [doc.to_dict() for doc in docs]
        # Ordena do mais recente ao mais antigo no Python
        posts.sort(key=lambda x: x.get("data", ""), reverse=True)
        posts = posts[:limite]
        if not posts:
            return ""
        msg = "\n        PROIBIDO REPETIR (HISTÓRICO DOS ÚLTIMOS REELS DE LEADS):\n"
        msg += "        Estes são os roteiros de captação já publicados. Crie algo 100% diferente em gancho, ângulo e frases de encerramento/CTA:\n"
        for i, p in enumerate(posts):
            titulo = p.get("titulo_pdf", "")
            gancho = (p.get("gancho_fase1") or "")[:120]
            cta_fechamento = (p.get("cta_final") or "")[:120]
            data = p.get("data", "")[:10]
            msg += f"        * Reels {i+1} ({data}): PDF='{titulo}' | Gancho='{gancho}' | Convite Final Usado='{cta_fechamento}'\n"
        msg += "        Qualquer semelhança com os ganchos ou frases finais acima é inaceitável. Seja 100% original em todo o roteiro.\n"
        return msg
    except Exception as e:
        logger.warning(f"Erro ao buscar histórico de reels_leads: {e}")
        return ""


def _pos_processar_dados(dados, tipo, tema_escolhido, detalhes_tema, gancho_categoria="", tipo_cta="", duracao_video=0, subtema="", tom_emocional=""):
    """
    Funcao auxiliar para centralizar o pos-processamento dos dados gerados (IA ou Contingencia).
    Injeta as hashtags correspondentes na legenda e os metadados de analytics no dicionario.
    """
    # (Hashtags foram removidas da legenda a pedido do usuário)
    # Metadados internos para o sistema de analytics (prefixo _ indica uso interno)
    dados["_gancho_categoria"] = gancho_categoria
    dados["_tipo_cta"]         = tipo_cta
    dados["_duracao_video"]    = duracao_video
    dados["_subtema"]          = subtema
    dados["_tom_emocional"]    = tom_emocional

    # ── Injeção de CTAs Padronizados e Robustos ──
    if "slides" in dados and isinstance(dados["slides"], list):
        slides_val = list(dados["slides"])
        if tipo in ["story_tarde", "pexels_story", "pexels_story_noite", "reels", "reels_noite"]:
            while len(slides_val) < 3:
                slides_val.append("...")
            if len(slides_val) > 3:
                slides_val = slides_val[:3]

            if tipo == "story_tarde":
                titulo_pdf = "Material da Semana"
                try:
                    bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
                    caminho_pdf = os.path.join(bot_path, "gerador_pdf", "output", "ultimo_conteudo.json")
                    if os.path.exists(caminho_pdf):
                        with open(caminho_pdf, "r", encoding="utf-8") as f:
                            dados_pdf = json.load(f)
                        titulo_pdf = dados_pdf.get("titulo_pdf", "Material da Semana")
                except Exception as e:
                    logger.warning(f"Erro ao carregar PDF no pos-processamento: {e}")

                ctas_ebook = [
                    f"Se você acompanha o perfil, adquire o ebook\\n'{titulo_pdf}' atualizado da semana.\\nDigite SABEDORIA e receba no direct.",
                    f"O ebook '{titulo_pdf}' da semana\\njá está disponível. Pegue o seu, é gratuito.\\nDigite SABEDORIA no direct.",
                    f"Se você quer crescer e desenvolver\\nconhecimento prático, digite SABEDORIA\\nque eu te envio no direct."
                ]
                slides_val[2] = random.choice(ctas_ebook)

            elif tipo in ["pexels_story", "pexels_story_noite", "reels", "reels_noite"]:
                ctas_follow = [
                    "Siga o perfil para não perder os próximos.\\nAtive as notificações.",
                    "Quem chegou até aqui já está à frente.\\nSiga para continuar crescendo.",
                    "Acompanhe o perfil para a próxima reflexão.\\nAtive o sininho.",
                    "Salva esse vídeo para não esquecer.\\nSiga para mais sabedoria diária."
                ]
                slides_val[2] = random.choice(ctas_follow)
            dados["slides"] = slides_val

    # ── Truncador de segurança para imagens estáticas ──
    # A IA às vezes gera frases muito longas ignorando o limite pedido no prompt.
    # Para posts de imagem única (story), limitamos a 20 palavras
    # para garantir que o texto caiba no layout sem sobrepor o emblema ou a marca d'água.
    if tipo == "story" and "frase" in dados:
        frase_val = dados["frase"]
        if isinstance(frase_val, str):
            # Remove quebras de linha que a IA pode gerar
            frase_limpa = frase_val.replace("\n", " ").replace("\r", " ").strip()
            palavras = frase_limpa.split()
            if len(palavras) > 20:
                logger.warning(f"⚠️ [IA] Frase do {tipo} com {len(palavras)} palavras. AVISO: Ultrapassou o limite recomendado de 20.")
            dados["frase"] = frase_limpa

    # ── Truncador + normalizador para slides do story_tarde ──
    # O story_tarde usa o campo 'slides' (lista), não 'frase'.
    # Limita cada slide a 18 palavras e converte '\\n' literal (escape do JSON)
    # para '\n' real (quebra de linha Python), garantindo que o CTA seja
    # dividido em dois blocos visuais (topo e baixo) e que 'SABEDORIA' fique dourada.
    if tipo == "story_tarde" and "slides" in dados:
        slides_val = dados["slides"]
        if isinstance(slides_val, list):
            slides_normalizados = []
            ultimo_idx = len(slides_val) - 1
            penultimo_idx = ultimo_idx - 1
            for idx, s in enumerate(slides_val):
                # Converte \\n literal → \n real (vem assim do JSON do Gemini)
                s_norm = str(s).replace("\\n", "\n").strip()
                # NUNCA trunca o último slide (CTA) nem o penúltimo (Título PDF)
                if idx >= penultimo_idx:
                    slides_normalizados.append(s_norm)
                    continue
                palavras = s_norm.replace("\n", " ").split()
                if len(palavras) > 10:
                    logger.warning(f"⚠️ [IA] Slide do story_tarde com {len(palavras)} palavras. AVISO: Ultrapassou o limite de 10 palavras.")
                slides_normalizados.append(s_norm)
            dados["slides"] = slides_normalizados

    # ── Truncador + normalizador para slides do reels_leads ──
    # Limita cada slide de corpo (não o CTA nem o Título PDF) a 15 palavras máximas.
    if tipo == "reels_leads" and "slides" in dados:
        slides_val = dados["slides"]
        if isinstance(slides_val, list):
            slides_normalizados = []
            ultimo_idx = len(slides_val) - 1
            penultimo_idx = ultimo_idx - 1
            for idx, s in enumerate(slides_val):
                s_norm = str(s).replace("\\n", "\n").strip()
                # NUNCA trunca o último slide (CTA) nem o penúltimo (Título PDF)
                if idx >= penultimo_idx:
                    slides_normalizados.append(s_norm)
                    continue
                palavras = s_norm.replace("\n", " ").split()
                if len(palavras) > 10:
                    logger.warning(f"⚠️ [IA] Slide do reels_leads com {len(palavras)} palavras. AVISO: Ultrapassou o limite de 10 palavras.")
                slides_normalizados.append(s_norm)
            dados["slides"] = slides_normalizados

    return dados

def gerar_conteudo_gemini(tipo, custom_tema=None, custom_mensagem=None):
    # Calcula número de slides para stories de forma alternada a cada dia (2 em um dia, 3 no outro)
    dia_ano = datetime.now(timezone.utc).timetuple().tm_yday
    num_slides_story = 2 if dia_ano % 2 == 0 else 3

    if tipo == "test":
        logger.info("Gerando conteudo de teste estatico...")
        prompt_visual = "A serene sunset reflecting on a calm lake, warm golden hour, realistic photograph"
        logger.info(f"Cena cinematografica (test): {prompt_visual}")
        return {
            "frase": "Seja forte e corajoso. Nao se apavore nem desanime, pois o Senhor, o seu Deus, estara com voce por onde voce andar.",
            "legenda": "Ambiente de automacao inicializado com sucesso no GitHub Actions!\n\nEste e um teste integrado disparado pelo bot para validar as permissoes e notificacoes do sistema.\n\n#bot #instagram #automacao #dev",
            "prompt_imagem": prompt_visual
        }, "espiritualidade", "teste"
        
    logger.info(f"🤖 Solicitando texto ao Gemini para post do tipo: {tipo.upper()}...")
    if not GEMINI_KEYS and not GROQ_KEYS and not OPENROUTER_KEY:
        raise ValueError("Nenhuma chave de API (Gemini, Groq ou OpenRouter) está configurada! Por favor, adicione-as ao arquivo .env ou Secrets.")
        
    # --- INTEGRAÇÃO COM ANALYTICS CRUZADO (ROLETA VICIADA) E CONQUISTADOR ---
    estado = carregar_estado()
    tema_escolhido = custom_tema
    contexto_analytics = ""
    evitar_repeticao_msg = ""
    
    agora = datetime.now(timezone.utc)
    dia_hoje_str = agora.strftime("%Y-%m-%d")

    is_conquistador = (tipo == "reels_conquistador")
    
    if is_conquistador and not custom_tema:
        # Loop Cego: Ignora o Analytics e roda pelos 8 temas em sequência
        temas_lista = [f["nome"] for f in FONTES_SABEDORIA]
        idx = estado.get("index_conquistador", 0)
        if idx >= len(temas_lista): idx = 0
            
        tema_escolhido = temas_lista[idx]
        
        # Avança pro próximo dia
        estado["index_conquistador"] = (idx + 1) % len(temas_lista)
        salvar_estado(estado)
        logger.info(f"🎯 [CONQUISTADOR] Tema forçado pelo ciclo: {tema_escolhido}")

        # Busca histórico DESTE TEMA para evitar repetição de mensagens no Conquistador
        evitar_repeticao_msg = buscar_historico_por_tema(tema_escolhido, tipo_post="reels_conquistador", limite=6)
    elif not custom_tema:
        # Se for o primeiro post do dia, rotaciona o tema sequencialmente
        if estado.get("data_tema_do_dia") == dia_hoje_str and estado.get("tema_do_dia"):
            tema_escolhido = estado["tema_do_dia"]
            logger.info(f"🎲 Tema do dia continuado: {tema_escolhido}")
        else:
            temas_lista = [f["nome"] for f in FONTES_SABEDORIA]
            idx = estado.get("index_tema_diario", 0)
            if idx >= len(temas_lista): idx = 0
            
            tema_escolhido = temas_lista[idx]
            
            estado["tema_do_dia"] = tema_escolhido
            estado["data_tema_do_dia"] = dia_hoje_str
            estado["index_tema_diario"] = (idx + 1) % len(temas_lista)
            salvar_estado(estado)
            logger.info(f"🎲 Novo tema sequencial diário ativado: {tema_escolhido}")

    if not custom_tema:
        # Busca histórico deste TEMA em TODOS os formatos (anti-repetição unificada)
        # Isso evita que uma ideia publicada em vídeo apareça como carrossel no mesmo dia
        evitar_repeticao_msg = buscar_historico_por_tema(tema_escolhido, tipo_post=None, limite=10)
        if evitar_repeticao_msg:
            logger.info(f"📚 Histórico unificado do tema '{tema_escolhido}' carregado (todos os formatos).")

        # NOVO FLUXO: Lê diretamente o contexto mestre gerado pela IA Estrategista
        recomendacoes_file = "analytics/dados/recomendacoes.json"
        
        try:
            if os.path.exists(recomendacoes_file):
                with open(recomendacoes_file, "r", encoding="utf-8") as f:
                    rec_cruzada = json.load(f)
                
                # Monta um super contexto com toda a inteligência gerada pela IA estrategista
                contexto_analytics += "=== DIRETRIZES ESTRATÉGICAS DA SEMANA (IA) ===\n"
                
                if rec_cruzada.get("vibe_da_semana"):
                    contexto_analytics += f"VIBE DA SEMANA: {rec_cruzada['vibe_da_semana']}\n\n"
                
                if rec_cruzada.get("padroes_campeoes"):
                    contexto_analytics += f"PADRÕES QUE BOMBARAM (Replique isso): {rec_cruzada['padroes_campeoes']}\n\n"
                
                if rec_cruzada.get("ganchos_exclusivos"):
                    ganchos_str = "\n  - ".join(rec_cruzada["ganchos_exclusivos"])
                    contexto_analytics += f"GANCHOS INÉDITOS SUGERIDOS:\n  - {ganchos_str}\n\n"
                
                if rec_cruzada.get("ideias_de_narrativa"):
                    narrativas_str = "\n  - ".join(rec_cruzada["ideias_de_narrativa"])
                    contexto_analytics += f"IDEIAS DE NARRATIVA PARA EXPLORAR:\n  - {narrativas_str}\n\n"
                
                if rec_cruzada.get("aviso_estrategico"):
                    contexto_analytics += f"AVISO URGENTE DA IA ESTRATEGISTA: {rec_cruzada['aviso_estrategico']}\n\n"
                
                # Também adiciona o resumo clássico (fallback matemático / resumo final)
                contexto_analytics += f"RESUMO DO CONTEXTO: {rec_cruzada.get('contexto_para_gemini', '')}\n\n"
                
                logger.info("✅ Super Contexto estratégico (IA) injetado no prompt.")
                
                try:
                    from core.utils.contexto import registrar_contexto
                    registrar_contexto("analytics_ativo", True)
                    registrar_contexto("analytics_vibe", rec_cruzada.get("vibe_da_semana", ""))
                    registrar_contexto("analytics_padroes", rec_cruzada.get("padroes_campeoes", ""))
                except Exception as ctx_err:
                    logger.debug(f"Erro ao registrar contexto analytics: {ctx_err}")
        except Exception as e:
            logger.warning(f"Erro ao ler contexto estratégico (recomendacoes.json): {e}")

    # Sorteia sentimento a cada postagem — sem travar por data
    # Assim cada publicação do dia carrega uma cor emocional diferente
    sentimento_escolhido = None
    if not is_conquistador:
        from core.ai.styles import SENTIMENTOS_CONFIG
        hist_sentimentos = estado.get("historico_sentimentos", [])
        # Filtra sentimentos ainda não usados recentemente
        opcoes_sentimentos = [s for s in SENTIMENTOS_CONFIG.keys() if s not in hist_sentimentos]
        if not opcoes_sentimentos:  # Todos já foram usados: reseta e recomeça
            hist_sentimentos = []
            opcoes_sentimentos = list(SENTIMENTOS_CONFIG.keys())
        sentimento_escolhido = random.choice(opcoes_sentimentos)
        hist_sentimentos.append(sentimento_escolhido)
        estado["historico_sentimentos"] = hist_sentimentos[-10:]  # Guarda os últimos 10
        estado["sentimento_do_dia"] = sentimento_escolhido  # Mantém compatível com rest of code
        salvar_estado(estado)
        logger.info(f"🧠 Sentimento da postagem: {sentimento_escolhido.upper()} (varia a cada post)")
        
    detalhes_tema = {"nome": tema_escolhido}
    logger.info(f"✨ Tema que guiará o bot hoje: {detalhes_tema['nome']}")
    
    # ---------------- CICLO SEQUENCIAL DE GANCHOS E CTAs ----------------
    hist_angulos = estado.get("historico_angulos", [])
    hist_estilos = estado.get("historico_estilos", [])

    # Índices sequenciais: avançam 1 por postagem
    indice_gancho             = estado.get("indice_gancho", 0)
    indice_gancho_conquistador = estado.get("indice_gancho_conquistador", 0)
    indice_cta                = estado.get("indice_cta", 0)
    indice_arquitetura        = estado.get("indice_arquitetura", 0)

    # Seleciona o índice correto de gancho conforme o modo da postagem
    idx_atual = indice_gancho_conquistador if is_conquistador else indice_gancho

    # Monta instrucoes de copy (gancho sequencial + cta sequencial + arquitetura narrativa + ângulo anti-repetição)
    instrucoes_copy, sub_angulo, gancho, descricao_categoria, categoria_gancho, novo_indice, categoria_cta, referencia_cta, novo_indice_cta, arquitetura, novo_indice_arquitetura = montar_instrucoes_copy(
        contexto_analytics=contexto_analytics,
        historico_fontes=hist_angulos,
        indice_gancho=idx_atual,
        indice_cta=indice_cta,
        indice_arquitetura=indice_arquitetura,
        is_conquistador=is_conquistador,
        sentimento_escolhido=sentimento_escolhido
    )

    # Injeta o histórico do tema no instrucoes_copy → propagado automaticamente para TODOS os tipos de post
    if evitar_repeticao_msg:
        instrucoes_copy += evitar_repeticao_msg

    if custom_mensagem:
        instrucoes_copy += f"\n\n====================\nMENSAGEM E CONCEITO OBRIGATÓRIO SOLICITADO PELO USUÁRIO NO DASHBOARD:\n\"{custom_mensagem}\"\nVocê DEVE obrigatoriamente construir a postagem com base nesta mensagem/ideia do usuário.\n====================\n"
        logger.info(f"💬 [Studio de Criação] Mensagem do usuário injetada no prompt: {custom_mensagem[:60]}...")

    # Estilo de abordagem sorteado (com anti-repetição)
    estilo_escolhido = sortear_estilo(hist_estilos)
    logger.info(f"🎭 Estilo de abordagem sorteado: {estilo_escolhido.split(':')[0].upper()}")
    logger.info(f"🎣 Mecanismo Psicológico: {categoria_gancho.upper()} | Slide 1: \"{gancho}\"")
    logger.info(f"📐 Arquitetura narrativa: {arquitetura['nome']}")
    
    try:
        from core.utils.contexto import registrar_contexto
        registrar_contexto("sub_angulo", sub_angulo)
        registrar_contexto("gancho_abertura", gancho)
        registrar_contexto("arquitetura_nome", arquitetura.get('nome', ''))
        registrar_contexto("sentimento_post", sentimento_escolhido or "")
        registrar_contexto("estilo_escolhido", estilo_escolhido.split(':')[0].strip() if estilo_escolhido else "")
    except Exception as ctx_err:
        logger.debug(f"Erro ao registrar contexto estratégico: {ctx_err}")

    # Atualiza histórico de ângulos e estilos (mantém os últimos 25)
    hist_angulos.append(sub_angulo)
    hist_estilos.append(estilo_escolhido)

    estado["historico_angulos"] = hist_angulos[-25:]
    estado["historico_estilos"] = hist_estilos[-25:]

    # Avança o índice do gancho no estado (separado por modo)
    if is_conquistador:
        estado["indice_gancho_conquistador"] = novo_indice
    else:
        estado["indice_gancho"] = novo_indice

    # Define se esta postagem consome e avança o índice de CTA e Arquitetura
    tipos_com_cta = ["carousel", "reels", "reels_conquistador", "pexels_story", "reels_noite", "pexels_story_noite"]
    if tipo in tipos_com_cta:
        estado["indice_cta"] = novo_indice_cta
        estado["indice_arquitetura"] = novo_indice_arquitetura
        logger.info(f"📣 CTA sequencial #{indice_cta}: [{categoria_cta.upper()}] -> '{referencia_cta}'")

    salvar_estado(estado)
    # --------------------------------------------------------------------

    # Instruções de livros já estão embutidas na Sabedoria Viva.
    instrucoes_livros = ""


    if tipo == "story":
        prompt = f"""
        Você cria Stories de Instagram direcionados estritamente para pessoas que JÁ TE SEGUEM (audiência quente).
        Sua comunicação deve ser uma CONVERSA ÍNTIMA, EXCLUSIVA, PROPOSITAL E DIRECIONAL.
        Estilo obrigatório para este story: {estilo_escolhido}

        CONTEXTO DO DIA (use como bússola de valor — não copie literalmente):
        - Tema do dia: {detalhes_tema['nome']}
        - Ângulo de inspiração: "{sub_angulo}"
        - Tom emocional do dia: {sentimento_escolhido.upper() if sentimento_escolhido else 'REFLEXÃO'}

        DIRETRIZ DE ESCRITA E PERCEPÇÃO DE VALOR:
        - Fale de igual para igual, como um mentor compartilhando uma percepção pessoal profunda do seu dia a dia.
        - O story deve parecer um pensamento que normalmente só surge depois de muita experiência observando pessoas e a própria vida.
        - Escreva como alguém que fala pouco, mas quando fala muda a forma como o leitor enxerga uma situação.
        - Evite frases prontas ou conselhos de autoajuda vazios. O objetivo deixa de ser "motivação" e passa a ser "lucidez".
        - Escreva uma única frase curta e com altíssimo impacto emocional (entre 10 e 15 palavras) que gere uma pequena mudança de perspectiva.
        - NÃO use "..." de forma automática — use no máximo 1 vez por sequência, somente quando criar tensão real.
        - NÃO use ponto de exclamação. Use ponto final ou interrogação.
        - NÃO inclua CTA, convite para seguir ou qualquer chamada para ação.
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": "Sua frase de conversa íntima com seu seguidor aqui"
        }}
        """
    elif tipo == "story_manha":
        prompt = f"""
        Você cria uma sequência de Stories de Instagram matinais de alta autoridade para sua audiência.
        Sua missão é entregar uma PÍLULA DE SABEDORIA MATINAL em pequena dose: clara, elevada, inspiradora e sem nenhum tom carrancudo ou pesado.
        Estilo obrigatório para esta sequência: {estilo_escolhido}

        CONTEXTO DO DIA (use como bússola de valor — não copie literalmente):
        - Tema do dia: {detalhes_tema['nome']}
        - Ângulo de inspiração: "{sub_angulo}"
        - Tom emocional do dia: {sentimento_escolhido.upper() if sentimento_escolhido else 'REFLEXÃO'}

        CRIE UMA SEQUÊNCIA DE EXATAMENTE {num_slides_story} FRASES CONECTADAS (ENTRE 10 E 15 PALAVRAS POR FRASE):
        - SLIDE 1 (GANCHO MATINAL VISCERAL): Frase curta e cortante que rompe o piloto automático do leitor ao acordar (10 a 15 palavras). Baseada em um princípio bíblico, estoico ou psicológico prático — nunca clichê.
        - SLIDES INTERMEDIÁRIOS (ENSINAMENTO PRÁTICO SÓLIDO): Entregue um princípio de sabedoria ou comportamento com aplicação IMEDIATA no dia do leitor. Deve gerar o impulso de salvar o story ou enviar para alguém.
        - SLIDE FINAL (DIREÇÃO FIRME): Feche com uma sentença de autoridade que oriente claramente o leitor para o que fazer ou como pensar neste dia.
        - PROIBIDO: Tom pesado, vitimista, poético sem aplicação prática, ou autoajuda vazia.
        - NÃO inclua CTA, convite para seguir ou qualquer chamada para ação.
        - Não use ponto de exclamação.
        - Escolha se quer usar música de fundo ou não no story (true ou false) de acordo com o tom.
        
        PERCEPÇÃO DE VALOR DO STORY MATINAL:
        - O seguidor deve sentir que recebeu um insight que valeu a pena acordar e ver. Não motivação vazia — sabedoria aplicável.
        - A autoridade do story deve vir exclusivamente da profundidade do raciocínio prático.
        
        Responda APENAS em formato JSON válido assim (o array 'frase' DEVE ter EXATAMENTE {num_slides_story} itens):
        {{
          "frase": [
            "Slide 1 (Gancho matinal visceral - 10 a 15 palavras)",
            "Slide 2 (Princípio prático de sabedoria - 10 a 15 palavras)",
            "Slide {num_slides_story} (Direção firme para o dia - 10 a 15 palavras)"
          ],
          "usar_musica": true
        }}
        """
    elif tipo == "story_tarde":
        resumo_pdf_tarde = ler_resumo_ultimo_pdf() or "Nenhum PDF encontrado. Construa o roteiro com base nos princípios filosóficos e de crescimento pessoal."
        titulo_pdf_tarde = "Material da Semana"
        bot_path_tarde = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        caminho_pdf_tarde = os.path.join(bot_path_tarde, "gerador_pdf", "output", "ultimo_conteudo.json")
        if os.path.exists(caminho_pdf_tarde):
            try:
                import json as _json
                with open(caminho_pdf_tarde, "r", encoding="utf-8") as _f:
                    _dados_pdf_tarde = _json.load(_f)
                titulo_pdf_tarde = _dados_pdf_tarde.get("titulo_pdf", "Material da Semana")
            except Exception as _e:
                logger.warning(f"Erro ao carregar PDF para story_tarde: {_e}")

        SINONIMOS_MODULO = ["guia", "material", "conteúdo", "edição", "acervo", "manual", "recurso", "kit"]
        sinonimo_modulo = random.choice(SINONIMOS_MODULO)

        VARIACOES_CTA_TARDE = [
            f"Se você ainda não garantiu o seu desta semana, comenta 'SABEDORIA' que te mando no Direct. \\n Baixe o seu {sinonimo_modulo} de evolução prática.",
            f"Essa semana o {sinonimo_modulo} já está disponível. É só comentar 'SABEDORIA' para receber. \\n Tenha o direcionamento certo no bolso.",
            f"Conhecimento de valor se aplica. Comenta 'SABEDORIA' e pega a edição desta semana. \\n Comece hoje seu avanço pessoal.",
            f"Já liberamos a nova edição semanal. Comenta 'SABEDORIA' que te envio o link direto. \\n Receba o material completo no seu Direct.",
            f"Se você quer aprofundar no tema de hoje, comenta 'SABEDORIA' no Direct. \\n Pega o seu {sinonimo_modulo} inédito agora.",
            f"Toda semana um {sinonimo_modulo} novo pra quem busca maestria. Comenta 'SABEDORIA'. \\n O material completo já está no seu Direct.",
            f"Não deixa pra depois: comenta 'SABEDORIA' e recebe o link imediatamente. \\n Seu guia de lucidez da semana.",
            f"O material desta semana tá pronto. Comenta 'SABEDORIA' que te entrego no Direct. \\n Receba o passo a passo de aplicação.",
            f"Quem te acompanha sabe do valor disso. Comenta 'SABEDORIA' e pega seu {sinonimo_modulo}. \\n Acesse o conteúdo completo no Direct.",
            f"Se ainda não pegou seu {sinonimo_modulo} semanal, comenta 'SABEDORIA' agora mesmo. \\n O mapa da semana no seu bolso.",
        ]
        cta_tarde = random.choice(VARIACOES_CTA_TARDE)
        cta_do_dia = "SABEDORIA"

        prompt = f"""
        Você é um estrategista de conversão, especialista em comportamento humano e copywriting de alta performance.
        Sua função é criar uma sequência de STORIES em vídeo para AUDIÊNCIA QUENTE — pessoas que JÁ SEGUEM o perfil @codigo.da.sabedoria_.
        Elas te conhecem. Confiam em você. Mas ainda não pediram o PDF desta semana.
        Seu trabalho é criar a mensagem que vai fazer elas reconhecerem que precisam desse material agora.

        ═══════════════════════════════════════════════════
        DIFERENÇA FUNDAMENTAL DE AUDIÊNCIA:
        Esta NÃO é uma audiência fria. A pessoa já te acompanha.
        Portanto: menos contexto, mais profundidade. Menos apresentação, mais revelação.
        Fale como um mentor próximo que identificou algo específico e quer compartilhar.
        A confiança já existe — use-a para ir direto ao ponto com elegância e sabedoria real.
        ═══════════════════════════════════════════════════

        MATERIAL DA SEMANA (CENTRO DE TODA A NARRATIVA):
        - Título: "{titulo_pdf_tarde}"
        - Conteúdo resumido: {resumo_pdf_tarde[:350]}

        ═══════════════════════════════════════════════════
        FILOSOFIA BASE (injete de forma invisível — nunca cite diretamente):
        - Liberdade real vem de viver de forma autêntica, recusando padrões que nunca foram seus.
        - A ausência de propósito é a única forma de morte em vida.
        - O conhecimento compartilhado é o que mantém vivos os ideais além do tempo.
        - A existência ganha significado quando há coragem de manter as aspirações mais profundas.
        ═══════════════════════════════════════════════════

        ESTRUTURA OBRIGATÓRIA DA SEQUÊNCIA (EXATAMENTE 3 SLIDES RÁPIDOS):
        ═══════════════════════════════════════════════════

        SLIDE 1 — GANCHO DE PARADA (MÁXIMO 5 a 8 palavras):
        OBJETIVO: Quebra de padrão visceral. Faz o seguidor parar o scroll no primeiro segundo.
        O GANCHO DEVE seguir obrigatoriamente um destes 3 formatos estruturais (gire aleatoriamente entre eles):
        1. "3 passos simples pra mudar [Tema] hoje mesmo"
        2. "Saiba como conseguir fazer [Tema] com um simples passo"
        3. "Você já pensou nisso: [Tema], e como isso influencia sua vida?"
        (Substitua [Tema] pelo tema ou foco do material da semana: "{titulo_pdf_tarde}").

        SLIDE 2 — O PRINCÍPIO / ENSINAMENTO PRÁTICO (MÁXIMO 6 a 9 palavras):
        OBJETIVO: Entregar sabedoria real e aplicável ANTES de pedir qualquer ação.
        Compartilhe o princípio-chave ou insight mais valioso do material "{titulo_pdf_tarde}".
        Se o Gancho 2 ("Saiba como...") foi usado, liste os 3 passos de forma ultra-curta (ex: "Passo 1: [A]. Passo 2: [B]. Passo 3: [C].").
        Esta frase deve fazer o seguidor pensar: "Eu PRECISO desse material completo."

        SLIDE 3 — CTA DIRETO (MÁXIMO 10 a 12 PALAVRAS):
        O slide 3 é o CTA de conversão para o Direct. Retorne exatamente este placeholder de CTA:
        "Comente '{cta_do_dia}' no Direct para receber o material completo."

        ═══════════════════════════════════════════════════
        REGRAS ABSOLUTAS:
        ═══════════════════════════════════════════════════
        - Tom: sereno, firme, próximo. Como um mentor que fala de igual para igual.
        - O Slide 2 DEVE entregar valor real — um princípio que valha a pena salvar e compartilhar.
        - PROIBIDO: "acredite em você", "nunca desista", "foco e determinação", "você é capaz", exclamações.
        - Não use "..." mais de uma vez na sequência inteira.

        PEXELS/PIXABAY QUERY:
        Crie queries de vídeo com estética DARK LUXURY CINEMATIC — liderança, contemplação e sofisticação urbana noturna.
        Exemplos: "confident man overlooking city skyline night lights cinematic 4k" ou "elegant person walking golden lit street night architecture"

        LEGENDA (3 a 4 linhas):
        - Benefício direto e concreto de receber o material — o que muda na prática.
        - Tom de mentor próximo — sem hype, sem urgência artificial.
        - Termine com variação do CTA: "Comente '{cta_do_dia}' que te envio no Direct 👇"
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido (o array 'slides' DEVE ter EXATAMENTE 3 itens):
        {{
          "cta_keyword": "{cta_do_dia}",
          "slides": [
            "Slide 1 — Gancho selecionado (5 a 8 palavras)",
            "Slide 2 — Princípio prático ou os 3 passos (6 a 9 palavras)",
            "Comente '{cta_do_dia}' no Direct para receber o material."
          ],
          "pexels_queries": [
            "confident man overlooking city skyline night lights cinematic 4k"
          ],
          "legenda": "Legenda próxima descrevendo o benefício prático do material. Comente '{cta_do_dia}' que te envio no Direct 👇"
        }}
        """
    elif tipo == "carousel":
        prompt = f"""
        Você cria Carrosséis de Instagram com narrativa progressiva, ganchos magnéticos e contrastes cortantes.
        Estilo obrigatório para este carrossel: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        1. TÍTULO DA CAPA (máximo 6 palavras):
        - O título da capa deve ser construído DIRETAMENTE a partir do gancho sorteado nas instruções acima.
        - Adapte o gancho de referência ({descricao_categoria}) para um título curto e provocativo que force o clique.
        - Formatos aceitos:
          * Afirmação chocante curta: "O preço que você não vê."
          * Pergunta que agride: "Por que você faz isso de novo?"
          * Paradoxo: "Quanto mais você corre, mais parado fica."
          * Declaração de identidade: "Dois tipos de pessoa. Qual é você?"
        - PROIBIDO: títulos com "dicas", "aprenda a", "como fazer", "passos para", "top X".

        2. SLIDES DE CONTEÚDO (entre 5 e 8 slides — o número exato deve variar livremente conforme a necessidade da mensagem):
        - Cada slide: frase curtíssima e cirúrgica de no entre 10 e 15 palavras (ideal: entre 5 e 8). Sem rodeios.
        - PROIBIDO usar "..." em todo slide — use no máximo 1 vez por carrossel, somente quando criar tensão real.
        - A sequência dos slides deve seguir esta arquitetura narrativa FLUIDA:

          SLIDE 1 — GANCHO (Pattern Interrupt):
          Adapte o gancho de referência '{gancho}' ao ângulo do post. Frase curta, cortante, que para o scroll.
          Deve usar a estrutura do formato: {descricao_categoria}

          SLIDES 2-3 — ABERTURA DE LOOP (Efeito Zeigarnik):
          Abra um ciclo de curiosidade sem fechá-lo. Aprofunde a provocação do gancho.
          O leitor deve sentir que precisa virar o slide para descobrir o que vem a seguir.
          PROIBIDO entregar a solução aqui.

          SLIDES 4-5 — DOR DO COTIDIANO (Identificação visceral):
          Nomeie a dor concreta e reconhecível do dia a dia do leitor.
          Seja específico. O leitor deve pensar: "Isso sou eu. Exatamente."
          Bata na ferida antes de curar.

          SLIDES 6-7 (se houver) — VIRADA E INSIGHT:
          Entregue a verdade prática ou o contraste que muda a perspectiva.
          Uma lição crua, madura, aplicável. Sem moralismo barato.
          Exemplos de formato: "Nem todo afastamento é perda. Alguns é só livramento."
                               "Pra cobrar de 10 a 10, você não pode ser nove e meio."

          SLIDE FINAL — XEQUE-MATE:
          Frase reflexiva e poderosa para o leitor guardar mentalmente.
          Deve criar o desejo de salvar ou compartilhar. Feche com impacto, sem conclusão bonita e embalada.

        VALOR PERCEBIDO DO CARROSSEL (OBRIGATÓRIO — LEI DO RECHEIO):
        - Cada slide deve ENTREGAR valor crescente — o leitor deve sentir que está desvendando um mecanismo oculto sobre a mente, o comportamento ou a maestria pessoal.
        - Os slides 4-5 DEVEM trazer sabedoria bíblica, estoica ou psicológica aplicável — não conselhos genéricos.
        - Explique primeiro: por que isso acontece (causa), qual é o erro invisível (diagnóstico), qual princípio resolve (solução prática).
        - O slide final deve ser tão forte que o leitor precise salvar ou enviar para alguém. Esse é o teste de qualidade.
        - PROIBIDO encerrar com frases motivacionais genéricas. Feche com uma verdade que doa ou liberta.

        3. LEGENDA:
        - Reforce a provocação do carrossel em 3-4 linhas usando linguagem direta, madura e próxima.
        - CTA OBRIGATÓRIO: A legenda DEVE terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NUNCA termine com uma conclusão fechada. O leitor deve ter algo a dizer ou um passo a dar.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim (slides deve ter entre 5 e 8 itens):
        {{
          "titulo": "Título da capa aqui",
          "slides": [
            "Slide 1 — Gancho adaptado do sistema",
            "Slide 2 — Abertura de loop",
            "Slide 3 — Aprofunda o loop / mistério",
            "Slide 4 — Dor do cotidiano",
            "Slide 5 — Bate na ferida",
            "Slide 6 — Virada / insight (opcional)",
            "Slide 7 — Regra prática (opcional)",
            "Slide final — Xeque-mate reflexivo"
          ],
          "legenda": "Sua legenda completa aqui sem hashtags"
        }}
        """
    elif tipo in ["reels", "reels_noite"]:
        prompt = f"""
        Você é o mestre da sabedoria prática do perfil @codigo.da.sabedoria_. Seu objetivo é criar slides que façam o usuário PARAR o scroll e sentir que recebeu algo valioso.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA DE EXATAMENTE 3 SLIDES (ENTRE 10 E 15 PALAVRAS POR SLIDE):
        - Slide 1 (GANCHO VISCERAL): Frase curta e cortante que quebra o padrão mental do leitor nos primeiros 2 segundos. Baseada em uma contradição, contraste ou declaração ousada de sabedoria.
        - Slide 2 (ENSINAMENTO PRÁTICO): NÃO é outra pergunta — é a entrega de um princípio real, lei comportamental ou insight bíblico/estoico/psicológico que o leitor vai querer salvar e compartilhar.
        - Slide 3 (CTA DE SEGUIR): Uma chamada para o leitor seguir o perfil para acompanhar os próximos ensinamentos.

        REGRAS DE ALTA RETENÇÃO:
        * Cada slide deve ser autossuficiente E conectado ao próximo — nenhum slide pode ser removido sem perder sentido.
        * PROIBIDO frases poéticas abstratas que soem bonitas mas não ensinam nada.
        * NÃO use pontos de exclamação.

        LEGENDA:
        - Máximo 3 linhas. Complementa o insight com uma reflexão prática direta.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter EXATAMENTE 3 itens):
        {{
          "slides": [
            "Slide 1 (Gancho visceral)",
            "Slide 2 (Ensinamento prático real)",
            "Siga o perfil para mais reflexões."
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_conquistador":
        prompt = f"""
        Você é o porta-voz de uma identidade viva e real. Não tenta convencer ninguém.
        Declara quem é — com densidade, coerência e autenticidade de quem viveu o que diz.
        {evitar_repeticao_msg}

        ===== PERSONA OBRIGATÓRIA: O CONQUISTADOR =====
        Esta é a essência que deve atravessar cada palavra:

        Fe profunda — nao como performance religiosa, mas como ancora interior e convicção de que ha proposito em tudo.
        Foco inabalavel — quem sabe para onde vai, nao se distrai com o que nao constroi.
        Iluminação — a busca continua por enxergar alem do obvio, do superficial e do imediato.
        Sabedoria — nao acumulo de informação, mas discernimento conquistado com experiencia e silencio.
        Espirito aventureiro — o conforto nunca foi o objetivo. A vida foi feita para ser vivida com ousadia.
        Batalhador — nao ha vitoria sem construção. Nao ha construção sem disciplina silenciosa e diaria.
        Sonhador — quem para de sonhar começa a encolher. O sonho e o combustivel da ação.
        Amante da liberdade — liberdade real nao e ausencia de responsabilidade, e fidelidade aos proprios valores.
        Valores familiares — familia e o fundamento. O que se conquista tem que ter raiz e legado.
        Amoroso — força e afeto nao se contradizem. O homem que ama com profundidade e o que mais cresce.
        Pensador — antes de agir, reflete. Antes de falar, pensa. A lentidao do raciocinio e virtude.
        Criador — a existencia pede que se construa algo com as maos, com a mente, com a alma.
        Conquistador — nao de pessoas, mas de versoes cada vez mais elevadas de si mesmo.
        Culto e estudioso — o livro, o silencio e a observação sao os melhores professores.
        Curioso — quem para de perguntar para de crescer.
        Criterioso — nao aceita tudo. Filtra com inteligencia. Escolhe com principio.
        Pontual e afetivo — respeito pelo tempo alheio e presença genuina nas relações.
        Visionario — enxerga o que ainda nao existe, mas que pode ser construido.
        ================================================

        CRIE UMA SEQUÊNCIA NARRATIVA DE EXATAMENTE 3 SLIDES que seja um MANIFESTO DE IDENTIDADE.
        Nao siga o modelo de curiosidade. Nao crie ganchos de suspense. Nao tente vender nada.
        Declare. Afirme. Construa com palavras.

        REGRAS DE ESTILO OBRIGATÓRIAS:
        - Tom: denso, intimo, real — como uma conversa entre pessoas que se respeitam
        - Cada slide deve ter MÁXIMO de 5 a 8 palavras. Frases cortantes e diretas.
        - PROIBIDO frases de autoajuda vazias (ex: "acredite em voce", "seja sua melhor versao")
        - PROIBIDO qualquer CTA, convite para seguir, convite invisivel ou pergunta reflexiva
        - PROIBIDO ponto de exclamação
        - PROIBIDO "..." automatico — use no maximo 1 vez por sequencia, somente quando criar tensao real
        - O arco narrativo deve ter coerencia: Slide 1 = Declaracao, Slide 2 = Valor vivido, Slide 3 = Fechamento firme

        EXEMPLOS DE TOM (nao copie — inspire-se):
        - "Nao persigo o sucesso. Construo quem merece."
        - "Minha liberdade e fidelidade aos meus valores."
        - "Fe e agir antes de ver acontecer."

        UNIVERSO VISUAL OBRIGATÓRIO:
        Queries em inglês evocando a estética de Solidão Urbana Contemporânea: cidades grandes à noite, arranha-céus, luzes urbanas vibrantes, iluminação dourada/âmbar, atmosfera 35mm.
        PROIBIDO: cenas de estádio de futebol, lutas, festas com bebidas, deserto ou praia diurna.
        (ex: contemporary urban solitude night city lights 35mm, modern skyscraper rooftop night golden light, city lights reflections wet street 4k)

        Responda APENAS em formato JSON valido assim (EXATAMENTE 3 SLIDES):
        {{
          "pexels_queries": [
            "contemporary urban solitude night city lights 35mm",
            "modern skyscraper rooftop night golden light cinematic",
            "city lights reflections wet street 4k"
          ],
          "slides": [
            "Texto do Slide 1 (Declaracao curta - 5 a 8 palavras)",
            "Texto do Slide 2 (Valor vivido - 5 a 8 palavras)",
            "Texto do Slide 3 (Sentenca firme de sabedoria - 5 a 8 palavras)"
          ],
          "legenda": "Maximo 2 linhas. Extensao natural do manifesto. Sem hashtags. Sem CTA."
        }}
        """

    elif tipo == "pexels_story":
        prompt = f"""
        Você é a voz do @codigo.da.sabedoria_ em formato Story matinal. Sua missão é criar uma sequência de 3 slides com sabedoria prática real em vídeo cinematográfico de fundo.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA DE EXATAMENTE 3 SLIDES RÁPIDOS E DE ALTO VALOR:

        - Slide 1 (GANCHO DE PARADA): Frase visceral e cortante de 5 a 8 palavras que quebra o piloto automático do leitor. Baseada em contraste, declaração ousada ou princípio de sabedoria. PROIBIDO perguntas fracas.
        - Slide 2 (PRINCÍPIO PRÁTICO): Entregue um ensinamento real e aplicável de 6 a 9 palavras — não outra pergunta. O leitor deve pensar: "Quero salvar isso."
        - Slide 3 (CTA DE SEGUIR): Uma chamada curta e direta de 5 a 8 palavras para o leitor seguir o perfil.

        PEXELS QUERY — UM ÚNICO VÍDEO DE FUNDO CINEMATOGRÁFICO PREMIUM:
        Crie UMA ÚNICA query em inglês evocando sofisticação, maestria e liderança noturna:
        - Exemplos: "confident man standing city skyline night golden cinematic 4k", "modern architecture night golden light luxury 4k"
        - PROIBIDO: scenes de festa, bebida, esportes ou natureza diurna.

        LEGENDA:
        - Máximo 3 linhas. Tom de mentor próximo compartilhando sabedoria. SEM HASHTAGS.

        Responda APENAS em formato JSON válido assim (EXATAMENTE 3 SLIDES):
        {{
          "slides": [
            "Slide 1 (Gancho visceral - 5 a 8 palavras)",
            "Slide 2 (Princípio prático real - 6 a 9 palavras)",
            "Siga o perfil para mais sabedoria."
          ],
          "pexels_queries": [
            "confident man standing city skyline night golden cinematic 4k"
          ],
          "legenda": "Sua legenda de mentor próximo aqui sem hashtags"
        }}
        """
    elif tipo == "reels_noite":
        prompt = f"""
        Você é a voz do @codigo.da.sabedoria_ no horário noturno (18h). Seu objetivo é capturar a atenção de quem está exausto do dia e entregar sabedoria que mude a perspectiva do leitor antes de dormir.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA EXATA DE 6 SLIDES seguindo a estrutura de 6 Fases de Alta Retenção:

        - Slide 1 / Fase 1 (GANCHO NOTURNO — 0-2s): Declaração ousada ou contraste que para o scroll. NÃO comece com perguntas fracas. Use afirmações que gerem choque de realidade. (entre 10 e 15 palavras)
        - Slide 2 / Fase 2 (DIAGNÓSTICO — 2-6s): Identifique com precisão o estado emocional/mental real de quem chegou cansado em casa. Fale com "você" de forma íntima e verdadeira. (entre 10 e 15 palavras)
        - Slide 3 / Fase 3 (A CAUSA OCULTA): Revele o mecanismo por trás do problema — a causa real que ninguém fala. (entre 10 e 15 palavras)
        - Slide 4 / Fase 4 (PRINCÍPIO PRÁTICO DE SABEDORIA): Entregue o ensinamento bíblico, estoico ou psicológico que resolve o conflito. Esta é a fase do "UAU" — o leitor deve querer salvar o vídeo. (entre 10 e 15 palavras)
        - Slide 5 / Fase 5 (APLICAÇÃO IMEDIATA): Frase marcante que conecta o princípio à noite do leitor — o que ele faz AGORA com essa sabedoria. (entre 10 e 15 palavras)
        - Slide 6 / Fase 6 (FECHAMENTO NOTURNO): Sentença serena e firme para carregar antes de dormir. Sem CTA. (entre 10 e 15 palavras)

        LEGENDA:
        - Máximo 3 linhas. Complementa o ensinamento com um reflexo prático da sabedoria entregue.
        - SEM HASHTAGS.

        Responda APENAS em formato JSON válido assim:
        {{
          "slides": [
            "Slide 1 (Gancho noturno ousado)",
            "Slide 2 (Diagnóstico íntimo)",
            "Slide 3 (Causa oculta)",
            "Slide 4 (Princípio prático de sabedoria)",
            "Slide 5 (Aplicação imediata)",
            "Slide 6 (Fechamento sereno)"
          ],
          "legenda": "Sua legenda noturna aqui sem hashtags"
        }}
        """
    elif tipo == "pexels_story_noite":
        prompt = f"""
        Você é a voz do @codigo.da.sabedoria_ no fim do dia. Sua missão é entregar em 3 slides uma sabedoria que o leitor vai carregar para a noite e querer compartilhar antes de dormir.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA DE EXATAMENTE 3 SLIDES NOTURNOS — tom sereno, denso e de alta profundidade:

        - Slide 1 (GANCHO NOTURNO): Frase cortante de 5 a 8 palavras que captura o estado mental do fim do dia. Não uma pergunta genérica — uma declaração que toca diretamente no que o leitor viveu hoje.
        - Slide 2 (ENSINAMENTO SERENO): Princípio prático de sabedoria de 6 a 9 palavras que reorienta a perspectiva do leitor para o descanso e o crescimento. Deve ter o valor de uma frase que o leitor quer salvar.
        - Slide 3 (CTA DE SEGUIR): Uma chamada curta e direta de 5 a 8 palavras para o leitor seguir o perfil antes de dormir.

        PEXELS QUERY — UM ÚNICO VÍDEO DE FUNDO NOTURNO PREMIUM:
        Crie UMA ÚNICA query em inglês evocando elegância e reflexão noturna de alto nível:
        - Exemplos: "luxury penthouse interior night city view window cinematic", "person looking out window night city lights contemplation 4k"
        - PROIBIDO: festas, bebidas, esportes ou ambientes diurnos.

        LEGENDA:
        - Máximo 3 linhas. Tom de mentor próximo que fala de igual para igual. SEM HASHTAGS.

        Responda APENAS em formato JSON válido assim (EXATAMENTE 3 SLIDES):
        {{
          "slides": [
            "Slide 1 (Gancho noturno visceral - 5 a 8 palavras)",
            "Slide 2 (Ensinamento sereno e prático - 6 a 9 palavras)",
            "Siga o perfil para mais reflexões."
          ],
          "pexels_queries": [
            "person looking out window night city lights contemplation 4k"
          ],
          "legenda": "Sua legenda noturna de mentor próximo sem hashtags"
        }}
        """

    elif tipo == "reels_leads":
        resumo_pdf = ler_resumo_ultimo_pdf() or "Nenhum PDF anterior encontrado. Crie um roteiro genérico focando em 'Hábitos Inquebráveis'."
        evitar_repeticao_leads = buscar_historico_reels_leads(limite=6)
        if evitar_repeticao_leads:
            logger.info("📚 Histórico de reels_leads carregado para anti-repetição.")

        titulo_pdf_limpo = "Material Exclusivo"
        solucao_pdf_limpo = "Método Prático"

        bot_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        caminho_arquivo = os.path.join(bot_path, "gerador_pdf", "output", "ultimo_conteudo.json")
        if os.path.exists(caminho_arquivo):
            try:
                with open(caminho_arquivo, "r", encoding="utf-8") as f:
                    dados_pdf = json.load(f)
                titulo_pdf_limpo = dados_pdf.get("titulo_pdf", "Material Exclusivo")
                plano = dados_pdf.get("plano_acao", {})
                solucao_pdf_limpo = plano.get("subtitulo", "Método Prático")
            except Exception as e:
                logger.warning(f"Erro ao obter titulo e solucao do PDF: {e}")

        # ── Rotação sequencial dos 5 pilares visuais de alta classe ───────────
        PILARES_VISUAIS_LEADS = [
            {
                "nome": "Gala de Luxo e Alta Sociedade",
                "exemplo_query": "exclusive luxury gala evening event elegant man in suit chic woman cinematic",
                "descricao": "eventos de gala noturnos, ternos elegantes, vestidos de grife, iluminação dourada requintada e alta sociedade",
            },
            {
                "nome": "Caminhada Urbana Noturna",
                "exemplo_query": "stylish couple walking city night golden lighting architecture cinematic 4k",
                "descricao": "casais ou pessoas elegantes caminhando em avenidas e praças iluminadas à noite ou no amanhecer",
            },
            {
                "nome": "Visão Penthouse e Liderança",
                "exemplo_query": "confident leader standing modern skyscraper penthouse balcony city night view",
                "descricao": "terraços de luxo, coberturas modernas, visão panorâmica da cidade iluminada e atmosfera de triunfo",
            },
            {
                "nome": "Estilo de Vida VIP Sábio",
                "exemplo_query": "luxury sports car driving illuminated modern city night successful lifestyle",
                "descricao": "carros premium rodando pela cidade à noite, arquitetura contemporânea, cafés requintados e sobriedade",
            },
            {
                "nome": "Palco e Prestígio",
                "exemplo_query": "charismatic leader speaking on illuminated stage audience applause cinematic",
                "descricao": "líderes em palcos iluminados, atmosfera de sabedoria, palestras de prestígio e autoridade",
            },
        ]
        estado_leads = carregar_estado()
        idx_pilar = estado_leads.get("index_pilar_reels_leads", 0) % len(PILARES_VISUAIS_LEADS)
        pilar_atual = PILARES_VISUAIS_LEADS[idx_pilar]
        estado_leads["index_pilar_reels_leads"] = (idx_pilar + 1) % len(PILARES_VISUAIS_LEADS)
        salvar_estado(estado_leads)
        pilar_nome = pilar_atual["nome"]
        pilar_exemplo = pilar_atual["exemplo_query"]
        pilar_descricao = pilar_atual["descricao"]
        logger.info(f"🎨 [REELS_LEADS] Pilar visual #{idx_pilar+1} forçado: {pilar_nome.upper()}")
        # ─────────────────────────────────────────────────────────────────────

        # ── Sorteio declarado do mecanismo persuasivo ─────────────────────────
        MECANISMOS_PERSUASIVOS = [
            {
                "nome": "IDENTIDADE",
                "descricao": "Desperta a consciência de status. Faz a pessoa perceber a distância entre quem ela é e quem ela sabe que poderia ser. Usa tensão interna, não acusação.",
                "exemplo_gancho": "Você não quer uma vida maior. Quer uma vida que finalmente pareça sua.",
            },
            {
                "nome": "CONTRASTE",
                "descricao": "Coloca dois mundos lado a lado. Mostra que pessoas em situação similar chegaram a destinos opostos — e que a diferença estava em uma percepção, não em esforço.",
                "exemplo_gancho": "Duas pessoas podem trabalhar 10 horas por dia. Uma constrói liberdade. A outra apenas acumula cansaço.",
            },
            {
                "nome": "CURIOSIDADE",
                "descricao": "Abre uma lacuna de informação. Apresenta uma pergunta ou dado surpreendente que a pessoa não consegue ignorar sem saber a resposta. Cria tração para continuar lendo.",
                "exemplo_gancho": "Existe uma pergunta simples que pode revelar por que seus planos continuam sendo adiados.",
            },
            {
                "nome": "REVELAÇÃO",
                "descricao": "Remove a culpa da pessoa e revela que o obstáculo real é externo — um padrão oculto, uma crença instalada, uma ausência de método. A pessoa sente alívio e abertura.",
                "exemplo_gancho": "O problema talvez não seja falta de disciplina. É tentar organizar uma vida que nunca foi planejada para você.",
            },
            {
                "nome": "DESAFIO",
                "descricao": "Convoca a pessoa a se posicionar. Faz uma pergunta que ela deveria saber responder — mas provavelmente não sabe. Ativa o desejo de provar algo para si mesma.",
                "exemplo_gancho": "Se você tivesse que eliminar 80% do que ocupa seu dia, saberia quais 20% merecem permanecer?",
            },
            {
                "nome": "AUTORIDADE",
                "descricao": "Posiciona quem fala como alguém que estudou algo que a maioria ignora. Cria curiosidade sobre o que essa pessoa sabe — e que o seguidor ainda não aprendeu.",
                "exemplo_gancho": "Passei a estudar uma coisa que quase ninguém ensina: como transformar intenção em execução real.",
            },
        ]
        idx_mecanismo = estado_leads.get("index_mecanismo_reels_leads", 0) % len(MECANISMOS_PERSUASIVOS)
        mecanismo_atual = MECANISMOS_PERSUASIVOS[idx_mecanismo]
        estado_leads["index_mecanismo_reels_leads"] = (idx_mecanismo + 1) % len(MECANISMOS_PERSUASIVOS)
        salvar_estado(estado_leads)
        mecanismo_nome = mecanismo_atual["nome"]
        mecanismo_descricao = mecanismo_atual["descricao"]
        mecanismo_gancho = mecanismo_atual["exemplo_gancho"]
        logger.info(f"🧠 [REELS_LEADS] Mecanismo persuasivo #{idx_mecanismo+1}: {mecanismo_nome}")
        # ─────────────────────────────────────────────────────────────────────

        prompt = f"""
        Você é um estrategista de conversão de elite, especialista em comportamento humano, funis de decisão e copywriting de alta performance.
        Sua função é criar um REEL de slides de texto para o perfil @codigo.da.sabedoria_ voltado a PÚBLICO FRIO — pessoas que ainda não seguem o perfil e estão consumindo conteúdo rapidamente.

        ═══════════════════════════════════════════════════
        MECANISMO PERSUASIVO DESTA GERAÇÃO: {mecanismo_nome}
        {mecanismo_descricao}
        Exemplo de gancho para este mecanismo: "{mecanismo_gancho}"
        VOCÊ DEVE CONSTRUIR TODA A SEQUÊNCIA USANDO EXCLUSIVAMENTE ESTE MECANISMO.
        ═══════════════════════════════════════════════════

        MATERIAL DA SEMANA (ENTREGA AO FINAL DO FUNIL):
        - Título: "{titulo_pdf_limpo}"
        - Solução Prática: "{solucao_pdf_limpo}"
        - Contexto: {resumo_pdf[:300]}

        {evitar_repeticao_leads}

        ═══════════════════════════════════════════════════
        FILOSOFIA DO CONTEÚDO (injete de forma invisível — nunca cite diretamente):
        - Liberdade real vem de viver de forma autêntica, recusando padrões que nunca foram seus.
        - A ausência de propósito é a única forma de morte em vida.
        - Trabalhar muito na direção errada é a forma mais sofisticada de ficar parado.
        - A mudança não exige mais esforço. Exige uma percepção que você ainda não teve.
        ═══════════════════════════════════════════════════

        ANTES DE ESCREVER, DEFINA INTERNAMENTE (não precisa aparecer no JSON):
        1. A única ideia que este Reel vai comunicar (uma frase).
        2. O comportamento específico que cada slide precisa provocar.
        3. Se a sequência toda conduz logicamente ao PDF como próxima peça natural da conversa.

        ═══════════════════════════════════════════════════
        ESTRUTURA OBRIGATÓRIA DOS SLIDES (EXATAMENTE 4 SLIDES DE ALTA RETENÇÃO):
        ═══════════════════════════════════════════════════

        SLIDE 1 — GANCHO VISCERAL / QUEBRA DE PADRÃO (MÁXIMO 6 a 8 palavras):
        OBJETIVO: Fazer o polegar travar no primeiro milissegundo.
        Abra com uma declaração ousada, contraste ou segredo usando o mecanismo {mecanismo_nome}.
        PROIBIDO: Perguntas retóricas fracas ("Você sabe a diferença?"), poesia abstrata ou clichês motivacionais.
        Exemplo: "A regra de ouro que a maioria ignora:" ou "O erro silencioso que trava seus resultados:"

        SLIDE 2 — O DIAGNÓSTICO / TENSÃO REAL (MÁXIMO 8 a 11 palavras):
        OBJETIVO: Fazer a pessoa sentir "isso foi escrito exatamente para mim".
        Aponte a causa real por trás da frustração/cansaço/falta de direção sem acusar o leitor.
        Exemplo: "Você não está sobrecarregado pelo que faz, mas pelo que tolera em silêncio."

        SLIDE 3 — O CÓDIGO DA SABEDORIA / INSIGHT PRÁTICO (MÁXIMO 8 a 11 palavras):
        OBJETIVO: O momento "UAU" — Entregar sabedoria prática e concreta antes de pedir qualquer ação.
        Entregue um princípio real de maestria/provérbios conectado com {titulo_pdf_limpo}.
        Exemplo: "Provérbios ensina: domínio próprio não é força bruta, é saber filtrar o que entra."

        SLIDE 4 — CTA DINÂMICO PARA AUDIÊNCIA FRIA (MÁXIMO 10 a 12 PALAVRAS NO TOTAL, dividido por quebra de linha):
        OBJETIVO: Converter visitantes de fora do perfil em leads que comentam e recebem o material no Direct.
        ATENÇÃO — REGRA ANTI-PAPAGAIO: NUNCA use frases batidas ou clichês engessados. Crie uma variação INÉDITA, contextualizada ao tema "{titulo_pdf_limpo}".

        Estruturas de inspiração para a audiência fria do Feed (escolha 1 estrutura e personalize com o tema):
        - Estrutura 1 (Valor Direto): Parte 1: "Quer o guia prático de {titulo_pdf_limpo}?" \n Parte 2: "Comente 'SABEDORIA' abaixo que te envio no Direct 👇"
        - Estrutura 2 (Aplicação): Parte 1: "Para aplicar esse método na sua vida:" \n Parte 2: "Comente 'SABEDORIA' e receba o material no Direct 👇"
        - Estrutura 3 (Acesso Exclusivo): Parte 1: "Liberamos o mapa completo desta semana:" \n Parte 2: "Comente 'SABEDORIA' para receber no Direct 👇"
        - Estrutura 4 (Pergunta de Desejo): Parte 1: "Pronto para dominar {titulo_pdf_limpo}?" \n Parte 2: "Comente 'SABEDORIA' que te entrego no Direct 👇"
        - Estrutura 5 (Transformação): Parte 1: "Baixe o guia de evolução da semana:" \n Parte 2: "Comente 'SABEDORIA' e receba agora no Direct 👇"
        - Estrutura 6 (Solução): Parte 1: "Quer o passo a passo completo?" \n Parte 2: "Comente 'SABEDORIA' abaixo e receba no Direct 👇"

        REGRA INEGOCIÁVEL: A soma das duas partes NÃO PODE ultrapassar 12 palavras no total (máximo 3 linhas na tela).
        O tom deve ser CLARO, CONVIDATIVO e DIRETO para quem NUNCA te viu antes.

        ═══════════════════════════════════════════════════
        REGRAS ABSOLUTAS DE QUALIDADE & RETENÇÃO:
        ═══════════════════════════════════════════════════
        - A lei do recheio: O Slide 3 DEVE entregar um ensinamento que valha a pena ser salvo ou compartilhado.
        - Elimine qualquer tom de coach clichê ("acredite em você", "lute sempre"). Fale com a autoridade de um mestre de sabedoria prática.
        - Nunca use frases de efeito que soem vazias ou desconectadas da realidade.
        - O material semanal ({titulo_pdf_limpo}) é a ferramenta de aplicação definitiva desse ensinamento.

        PEXELS QUERY — PILAR VISUAL OBRIGATÓRIO: "{pilar_nome}"
        A PRIMEIRA query do array pexels_queries DEVE ser: '{pilar_exemplo}'
        As demais complementam o mesmo universo visual: {pilar_descricao}.
        PROIBIDO: vídeos de dor, chuva, depressão, isolamento, escuridão. Toda query DEVE evocar poder, luz, movimento, liderança ou conquista.

        LEGENDA (3 a 4 linhas):
        - Benefício direto e concreto, sem jargões, sem hype.
        - Tom de conversa próxima, como alguém que descobriu algo e está compartilhando.
        - DEVE terminar com variação natural do CTA. Exemplo: "Comente 'SABEDORIA' que te envio no Direct 👇"
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido (o array 'slides' DEVE conter EXATAMENTE 4 frases, a 4ª com quebra de linha):
        {{
          "cta_keyword": "SABEDORIA",
          "slides": [
            "Gancho visceral curto com {mecanismo_nome}.",
            "Diagnóstico preciso da tensão ou conflito real.",
            "Princípio de sabedoria prática conectado a {titulo_pdf_limpo}.",
            "Quer o guia completo de {titulo_pdf_limpo}? \\n Comente 'SABEDORIA' que te envio no Direct 👇"
          ],
          "pexels_queries": [
            "{pilar_exemplo}",
            "exclusive luxury gala evening event elegant man in suit 4k",
            "stylish couple walking city night golden lighting architecture"
          ],
          "legenda": "Legenda próxima e direta baseada no material desta semana. Comente 'SABEDORIA' que te envio no Direct 👇"
        }}
        """
    else:
        raise ValueError(f"Tipo inválido: {tipo}")

    # [NOVO] Adiciona a exigência dos 5 novos metadados na raiz do JSON, independente do tipo de post
    prompt += """
    MUITO IMPORTANTE: Além da estrutura exigida acima, você DEVE retornar as seguintes 5 chaves NA RAIZ do seu JSON:
    - "objetivo": O objetivo principal deste post (ex: "Educar", "Vender", "Inspirar", "Entreter")
    - "categoria_imagem": A estética visual sugerida (ex: "Minimalista", "Cores Quentes", "Texto Dinâmico", "B-roll")
    - "categoria_musica": A vibração sonora sugerida (ex: "Lofi", "Phonk", "Acústico", "Misterioso", "Sem Música")
    - "estrutura_narrativa": A forma como a história é contada (ex: "Problema-Solução", "Lista", "Storytelling", "Ameaça-Alívio")
    - "complexidade": O nível intelectual do conteúdo ("Baixa", "Média", "Alta")
    """

    # Função auxiliar para extrair JSON de markdown
    def extrair_json(texto):
        # Remove blocos markdown (```json ... ```) e eventuais espaços
        import re
        texto = texto.strip()
        padrao = r'```(?:json)?\s*(.*?)\s*```'
        match = re.search(padrao, texto, re.DOTALL)
        if match:
            texto = match.group(1)
        # Tenta parsear
        return json.loads(texto)

    # LOOP DE TENTATIVAS (Múltiplas chaves)
    max_tentativas_por_chave = 3
    
    for key_index, current_key in enumerate(GEMINI_KEYS):
        logger.info(f"Tentando usar chave Gemini {key_index + 1}/{len(GEMINI_KEYS)}...")
        client = genai.Client(api_key=current_key)
        
        for tentativa in range(max_tentativas_por_chave):
            try:
                resposta = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                
                # Extração e parse robusto
                try:
                    dados = extrair_json(resposta.text)
                except Exception as e:
                    logger.error(f"Erro ao parsear JSON na Tentativa {tentativa+1}. Texto bruto: {resposta.text}")
                    raise Exception(f"Gemini nao retornou um JSON valido: {e}")
                
                # Pos-processamento centralizado
                dados = _pos_processar_dados(
                    dados, tipo, tema_escolhido, detalhes_tema,
                    gancho_categoria=descricao_categoria, tipo_cta=categoria_cta,
                    subtema=sub_angulo, tom_emocional=estilo_escolhido
                )
                    
                return dados, tema_escolhido, estilo_escolhido
                
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                    logger.warning(f"⚠️ Cota esgotada na chave {key_index + 1} (429). Passando para a próxima chave...")
                    break # Sai do loop de tentativas e vai para a próxima chave
                
                if tentativa < max_tentativas_por_chave - 1:
                    logger.warning(f"⚠️ Erro ao chamar Gemini (Chave {key_index + 1}, Tentativa {tentativa+1}/{max_tentativas_por_chave}): {e}. Tentando novamente em 5 segundos...")
                    time.sleep(5)
                else:
                    logger.error(f"❌ Falha ao obter resposta na chave {key_index + 1} após {max_tentativas_por_chave} tentativas.")
                    
    # Se sair do loop do Gemini, todas as chaves falharam.
    logger.warning("⚠️ Gemini esgotado. Tentando GROQ (llama-3.3-70b)...")

    # ─── FALLBACK 1: GROQ ───
    for groq_index, groq_key in enumerate(GROQ_KEYS):
        logger.info(f"🔑 Tentando usar chave Groq {groq_index + 1}/{len(GROQ_KEYS)}...")
        try:
            import requests as _req
            groq_resp = _req.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096, "temperature": 0.9},
                timeout=60
            )
            if groq_resp.status_code == 200:
                texto_groq = groq_resp.json()["choices"][0]["message"]["content"]
                dados = extrair_json(texto_groq)
                # Pos-processamento centralizado
                dados = _pos_processar_dados(
                    dados, tipo, tema_escolhido, detalhes_tema,
                    gancho_categoria=descricao_categoria, tipo_cta=categoria_cta,
                    subtema=sub_angulo, tom_emocional=estilo_escolhido
                )
                logger.success(f"✅ [GROQ] Conteúdo gerado com sucesso pela chave {groq_index + 1}!")
                return dados, tema_escolhido, estilo_escolhido
            elif groq_resp.status_code == 429:
                logger.warning(f"⚠️ Groq chave {groq_index + 1}: cota esgotada. Tentando próxima...")
            else:
                logger.warning(f"⚠️ Groq chave {groq_index + 1}: erro HTTP {groq_resp.status_code}.")
        except Exception as e:
            logger.warning(f"⚠️ Groq chave {groq_index + 1} falhou: {str(e)[:100]}")

    # ─── FALLBACK 2: OPENROUTER ───
    if OPENROUTER_KEY:
        logger.warning("⚠️ Groq esgotado. Tentando OpenRouter (GPT-4o-mini)...")
        try:
            import requests as _req
            or_resp = _req.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENROUTER_KEY}", "Content-Type": "application/json"},
                json={"model": "openai/gpt-4o-mini", "messages": [{"role": "user", "content": prompt}], "max_tokens": 4096},
                timeout=60
            )
            if or_resp.status_code == 200:
                texto_or = or_resp.json()["choices"][0]["message"]["content"]
                dados = extrair_json(texto_or)
                # Pos-processamento centralizado
                dados = _pos_processar_dados(
                    dados, tipo, tema_escolhido, detalhes_tema,
                    gancho_categoria=descricao_categoria, tipo_cta=categoria_cta,
                    subtema=sub_angulo, tom_emocional=estilo_escolhido
                )
                logger.success("✅ [OPENROUTER] Conteúdo gerado com sucesso!")
                return dados, tema_escolhido, estilo_escolhido
            else:
                logger.warning(f"⚠️ OpenRouter falhou: HTTP {or_resp.status_code} - {or_resp.text[:100]}")
        except Exception as e:
            logger.warning(f"⚠️ OpenRouter falhou: {str(e)[:100]}")

    # ─── FALLBACK FINAL: MENSAGENS DE EMERGÊNCIA ───
    logger.warning("🚨 [SAÍDA DE EMERGÊNCIA] Todos os provedores falharam. Carregando post estático de contingência...")
    try:
        emergencia_file = "core/ai/mensagens_emergencia.json"
        if os.path.exists(emergencia_file):
            with open(emergencia_file, "r", encoding="utf-8") as f:
                emergencias = json.load(f)
            
            # Identifica o tema e normaliza
            tema_key = tema_escolhido.lower() if tema_escolhido else "superacao"
            if tema_key not in emergencias:
                tema_key = "superacao"
                
            # Mapeia os tipos de postagens para as chaves principais do JSON (story, reels, carousel)
            tipo_key = "story"
            if tipo in ["reels", "reels_noite", "reels_conquistador", "pexels_story", "pexels_story_noite", "reels_leads"]:
                tipo_key = "reels"
            elif tipo == "carousel":
                tipo_key = "carousel"
            
            # Sorteia uma das mensagens prontas
            lista_opcoes = emergencias.get(tema_key, {}).get(tipo_key, [])
            if lista_opcoes:
                import copy
                # Faz cópia para não alterar o dicionário original carregado em memória
                dados = copy.deepcopy(random.choice(lista_opcoes))
                
                # Pos-processamento centralizado
                dados = _pos_processar_dados(
                    dados, tipo, tema_escolhido, detalhes_tema,
                    gancho_categoria=descricao_categoria, tipo_cta=categoria_cta,
                    subtema=sub_angulo, tom_emocional=estilo_escolhido
                )
                
                logger.success(f"🛡️ [SAÍDA DE EMERGÊNCIA] Mensagem de contingência recuperada para Tema: {tema_key.upper()} | Formato: {tipo_key.upper()}")
                return dados, tema_escolhido, estilo_escolhido
                
    except Exception as e_emergencia:
        logger.error(f"❌ Erro grave no sistema de emergência: {e_emergencia}")

    raise ValueError(f"❌ Falha crítica: Todas as {len(GEMINI_KEYS)} chaves do Gemini falharam ou estão sem cota.")

