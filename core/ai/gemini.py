import json
import random
import time
import os
from google import genai
from datetime import datetime, timezone

from core.config.settings import GEMINI_KEYS, GROQ_KEYS, OPENROUTER_KEY
from core.ai.prompts import TEMAS_MAPEADOS, montar_instrucoes_copy
from core.ai.styles import sortear_estilo
from core.ai.olhos_da_rede import gerar_contexto_mundo_real
from core.config.state import carregar_estado, salvar_estado
from core.analytics.leitor_pdf import ler_resumo_ultimo_pdf
from loguru import logger


def buscar_historico_por_tema(tema, tipo_post=None, limite=8):
    """
    Busca os últimos posts do mesmo TEMA no historico_posts do Firebase.
    Retorna uma string de contexto para ser injetada no prompt da IA,
    instruindo-a a não repetir as frases e ideias já usadas nesse tema.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return ""

        # Consulta: mesmo tema, ordenado do mais recente ao mais antigo
        query = db.collection("historico_posts").where("tema", "==", tema)
        if tipo_post:
            query = query.where("tipo", "==", tipo_post)
        docs = query.order_by("data", direction="DESCENDING").limit(limite).stream()
        posts_anteriores = [doc.to_dict() for doc in docs]

        if not posts_anteriores:
            return ""

        msg = "\n        PROIBIDO REPETIR (HISTÓRICO DO TEMA):\n"
        msg += f"        O tema de hoje é '{tema}'. Veja abaixo o que já foi publicado nesse tema recentemente.\n"
        msg += "        Você DEVE criar algo completamente diferente — novas frases, novas metáforas, novos ângulos:\n"
        for i, p in enumerate(posts_anteriores):
            frase = p.get("frase_visual") or ""
            legenda_trecho = (p.get("legenda") or "")[:120]
            data = p.get("data", "")[:10]
            if frase or legenda_trecho:
                msg += f"        * Post {i+1} ({data}): Frase='{frase[:150]}' | Legenda='{legenda_trecho}...'\n"
        msg += "        Qualquer semelhança com os textos acima é inaceitável. Seja 100% original.\n"
        return msg

    except Exception as e:
        logger.warning(f"Erro ao buscar histórico por tema '{tema}': {e}")
        return ""

def buscar_historico_reels_leads(limite=6):
    """
    Busca os últimos reels_leads gerados em 'historico_reels_leads' no Firebase.
    Retorna string de contexto para a IA não repetir os mesmos ganchos e frases.
    """
    try:
        from core.analytics.db import get_db
        db = get_db()
        if not db:
            return ""
        docs = db.collection("historico_reels_leads") \
                 .order_by("data", direction="DESCENDING") \
                 .limit(limite).stream()
        posts = [doc.to_dict() for doc in docs]
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
    if "legenda" in dados and detalhes_tema and "hashtags" in detalhes_tema:
        tags = " ".join(detalhes_tema["hashtags"])
        if not any(tag in dados["legenda"] for tag in detalhes_tema["hashtags"]):
            dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
    # Metadados internos para o sistema de analytics (prefixo _ indica uso interno)
    dados["_gancho_categoria"] = gancho_categoria
    dados["_tipo_cta"]         = tipo_cta
    dados["_duracao_video"]    = duracao_video
    dados["_subtema"]          = subtema
    dados["_tom_emocional"]    = tom_emocional
    return dados

def gerar_conteudo_gemini(tipo):
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
    tema_escolhido = None
    contexto_analytics = ""
    evitar_repeticao_msg = ""
    
    agora = datetime.now(timezone.utc)
    dia_hoje_str = agora.strftime("%Y-%m-%d")

    is_conquistador = (tipo == "reels_conquistador")
    
    if is_conquistador:
        # Loop Cego: Ignora o Analytics e roda pelos 8 temas em sequência
        temas_lista = list(TEMAS_MAPEADOS.keys())
        idx = estado.get("index_conquistador", 0)
        if idx >= len(temas_lista): idx = 0
            
        tema_escolhido = temas_lista[idx]
        
        # Avança pro próximo dia
        estado["index_conquistador"] = (idx + 1) % len(temas_lista)
        salvar_estado(estado)
        logger.info(f"🎯 [CONQUISTADOR] Tema forçado pelo ciclo: {tema_escolhido}")

        # Busca histórico DESTE TEMA para evitar repetição de mensagens no Conquistador
        evitar_repeticao_msg = buscar_historico_por_tema(tema_escolhido, tipo_post="reels_conquistador", limite=6)
    else:
        # Se for o primeiro post do dia, rotaciona o tema sequencialmente
        if estado.get("data_tema_do_dia") == dia_hoje_str and estado.get("tema_do_dia"):
            tema_escolhido = estado["tema_do_dia"]
            logger.info(f"🎲 Tema do dia continuado: {tema_escolhido}")
        else:
            temas_lista = list(TEMAS_MAPEADOS.keys())
            idx = estado.get("index_tema_diario", 0)
            if idx >= len(temas_lista): idx = 0
            
            tema_escolhido = temas_lista[idx]
            
            estado["tema_do_dia"] = tema_escolhido
            estado["data_tema_do_dia"] = dia_hoje_str
            estado["index_tema_diario"] = (idx + 1) % len(temas_lista)
            salvar_estado(estado)
            logger.info(f"🎲 Novo tema sequencial diário ativado: {tema_escolhido}")

        # Busca histórico DESTE TEMA no historico_posts para não repetir a mensagem
        evitar_repeticao_msg = buscar_historico_por_tema(tema_escolhido, tipo_post=tipo, limite=8)
        if evitar_repeticao_msg:
            logger.info(f"📚 Histórico do tema '{tema_escolhido}' carregado para anti-repetição.")

        # NOVO FLUXO: Ciclo sequencial diário
        recomendacoes_file = "analytics/dados/recomendacoes.json"
        recomendacoes_semanais_file = "analytics/dados/recomendacoes_semanais.json"
        
        # Lê o contexto do analytics cruzado (diário/múltiplos períodos)
        try:
            if os.path.exists(recomendacoes_file):
                with open(recomendacoes_file, "r", encoding="utf-8") as f:
                    rec_cruzada = json.load(f)
                contexto_analytics += rec_cruzada.get("contexto_para_gemini", "") + "\n\n"

                # --- Fase 6: Injeção de Growth Score, ICC e Hipóteses Confirmadas ---
                gs_ref = rec_cruzada.get("growth_score_referencia", 0)
                if gs_ref > 0:
                    contexto_analytics += f"GROWTH SCORE DE REFERENCIA DA CONTA: {gs_ref:.4f}\n"
                    contexto_analytics += "  (Este e o benchmark atual. Posts acima deste valor impulsionam crescimento real.)\n\n"

                icc = rec_cruzada.get("icc_por_tema", {})
                if icc:
                    tema_icc_lider = max(icc, key=icc.get)
                    contexto_analytics += f"TEMA COM MAIOR ICC (converte curiosidade em seguidores): {tema_icc_lider.upper()} ({icc[tema_icc_lider]:.1%})\n\n"

        except Exception as e:
            logger.warning(f"Erro ao ler contexto do analytics cruzado: {e}")

        # Injeta hipóteses confirmadas da Memória Estratégica
        try:
            from core.analytics.motor_hipoteses import obter_hipoteses_confirmadas
            hipoteses = obter_hipoteses_confirmadas()
            if hipoteses:
                contexto_analytics += "CONHECIMENTO ESTRATEGICO VALIDADO (hipoteses confirmadas com dados reais):\n"
                for h in hipoteses[:5]:  # Limita a 5 para não inflar o prompt
                    contexto_analytics += f"  - {h['hipotese']} (Confianca: {h.get('confianca', 0):.0%}, Amostra: {h.get('amostra', 0)} posts)\n"
                contexto_analytics += "\n"
        except Exception:
            pass  # Motor ainda não rodou; ignora silenciosamente

        # Lê o contexto do analytics semanal (tendências)
        try:
            if os.path.exists(recomendacoes_semanais_file):
                with open(recomendacoes_semanais_file, "r", encoding="utf-8") as f:
                    rec_semanal = json.load(f)
                contexto_analytics += rec_semanal.get("contexto_para_gemini", "") + "\n\n"
        except Exception as e:
            logger.warning(f"Erro ao ler contexto do analytics semanal: {e}")

        # [NOVO] Adiciona a visão externa (Olhos da Rede)
        try:
            # Pega o nome do tema escolhido para fazer uma busca cirúrgica no YouTube
            nome_do_tema_atual = TEMAS_MAPEADOS[tema_escolhido]['nome'] if tema_escolhido in TEMAS_MAPEADOS else None
            mundo_real = gerar_contexto_mundo_real(dias=7, tema_especifico=nome_do_tema_atual)
            if mundo_real:
                contexto_analytics += "\n====================\n" + mundo_real + "\n====================\n\n"
        except Exception as e:
            logger.warning(f"Erro ao coletar Olhos da Rede: {e}")

    # Sorteia sentimento do dia de forma persistente ou diária (apenas para posts comuns - não conquistador)
    sentimento_escolhido = None
    if not is_conquistador:
        from core.ai.styles import SENTIMENTOS_CONFIG
        if estado.get("data_sentimento_do_dia") == dia_hoje_str and estado.get("sentimento_do_dia"):
            sentimento_escolhido = estado["sentimento_do_dia"]
            logger.info(f"🧠 Sentimento do dia continuado: {sentimento_escolhido.upper()}")
        else:
            # Sorteia sentimento diário
            sentimento_escolhido = random.choice(list(SENTIMENTOS_CONFIG.keys()))
            estado["sentimento_do_dia"] = sentimento_escolhido
            estado["data_sentimento_do_dia"] = dia_hoje_str
            salvar_estado(estado)
            logger.info(f"🧠 Novo sentimento diário sorteado: {sentimento_escolhido.upper()}")
        
    detalhes_tema = TEMAS_MAPEADOS[tema_escolhido]
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
    instrucoes_copy, sub_angulo, gancho, descricao_categoria, novo_indice, categoria_cta, referencia_cta, novo_indice_cta, arquitetura, novo_indice_arquitetura = montar_instrucoes_copy(
        detalhes_tema, contexto_analytics, hist_angulos, idx_atual, indice_cta, indice_arquitetura=indice_arquitetura, is_conquistador=is_conquistador, sentimento_escolhido=sentimento_escolhido
    )

    # Injeta o histórico do tema no instrucoes_copy → propagado automaticamente para TODOS os tipos de post
    if evitar_repeticao_msg:
        instrucoes_copy += evitar_repeticao_msg

    # Estilo de abordagem sorteado (com anti-repetição)
    estilo_escolhido = sortear_estilo(hist_estilos)
    logger.info(f"🎭 Estilo de abordagem sorteado: {estilo_escolhido.split(':')[0].upper()}")
    logger.info(f"🎣 Gancho sequencial #{idx_atual}: [{gancho[:50]}...]")
    logger.info(f"📐 Arquitetura narrativa: {arquitetura['nome']}")

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

    # Injeção da Base Bibliográfica (Livros) para posts que suportam profundidade
    livros_base = detalhes_tema.get("inspira", "")
    if livros_base and tipo != "reels_leads":
        instrucoes_livros = f"\n        BASE BIBLIOGRÁFICA (PROFUNDIDADE OBRIGATÓRIA):\n        - Inspire-se fortemente nos conceitos, filosofias e maturidade das seguintes obras: {livros_base}\n        - Traga o peso dessas referências para o conteúdo, sem perder a linguagem direta e moderna."
    else:
        instrucoes_livros = ""


    if tipo == "story":
        prompt = f"""
        Você cria Stories de Instagram direcionados estritamente para pessoas que JÁ TE SEGUEM (audiência quente).
        Sua comunicação deve ser uma CONVERSA ÍNTIMA, EXCLUSIVA, PROPOSITAL E DIRECIONAL.
        Estilo obrigatório para este story: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        DIRETRIZ DE ESCRITA:
        - Fale de igual para igual, como um mentor compartilhando uma percepção pessoal profunda do seu dia a dia.
        - Não use ganchos artificiais ou fórmulas de interrupção de padrão frias. Comece o diálogo diretamente.
        - Escreva uma única frase curta e com altíssimo impacto emocional (máximo de 15 palavras).
        - NÃO use ponto de exclamação. Use ponto final ou interrogação.
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": "Sua frase de conversa íntima com seu seguidor aqui"
        }}
        """
    elif tipo == "story_manha":
        prompt = f"""
        Você cria uma sequência de Stories de Instagram matinais para reflexão profunda com sua base de seguidores atuais.
        Sua missão é gerar uma CONVERSA INTENCIONAL e íntima que prepare o seguidor para encarar as decisões do dia.
        Estilo obrigatório para esta sequência: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA ENTRE 4 A 8 FRASES CURTAS CONECTADAS (MÁXIMO DE 12 PALAVRAS POR FRASE):
        - Cada frase representará um slide da sua conversa contínua.
        - Não use ganchos frios de atração. Comece o primeiro slide compartilhando uma dúvida, uma confissão ou um pensamento maduro diretamente.
        - Use os slides internos para aprofundar a lição ou o insight sugerido pelo sub-ângulo: "{sub_angulo}".
        - Termine a sequência (último slide) com uma frase de desfecho forte e reflexiva que dê um norte prático.
        - Não use ponto de exclamação.
        - Escolha se quer usar música de fundo ou não no story (true ou false) de acordo com o tom da conversa.
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": [
            "Frase do slide 1 (Início da conversa/Confissão)",
            "Frase do slide 2 (Aprofundamento)",
            "Frase do slide 3 (Insight ou dica prática)",
            "Frase do slide 4 (Conclusão direcional)"
          ],
          "usar_musica": true
        }}
        """
    elif tipo == "story_tarde":
        prompt = f"""
        Você cria uma sequência curta de Stories de Instagram para o fim de tarde com sua base de seguidores.
        O objetivo é dialogar sobre o cansaço do dia e a importância da consistência intencional.
        Estilo obrigatório para esta sequência: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA DE EXACTAMENTE 2 FRASES CURTAS CONECTADAS (MÁXIMO DE 12 PALAVRAS POR FRASE):
        - Slide 1: Uma reflexão íntima sobre o andamento do dia ou cansaço da rotina.
        - Slide 2: O insight prático ou a perspectiva do sub-ângulo: "{sub_angulo}" para trazer alívio e clareza.
        - Não use ponto de exclamação.
        - Escolha se quer usar música de fundo ou não (true ou false).
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": [
            "Frase do slide 1 (Conexão e rotina)",
            "Frase do slide 2 (Reflexão/Alívio)"
          ],
          "usar_musica": false
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
        - Cada slide: frase curtíssima e cirúrgica de no MÁXIMO 12 palavras. Sem rodeios.
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

        3. LEGENDA:
        - Reforce a provocação do carrossel em 3-4 linhas usando linguagem direta e madura.
        - CTA OBRIGATÓRIO: A legenda DEVE terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NUNCA termine com uma conclusão fechada. O leitor deve ter algo a dizer.
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
    elif tipo == "reels":
        prompt = f"""
        Você é um especialista em storytelling magnético e neurociência aplicada ao conteúdo digital.
        Seu objetivo é criar um roteiro em slides que faça o usuário PARAR de rolar o feed e assistir até o final.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA DINÂMICA DE 8 A 12 SLIDES (o número exato deve flutuar livremente entre 8 e 12 a cada execução dependendo da necessidade da história) seguindo esta estrutura fluida:

        - Slide 1: O Gancho/Quebra de Padrão (Pattern Interrupt) — Frase super provocativa e inesperada para parar o scroll.
        - Slides 2 a 4: Abertura de loop, mistério e detalhamento da dor (o problema no cotidiano do leitor).
        - Slides 5 a 8: A entrega de valor prática e a explicação do porquê funciona (o insight/segredo revelado).
        - Slides 9 a 11: Choque de realidade, quebra de desculpas comuns e validação/elogio da inteligência de quem leu até aqui.
        - Slide Final: Fusão de Xeque-mate com convite sutil para seguir. Crie uma frase de forte impacto que encerre a reflexão e faça um convite persuasivo e elegante para seguir o perfil (ex: "Se você busca respostas que a maioria ignora, acompanhe o perfil.").

        REGRAS DE ESCUTA E RITMO VISUAL:
        * Misture o comprimento das frases! Algumas devem ser extremamente curtas e cortantes (ex: 4 a 8 palavras) para acelerar o ritmo de leitura. Outras devem ser um pouco mais longas e explicativas (até 25 palavras) para dar profundidade.
        * LIMITE MÁXIMO ESTRITO: Nenhuma frase pode passar de 25 palavras sob hipótese alguma.
        * NÃO use pontos de exclamação.

        LEGENDA:
        - Máximo 3 linhas. Tom de quem viveu aquilo, não de quem está ensinando.
        - CTA OBRIGATÓRIO: A legenda DEVE obrigatoriamente terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NUNCA termine com uma frase bonita e fechada. Sempre com uma pergunta em aberto.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim:
        {{
          "slides": [
            "Frase do slide 1 (Gancho rápido)",
            "Frase do slide 2 (Abertura de loop)",
            "Frase do slide 3 (Um pouco mais longa explicando a dor e a realidade)",
            "Frase do slide 4 (Frase curta de transição)",
            "Frase do slide 5 (Entrega do método prático e segredo)",
            "Frase do slide 6 (Mais longa detalhando a solução)",
            "Frase do slide 7 (Elogio a inteligência do leitor)",
            "Frase do slide 8 (Xeque-mate final + convite sutil para seguir)"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_conquistador":
        prompt = f"""
        Você é a representação viva de uma alma sábia, motivada e aventureira. O seu tom é INSPIRADOR, SÁBIO, ARGUMENTADOR, CURIOSO, VALENTE E CORAJOSO.
        Você ESBANJA ALEGRIA de viver, contempla o belo da criação e busca a liberdade com espírito aventureiro.
        Sua visão é imaterial: seus pilares sagrados são AMOR, FAMÍLIA, AMIZADE VERDADEIRA, IGUALDADE e LIBERDADE.
        Use os recursos oratórios da persona: fale com elegância e proximidade, de igual para igual, inspirando as pessoas a viverem com propósito e coragem.
        {evitar_repeticao_msg}

        INSPIRAÇÕES E PILARES OBRIGATÓRIOS:
        - "Armadilhas da Mente" (Augusto Cury): Domínio sobre os pensamentos e gestão da emoção.
        - Sabedoria Sapiencial: Citações e essência das palavras de Salomão e Jesus.
        - "O Poder da Ação" (Paulo Vieira): Despertar para a coragem, consistência e execução real.
        - Espírito Aventureiro: A alegria de explorar a vida, aprender, amar e proteger quem amamos.

        O QUE VOCÊ REPUDIA (NUNCA VALORIZE):
        - Pessoas arrogantes, soberbas e vaidosas.
        - Filosofia barata de autoajuda vazia.
        - Amor falso, hipocrisia e interesses puramente materialistas.
        - Traição de princípios e deslealdade.

        ESTRUTURA DO VÍDEO MANIFESTO (9 CENAS INSPIRADORAS — MÁXIMO 15 PALAVRAS POR CENA):
        - Cena 1 (Abertura Aventureira/Contemplativa): Um convite inspirador e curioso sobre a beleza da vida, a jornada ou o valor do tempo (SEM soco no estômago ou agressividade).
        - Cena 2: A contemplação do belo da vida e a clareza sobre o que realmente importa.
        - Cena 3: A sabedoria atemporal que liberta a mente das aparências (influência de Salomão/Jesus).
        - Cena 4: O resgate dos valores sagrados (família, igualdade e amigos leais).
        - Cena 5: A coragem e o espírito valente de agir e superar desafios (Poder da Ação).
        - Cena 6: O desapego das ilusões materiais e a rejeição da arrogância/autoajuda vazia.
        - Cena 7: A reconexão com a verdadeira essência, amor e liberdade de viver com propósito.
        - Cena 8: A frase final de impacto: nobre, inspiradora e inesquecível.
        - Cena 9 (Slide Final - CTA Imponente): Um convite sutil, nobre e alinhado para acompanhar a jornada da sabedoria no perfil. NUNCA use jargões de vendas.

        REQUISITO ANTI-REPETIÇÃO: Crie analogias e metáforas 100% inéditas baseadas em elementos reais da vida, da natureza e da jornada humana.

        LEGENDA DO POST:
        - Máximo de 3 linhas de reflexão poética e direta sobre o tema abordado.
        - SEM HASHTAGS.
        - SEM PEDIDO DE COMENTÁRIO OU COMPARTILHAMENTO.

        UNIVERSO VISUAL OBRIGATÓRIO — REELS CONQUISTADOR:
        As queries devem evocar a grandiosidade e sabedoria cibernética em tons de ouro e noite: metrópoles ciberpunk, néon noturno, multidão em movimento nas cidades, arquitetura tecnológica futurista com iluminação dourada nobre, reflexos néon na chuva. NUNCA vídeos genéricos de campo.

        Responda APENAS em formato JSON válido assim:
        {{
          "pexels_queries": [
            "cyberpunk city night neon lights crowd",
            "dark gold futuristic tech architecture",
            "glowing neural network cyber city night"
          ],
          "slides": [
            "Texto da Cena 1",
            "Texto da Cena 2",
            "Texto da Cena 3",
            "Texto da Cena 4",
            "Texto da Cena 5",
            "Texto da Cena 6",
            "Texto da Cena 7",
            "Texto da Cena 8",
            "Texto da Cena 9 (CTA Imponente)"
          ],
          "legenda": "Sua legenda aqui"
        }}
        """

    elif tipo == "pexels_story":
        prompt = f"""
        Você é um mestre de storytelling cinematográfico aplicado ao Instagram.
        Sua missão é criar uma história em formato de vídeo B-roll que prenda o espectador do primeiro ao último segundo.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA NARRATIVA MAGNÉTICA em 6 a 8 frases curtas seguindo esta arquitetura OBRIGATÓRIA:

        FRASE 1 — GANCHO DE PARADA DE FEED (OBRIGATÓRIA):
        Esta é a frase mais importante de todo o vídeo. É ela que aparece NA TELA assim que o vídeo começa.
        - REGRA DE OURO: O espectador PRECISA parar de rolar o feed. Use UMA das fórmulas abaixo:
          * Afirmação polêmica: "A maioria das pessoas faz isso completamente errado."
          * Identificação visceral: "Você acorda todo dia repetindo o mesmo erro sem perceber."
          * Pergunta perturbadora: "Sabe qual é a coisa que mais sabota o que você quer?"
          * Contradição inesperada: "Trabalhar mais não é a resposta. E você já sabia disso."
        - Máximo 10 palavras. CURTA, DIRETA, SEM RODEIOS. O choque primeiro, a explicação depois.

        FRASE 2 — APROFUNDAMENTO (sustenta o gancho):
        - Aprofunde a provocação da frase 1. Cria o loop de curiosidade — a pessoa precisa continuar assistindo.
        - Máximo 10 palavras.

        FASE 2 — ABERTURA DE POSSIBILIDADES (frases 3-4):
        - Expanda o universo. Mostre que existe um caminho, um padrão, uma verdade oculta.
        - Crie o "loop aberto" — o espectador precisa continuar assistindo para fechar o raciocínio.
        - Dica prática REAL que o espectador pode aplicar hoje. Algo concreto, não filosófico vago.

        FASE 3 — CHOQUE E VALIDAÇÃO (frases 5-6):
        - Bata na ferida com uma verdade difícil que destrói a desculpa favorita do espectador.
        - Imediatamente depois, ELEVE: elogie a inteligência de quem chegou até aqui.
        - Faça-o sentir que pertence a um grupo especial de pessoas que "entendem".

        FASE 4 — FECHAMENTO E CTA PREMIUM (frases 7-8):
        - Frase 7: Feche com uma frase que o espectador vai querer guardar mentalmente. Plante a semente do retorno: uma ideia inacabada, uma pergunta que ele vai continuar pensando.
        - Frase 8 (Slide Final - CTA Charmosa): Crie uma chamada para ação (CTA) altamente sedutora e sutil de acordo com o tema, convidando o espectador a comentar ou seguir de forma elegante.
        
        Exemplos de tom para a Frase 8 (use estas estruturas como inspiração para criar uma frase única conectada ao post):
        * "Deixe sua percepção nos comentários. E se você busca respostas reais, siga a página."
        * "Se você leu até aqui, comente o que pensa e acompanhe nossa jornada."
        * "Deixe sua resposta abaixo. Siga para não perder as próximas reflexões."
        * "A discussão continua nos comentários. Siga para evoluir junto conosco."

        PEXELS QUERY: Escolha um clima visual que CASE com a emoção da história.
        - Use buscas em inglês evocativas: dark moody reading, lonely city rain, candlelight silence, foggy mountain path.
        
        LEGENDA:
        - Máximo 3 linhas. Tom próximo e pessoal, como uma mensagem de voz transcrita.
        - CTA OBRIGATÓRIO: A legenda DEVE obrigatoriamente terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NUNCA termine com uma mensagem positiva e fechada. Sempre com uma pergunta que exija resposta.
        - NÃO inclua hashtags.

        UNIVERSO VISUAL OBRIGATÓRIO — PEXELS STORY MANHÃ:
        As queries devem evocar luz natural, espaços abertos, natureza ao amanhecer, calma e esperança: parques, rios, campos, trilhas, flores, luz solar. NUNCA ambientes noturnos ou interiores fechados.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 6 a 8 frases):
        {{
          "slides": [
            "Frase 1 aqui (Gancho)",
            "Frase 2 aqui",
            "Frase 3 aqui",
            "Frase 4 aqui",
            "Frase 5 aqui",
            "Frase 6 aqui",
            "Frase 7 aqui (Xeque-mate)",
            "Frase 8 aqui (CTA Charmosa)"
          ],
          "pexels_queries": [
            "golden sunrise meadow mist peaceful",
            "person walking forest trail morning light",
            "calm river reflection nature tranquil"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_noite":
        prompt = f"""
        Você é um contador de histórias que entende que o final do dia é o momento mais emocional da jornada humana.
        O seu Reels é o último do dia. A pessoa está voltando para casa ou já está deitada na cama.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        CRIE UMA SEQUÊNCIA NARRATIVA DINÂMICA DE 8 A 12 SLIDES (o número exato deve flutuar livremente entre 8 e 12 a cada execução dependendo da necessidade da história) que funcione como o CAPÍTULO FINAL de uma história que começou de manhã.
        A mensagem deve colocar quem assiste dentro da história: identifique a dor, gere empatia real e ofereça a solução.

        - Slide 1: A Dor e Empatia da Noite (A Fisgada da Noite) — Comece espelhando uma dor silenciosa ou solidão que bate forte ao deitar.
        - Slides 2 a 4: Diagnóstico íntimo do que acontece na mente da pessoa à noite (o ciclo de pensamentos destrutivos ou insônia mental).
        - Slides 5 a 8: A virada de perspectiva e a solução (o que mudou na sua atitude ou o método prático que quebrou esse ciclo de autossabotagem).
        - Slides 9 a 11: A promessa e o benefício do amanhã (como acordar diferente a partir de hoje se ele tomar a atitude proposta).
        - Slide Final: Fusão de Xeque-mate com convite sutil para seguir. Crie uma frase curta e profunda que encerre a história da noite e convide elegantemente o leitor a acompanhar a página para evoluir a cada dia (ex: "O caminho é longo. Siga o perfil para não caminhar sozinho.").

        REGRAS DE RITMO VISUAL:
        * Misture o comprimento das frases! Algumas devem ser curtas e diretas (ex: 4 a 8 palavras) para dinâmica rápida. Outras devem ser um pouco mais detalhadas e íntimas (até 25 palavras) para dar profundidade à conversa de travesseiro.
        * LIMITE MÁXIMO ESTRITO: Nenhuma frase pode passar de 25 palavras sob hipótese alguma.
        * NÃO use pontos de exclamação.

        LEGENDA:
        - Máximo 3 linhas. Tom íntimo, persuasivo e introspectivo.
        - CTA OBRIGATÓRIO: A legenda DEVE obrigatoriamente terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim:
        {{
          "slides": [
            "Frase do slide 1 (Gancho reflexivo e íntimo)",
            "Frase do slide 2 (Sentimento comum ao deitar)",
            "Frase do slide 3 (Um pouco mais longa detalhando o conflito mental da noite)",
            "Frase do slide 4 (Frase curta de impacto)",
            "Frase do slide 5 (Revelação da atitude ou técnica para quebrar a dor)",
            "Frase do slide 6 (Detalhe da solução prática)",
            "Frase do slide 7 (Elogio a busca por crescimento do leitor)",
            "Frase do slide 8 (Xeque-mate reflexivo final + convite sutil para seguir)"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "pexels_story_noite":
        prompt = f"""
        Você é um contador de histórias noturno, um roteirista que transforma experiências humanas comuns em micro-fábulas visuais que conectam profundamente antes de dormir.
        O público está deitado, com o celular na mão, em modo emocional aberto. Essa é a janela mais receptiva do dia.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}

        ===== MISSÃO: CRIAR UMA HISTÓRIA NOTURNA EM FORMATO STORYTELLING =====
        NÃO escreva reflexões filosóficas soltas. NÃO dê conselhos diretos.
        ESCREVA UMA HISTÓRIA CURTA — com personagem, cenário, conflito e resolução.
        O espectador DEVE se ver dentro da história. A lição surge naturalmente do desfecho, não é declarada.

        ESTRUTURA NARRATIVA OBRIGATÓRIA (10 a 12 frases curtas):

        ATO 1 — O PERSONAGEM E A CENA (frases 1-3):
        - Frase 1 (GANCHO - OBRIGATÓRIO): Apresente o personagem em uma situação noturna concreta e específica que o espectador reconhece.
          Não um conselho. Uma imagem cinematic: onde ele está, o que ele está fazendo ou sentindo à noite.
          Exemplo de tom: "Ela desligou o notebook às 23h. Mais um dia que não era o dia certo."
          Máximo 12 palavras. Cena real, específica, visceral.
        - Frase 2: Aprofunde o estado interno do personagem. O que ele sente, o que ele pensa antes de dormir.
        - Frase 3: O ambiente ao redor reflete o estado emocional dele (a luz fraca, o silêncio, o peso do travesseiro).

        ATO 2 — O CONFLITO / PONTO DE RUPTURA (frases 4-6):
        - Frase 4: O pensamento que invade a mente e não sai. A dor que o acompanha toda noite.
        - Frase 5: O momento em que o personagem percebe que algo precisa mudar. Ainda não sabe o quê.
        - Frase 6: A decisão errada que ele sempre toma nesse ponto (evitar, distrair, adiar). O leitor se reconhece aqui.

        ATO 3 — A DESCOBERTA / VIRADA (frases 7-9):
        - Frase 7: O personagem encontra (ou se lembra de) uma lição, um ensinamento ou uma mudança de perspectiva.
          Essa lição DEVE vir diretamente dos livros ou do ângulo do tema do dia. Não invente. Use a sabedoria dos livros.
        - Frase 8: O efeito dessa descoberta nele. Como a carga diminui. A respiração muda. A mente aquieta.
        - Frase 9: A resolução interna. Não é a solução do problema externo, mas uma paz ou clareza que ele encontra dentro de si.

        ATO 4 — O AMANHÃ E O CTA (frases 10-12):
        - Frase 10: A promessa do amanhã. Como ele vai acordar diferente porque teve essa percepção agora.
        - Frase 11 (Slide Final - CTA Charmoso): Crie uma chamada para ação (CTA) integrada ao tom da história, convidando a comentar ou seguir.

        Exemplos de tom para o Slide Final (crie uma frase única conectada à história do post, não copie):
        * "Se essa história te tocou, deixe nos comentários. Siga para a próxima."
        * "Você já se viu nesse personagem? Comente abaixo. E acompanhe amanhã."
        * "A jornada continua. Siga o perfil para não perder o próximo capítulo."

        REGRAS ABSOLUTAS DE RITMO:
        - Máximo de 12 palavras por frase. Frases curtas constroem tensão.
        - Misture frases muito curtas (4 palavras) com frases médias (12 palavras) para criar ritmo cinematográfico.
        - NÃO use ponto de exclamação.
        - NÃO declare a moral da história. Deixe ela emergir do desfecho.
        - NÃO use "você deve" ou "você precisa". Mostre através do personagem.

        PEXELS QUERY: Escolha imagens que criem uma atmosfera de aconchego e introspecção noturna com tons quentes.
        - Use buscas em inglês evocativas: warm candlelight bedroom, cozy night lamp reading, amber light window rain, golden hour sunset silhouette, fireplace warm glow night.

        LEGENDA:
        - Máximo 3 linhas. Tom de quem está te contando algo íntimo, como um amigo numa conversa de madrugada.
        - CTA OBRIGATÓRIO: A legenda DEVE obrigatoriamente terminar com a chamada para ação (CTA) adaptada conforme a 'DIRETRIZ OBRIGATÓRIA DE CTA' enviada nas instruções.
        - NÃO inclua hashtags.

        UNIVERSO VISUAL OBRIGATÓRIO — PEXELS STORY NOITE:
        As queries devem evocar aconchego, introspecção noturna, ambientes internos quentes: velas, lareira, chuva na janela, luzes âmbar, lâmpada vintage, city lights noturnos. NUNCA natureza aberta diurna.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 10 a 12 frases):
        {{
          "slides": [
            "Frase 1 aqui (Cena de abertura - o personagem)",
            "Frase 2 aqui (Estado interno)",
            "Frase 3 aqui (O ambiente)",
            "Frase 4 aqui (O conflito interno)",
            "Frase 5 aqui (A percepção de que algo precisa mudar)",
            "Frase 6 aqui (A decisão errada habitual)",
            "Frase 7 aqui (A descoberta / lição dos livros)",
            "Frase 8 aqui (O efeito da descoberta)",
            "Frase 9 aqui (A resolução interna / paz)",
            "Frase 10 aqui (A promessa do amanhã)",
            "Frase 11 aqui (CTA Charmoso integrado à história)"
          ],
          "pexels_queries": [
            "warm candlelight bedroom cozy night",
            "rain window city lights amber glow",
            "fireplace intimate evening interior warm"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """

    elif tipo == "reels_leads":
        resumo_pdf = ler_resumo_ultimo_pdf() or "Nenhum PDF anterior encontrado. Crie um roteiro genérico focando em 'Hábitos Inquebráveis'."
        evitar_repeticao_leads = buscar_historico_reels_leads(limite=6)
        if evitar_repeticao_leads:
            logger.info("📚 Histórico de reels_leads carregado para anti-repetição.")
        
        # Puxa dados isolados para enriquecer a instrução direta no prompt
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

        prompt = f"""
        Você é um mentor de desenvolvimento pessoal e contador de histórias focado em gerar conexão profunda, confiança e atração de leads.
        Sua missão é criar um vídeo longo (2:30 a 3:00) focado em capturar leads através da entrega de um material prático em PDF 100% gratuito.
        O roteiro usará a Técnica Psicológica do Usopp (10 fases), mas com uma pegada sinestésica e emocional guiada pelas variáveis do dia.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}{instrucoes_livros}
        {evitar_repeticao_leads}

        ==== CONTEÚDO BASE PARA O VÍDEO (EXTRAÍDO DO ÚLTIMO PDF GERADO) ====
        {resumo_pdf}
        ======================================================================
        
        INSTRUÇÃO CRUCIAL:
        1. O vídeo inteiro funciona estritamente como um "trailer cinematográfico e magnético" para o PDF gerado. O título do PDF é "{titulo_pdf_limpo}" e a solução principal é "{solucao_pdf_limpo}".
        2. O gancho inicial (Fase 1) DEVE atacar de forma visceral a dor/problema citada no resumo, usando a estrutura do gancho sorteado para hoje.
        3. FASE 9 (Desejo) e FASE 10 (Convite e CTA) DEVEM se conectar de forma cirúrgica com a transformação e a promessa do PDF, de forma leve, focando em ajuda real, sem parecer anúncio de vendas.
        4. O CTA deve deixar claro que preparamos um material exclusivo e gratuito para ajudar no passo a passo completo discutido no vídeo, direcionando o usuário de forma elegante para o link na bio.


        CRIE UM ROTEIRO LONGO COM 25 A 35 SLIDES seguindo OBRIGATORIAMENTE este funil de 10 Fases:

        FASE 1 — INTERRUPÇÃO DO PADRÃO (Pattern Interrupt) - Slides 1 a 3:
        Abra o Slide 1 e 2 usando a ESTRUTURA DO GANCHO DE REFERÊNCIA de hoje: "{gancho}" (formato: {descricao_categoria}).
        Adapte a estrutura do gancho ao assunto do PDF de hoje de forma impactante, natural e provocativa para parar o scroll. Não ofereça nada ainda.

        FASE 2 — CURIOSIDADE (Curiosity Gap) - Slides 4 a 6:
        Crie tensão e deixe perguntas sem resposta. Aumente o mistério. O leitor precisa querer ver os próximos slides.

        FASE 3 — AUMENTO DA TENSÃO - Slides 7 a 9:
        Não entregue a resposta cedo. Aumente a expectativa. A dor começa a se formar.

        FASE 4 — CRIAÇÃO DO PROBLEMA - Slides 10 a 12:
        Mostre a dor oculta e profunda da audiência. Eles não sabiam que precisavam de algo, agora precisam.
        INTRUÇÃO EMOCIONAL: Construa essa dor baseando-se fortemente no SENTIMENTO DO DIA sorteado: "{sentimento_escolhido}". Descreva a angústia ou o erro habitual sob a ótica desse sentimento.

        FASE 5 — SOLUÇÃO - Slides 13 a 15:
        Apresente a ideia da solução no momento de maior tensão. O alívio imediato.

        FASE 6 — DEMONSTRAÇÃO - Slides 16 a 18:
        Demonstre visualmente (em palavras) como essa solução age na vida prática. Elimine objeções.

        FASE 7 — AUTORIDADE - Slides 19 a 21:
        Explique o porquê de funcionar. Só explique depois de demonstrar. Seja o especialista/mentor.

        FASE 8 — PROVA SOCIAL - Slides 22 a 24:
        Mostre que pessoas normais estão alcançando resultados. Reduza o risco e o medo da mudança.

        FASE 9 — DESEJO - Slides 25 a 27:
        Foque na transformação de vida. A pessoa não quer um arquivo PDF, ela quer a paz ou o resultado prático que ele traz.

        FASE 10 — CONVITE E CTA - EXATAMENTE NOS 2 ÚLTIMOS SLIDES DO ARRAY (Slides N-1 e N):
        REGRAS RIGOROSAS E INVIOLÁVEIS DO CONVITE:
        1. PROIBIÇÃO ABSOLUTA DE REPETIÇÃO: Nos slides de 1 até o antepenúltimo, é ESTRITAMENTE PROIBIDO mencionar palavras como 'link', 'bio', 'material', 'acessar', 'PDF', 'guia' ou fazer qualquer convite antecipado. Todo o miolo do vídeo deve ser 100% conteúdo e história.
        2. A FASE 10 DEVE TER EXATAMENTE 2 SLIDES NO FINAL:
           - PENÚLTIMO SLIDE (Entrega de Valor - 1 slide): Fale como um palestrante generoso entregando uma ferramenta prática (ex: "Estruturei um plano de ação simples para você aplicar isso na sua rotina."). NUNCA use termos comerciais como "baixe o PDF", "manual", "pegue seu arquivo".
           - ÚLTIMO SLIDE (Convite Único ao Perfil - 1 slide): Faça um ÚNICO convite elegante e autoral direcionando para o topo do perfil (ex: "O caminho completo te espera no link principal do meu perfil."). É PROIBIDO repetir a palavra 'link' ou 'bio' mais de uma única vez no vídeo inteiro.


        PEXELS QUERY: Escolha buscas em inglês que criem uma atmosfera cinematográfica de acordo com o sentimento do dia "{sentimento_escolhido}". Ex: 'cinematic mysterious city', 'dark elegant texture', 'warm candlelight'.
        
        LEGENDA:
        - Máximo 3 linhas. Focada em empatia e conexão emocional com a dor debatida.
        - CTA OBRIGATÓRIO NA LEGENDA: Crie uma frase sutil convidando para acessar o Link na Bio de forma amigável (ex: "Se você quer dar o próximo passo, o link para acessar o material completo está na bio. Fique à vontade para ler.").
        - NÃO inclua hashtags.

        UNIVERSO VISUAL OBRIGATÓRIO — REELS LEADS:
        As queries devem evocar aprendizado, foco, profissionalismo e crescimento pessoal: pessoa lendo, escrevendo, estudando, café na mesa, livros, cadernos, janela com luz natural, escritório clean. NUNCA natureza épica ou ambiente noturno.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 25 a 35 frases curtas):
        {{
          "slides": [
            "Texto da Cena 1 (Gancho adaptado)",
            "Texto da Cena 2",
            "Texto da Cena 3",
            "..."
          ],
          "pexels_queries": [
            "person writing notebook focused desk",
            "open books library warm light study",
            "professional coffee window morning calm"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
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

