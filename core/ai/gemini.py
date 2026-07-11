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
from core.design.gerador_prompts import gerar_prompt_cinematografico
from loguru import logger

def gerar_conteudo_gemini(tipo):
    if tipo == "test":
        logger.info("Gerando conteudo de teste estatico...")
        prompt_visual = gerar_prompt_cinematografico("espiritualidade")
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
    else:
        # NOVO FLUXO: Ciclo sequencial diário
        recomendacoes_file = "analytics/dados/recomendacoes.json"
        recomendacoes_semanais_file = "analytics/dados/recomendacoes_semanais.json"
        
        # Lê o contexto do analytics cruzado (diário/múltiplos períodos)
        try:
            if os.path.exists(recomendacoes_file):
                with open(recomendacoes_file, "r", encoding="utf-8") as f:
                    rec_cruzada = json.load(f)
                contexto_analytics += rec_cruzada.get("contexto_para_gemini", "") + "\n\n"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao ler contexto do analytics cruzado: {e}")
            
        # Lê o contexto do analytics semanal (tendências)
        try:
            if os.path.exists(recomendacoes_semanais_file):
                with open(recomendacoes_semanais_file, "r", encoding="utf-8") as f:
                    rec_semanal = json.load(f)
                contexto_analytics += rec_semanal.get("contexto_para_gemini", "") + "\n\n"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao ler contexto do analytics semanal: {e}")
            
        # [NOVO] Adiciona a visão externa (Olhos da Rede)
        try:
            # Pega o nome do tema escolhido para fazer uma busca cirúrgica no YouTube
            nome_do_tema_atual = TEMAS_MAPEADOS[tema_escolhido]['nome'] if tema_escolhido in TEMAS_MAPEADOS else None
            mundo_real = gerar_contexto_mundo_real(dias=7, tema_especifico=nome_do_tema_atual)
            if mundo_real:
                contexto_analytics += "\n====================\n" + mundo_real + "\n====================\n\n"
        except Exception as e:
            logger.warning(f"⚠️ Erro ao coletar Olhos da Rede: {e}")

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
        
    detalhes_tema = TEMAS_MAPEADOS[tema_escolhido]
    logger.info(f"✨ Tema que guiará o bot hoje: {detalhes_tema['nome']}")
    
    # ---------------- ANTI-REPETIÇÃO ----------------
    hist_angulos = estado.get("historico_angulos", [])
    hist_ganchos = estado.get("historico_ganchos", [])
    hist_estilos = estado.get("historico_estilos", [])

    # Monta instrucoes de copy (com anti-repetição)
    instrucoes_copy, sub_angulo, gancho = montar_instrucoes_copy(
        detalhes_tema, contexto_analytics, hist_angulos, hist_ganchos, is_conquistador=is_conquistador
    )

    # Estilo de abordagem sorteado (com anti-repetição)
    estilo_escolhido = sortear_estilo(hist_estilos)
    logger.info(f"🎭 Estilo de abordagem sorteado: {estilo_escolhido.split(':')[0].upper()}")
    
    # Atualiza as listas (mantém os últimos 5 para não lotar o arquivo)
    hist_angulos.append(sub_angulo)
    hist_ganchos.append(gancho)
    hist_estilos.append(estilo_escolhido)
    
    estado["historico_angulos"] = hist_angulos[-5:]
    estado["historico_ganchos"] = hist_ganchos[-5:]
    estado["historico_estilos"] = hist_estilos[-5:]
    salvar_estado(estado)
    # ------------------------------------------------


    if tipo == "story":
        prompt = f"""
        Você cria Stories de Instagram que fazem as pessoas pararem de rolar o feed.
        Estilo obrigatório para este story: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA FRASE CURTÍSSIMA E PODEROSA:
        - Máximo de 10 palavras.
        - Deve funcionar como um soco no estômago ou uma pergunta que incomoda.
        - Formatos que funcionam bem em Stories:
          → Uma afirmação ousada que a maioria discorda na superfície mas concorda no fundo.
          → Uma pergunta que o leitor nunca se fez mas deveria.
          → Uma verdade dita de um jeito que parece errado mas faz sentido.
        - NÃO use ponto de exclamação. Frases com ponto final ou interrogação têm mais peso.

        Responda APENAS em formato JSON válido assim:
        {{
          "frase": "Sua frase para o story aqui"
        }}
        """
    elif tipo == "story_manha":
        prompt = f"""
        Você cria uma sequência de Stories de Instagram matinais para reflexão profunda.
        Estilo obrigatório para esta sequência: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA SEQUÊNCIA DE 3 OU 4 FRASES CURTAS CONECTADAS:
        - Cada frase será um slide diferente, então elas devem formar uma linha de raciocínio.
        - Máximo de 12 palavras por frase.
        - Não use ponto de exclamação.
        - Escolha se quer usar música de fundo ou não no story (true ou false) dependendo da intensidade da mensagem.
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": [
            "Frase 1 aqui",
            "Frase 2 aqui",
            "Frase 3 aqui"
          ],
          "usar_musica": true
        }}
        """
    elif tipo == "story_tarde":
        prompt = f"""
        Você cria uma sequência curta de Stories de Instagram para o fim de tarde.
        Estilo obrigatório para esta sequência: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA SEQUÊNCIA DE 2 FRASES CURTAS CONECTADAS:
        - A segunda frase deve complementar ou quebrar a expectativa da primeira de forma surpreendente.
        - Máximo de 12 palavras por frase.
        - Não use ponto de exclamação.
        - Escolha se quer usar música de fundo ou não no story (true ou false) dependendo do impacto da mensagem.
        
        Responda APENAS em formato JSON válido assim:
        {{
          "frase": [
            "Frase 1 aqui",
            "Frase 2 aqui"
          ],
          "usar_musica": false
        }}
        """
    elif tipo == "carousel":
        # Alterna dinamicamente entre 3 e 5 slides a cada execução
        estado = carregar_estado()
        tamanho_atual = 5 if estado.get("ultimo_carousel") == 3 else 3
        estado["ultimo_carousel"] = tamanho_atual
        salvar_estado(estado)

        if tamanho_atual == 3:
            regras_slides = """        2. ESTRUTURA DOS SLIDES DE CONTEÚDO (exatamente 3 slides):
        - Cada slide: frase curtíssima e cirúrgica de no MÁXIMO 12 palavras. Evite rodeios.
        - Slide 1 (Contraste ou Quebra de expectativa): Uma afirmação provocativa que coloca duas ideias opostas em choque.
          * Exemplo: "Nem todo afastamento é perda. Alguns é só livramento."
        - Slide 2 (O Soco de realidade / Insight): Desmonte uma desculpa comum do leitor de forma cortante.
          * Exemplo: "Pra você cobrar o topo, você não pode entregar o mínimo."
        - Slide 3 (A Regra de ouro final): Uma lição crua e madura sobre a vida, sem moralismo barato.
          * Exemplo: "Uma chance muda tudo, se você estiver pronto." """
            formato_slides = '            "Frase do slide 1 (Contraste)",\n            "Frase do slide 2 (Insight)",\n            "Frase do slide 3 (Regra)"'
        else:
            regras_slides = """        2. ESTRUTURA DOS SLIDES DE CONTEÚDO (exatamente 5 slides):
        - Cada slide: frase curtíssima e cirúrgica de no MÁXIMO 12 palavras.
        - Slide 1 (Quebra de expectativa): A verdade incômoda que destrói o senso comum.
        - Slide 2 (O Oposto da mentira): Expõe a ilusão que o leitor usa para se anestesiar.
        - Slide 3 (A Virada de perspectiva): O insight psicológico profundo que muda a regra do jogo.
        - Slide 4 (A Regra prática do topo): A lição de alta performance baseada em contraste.
          * Exemplo: "Pra cobrar de 10 a 10, você não pode ser nove e meio."
        - Slide 5 (O Legado ou Consequência real): Um xeque-mate reflexivo para o leitor digerir silenciosamente. """
            formato_slides = '            "Slide 1 (Verdade incômoda)",\n            "Slide 2 (Ilusão exposta)",\n            "Slide 3 (Virada de perspectiva)",\n            "Slide 4 (Regra prática)",\n            "Slide 5 (Xeque-mate)"'

        prompt = f"""
        Você cria Carrosséis de Instagram com ganchos magnéticos, quebras de expectativas e contrastes polidos.
        Estilo obrigatório para este carrossel: {estilo_escolhido}

        {instrucoes_copy}

        1. TÍTULO DA CAPA (máximo 6 palavras):
        - Deve gerar curiosidade e forçar o clique (gancho de interrupção de padrão).
        - Use formatos que desafiem o leitor ou usem títulos diretos/provocativos:
          * "Vou alugar um triplex na sua cabeça com isso:"
          * "Regra do jogo para você:"
          * "Lição do dia."
          * "O custo invisível de..."
          * "Por que você sabota o seu..."
        - PROIBIDO: títulos com "dicas", "aprenda a", "como fazer", "passos para".

{regras_slides}

        3. LEGENDA:
        - Reforce a provocação do carrossel em 3-4 linhas usando linguagem direta, madura e sem enrolação.
        - CTA OBRIGATÓRIO DE COMENTÁRIO: Sempre termine com uma das estratégias abaixo (escolha a mais adequada para o tema):
          → "Comente 1 se você já viveu isso, ou 2 se ainda está nessa fase."
          → "Você concorda com isso ou acha que é exagero? Comenta aqui embaixo."
          → "Marca alguém que PRECISA ler isso antes de desistir."
          → "Qual foi o slide que mais te pegou? Comenta o número."
        - NUNCA termine com uma conclusão fechada. O leitor deve ter algo a dizer.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim:
        {{
          "titulo": "Título da capa aqui",
          "slides": [
{formato_slides}
          ],
          "legenda": "Sua legenda completa aqui sem hashtags"
        }}
        """
    elif tipo == "reels":
        prompt = f"""
        Você é um especialista em storytelling magnético e neurociência aplicada ao conteúdo digital.
        Seu objetivo é criar um roteiro em slides que faça o usuário PARAR de rolar o feed e assistir até o final.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA SEQUÊNCIA NARRATIVA DE 4 A 6 SLIDES seguindo OBRIGATORIAMENTE esta estrutura:

        SLIDE 1 — QUEBRA DE PADRÃO (Interrupção de Estado - PNL):
        - Comece com algo INESPERADO. Uma contradição, um dado perturbador, ou uma observação que ninguém verbaliza.
        - O leitor deve sentir: "espera, isso não é o que eu esperava."
        - Máximo 10 palavras. Sem explicação ainda — só o choque inicial.

        SLIDE 2 — ABERTURA DE LOOP (Efeito Zeigarnik):
        - Apresente a possibilidade de um "outro lado" que o leitor desconhece.
        - Prometa implicitamente uma sacada prática e real. Não entregue ainda.
        - Máximo 12 palavras. Deve criar curiosidade irresistível para o próximo slide.

        SLIDE 3 — ENTREGA DE VALOR (Dopamina e Recompensa):
        - Dê uma dica ABSURDAMENTE PRÁTICA que o leitor pode aplicar hoje, em 5 minutos.
        - Deve parecer que você entregou um segredo de graça que valeria um curso pago.
        - Máximo 14 palavras.

        SLIDE 4 — CHOQUE DE REALIDADE + VALIDAÇÃO POSITIVA (Ancoragem de Identidade):
        - Primeiro: bata na ferida. Um choque que destrua a desculpa favorita do leitor.
        - Depois IMEDIATAMENTE: elogie a inteligência dele por estar lendo até ali.
        - Faça-o sentir especial, acima da média. Isso cria laço emocional com o seu perfil.
        - Ex: "Quem chega até aqui entende o que a maioria nunca vai perceber."
        - Máximo 16 palavras.

        (OPCIONAL) SLIDE 5 e 6 — Use se a história pedir. Aprofunde a narrativa ou adicione uma virada extra.

        LEGENDA:
        - Máximo 3 linhas. Tom de quem viveu aquilo, não de quem está ensinando.
        - CTA OBRIGATÓRIO DE COMENTÁRIO: Sempre termine com uma pergunta polarizada que force o leitor a tomar partido. Use uma das abaixo como modelo:
          → "Você concorda com isso ou acha que é papo de coach? Deixa aqui embaixo."
          → "Qual desculpa você parou de usar? Me conta nos comentários."
          → "Comente SIM se você já aplicou isso, ou NÃO se ainda tá adiando."
        - NUNCA termine com uma frase bonita e fechada. Sempre com uma pergunta em aberto.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim:
        {{
          "slides": [
            "Slide 1 aqui",
            "Slide 2 aqui",
            "Slide 3 aqui",
            "Slide 4 aqui"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_conquistador":

        prompt = f"""
        Você é um copywriter de elite especializado em VSL (Video Sales Letter) para o Instagram.
        Sua missão é criar um roteiro para um vídeo de 15 segundos que conta uma história completa
        e termina com uma chamada para ação irresistível.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}

        CRIE EXATAMENTE 5 CENAS para o vídeo, seguindo esta estrutura de funil:

        CENA 1 — DOR / PROBLEMA (O Gancho):
        - Use o "Gancho narrativo" das instruções como ponto de partida.
        - Mostre claramente o que o leitor está perdendo, sofrendo ou pagando caro.
        - Faça ele se identificar: "Isso me atrapalha. Isso me custa."
        - Máximo 15 palavras. Direto. Sem enrolação.

        CENA 2 — SOLUÇÃO (A Revelação):
        - Apresente o que resolve a dor de forma direta e prática.
        - Mostre que a solução é aplicável imediatamente.
        - Máximo 12 palavras.

        CENA 3 — BENEFÍCIO / RESULTADO (A Terra Prometida):
        - Deixe explícito o que o leitor GANHA ao agir: poder, tempo, dinheiro, paz, status.
        - Seja concreto. Evite abstrações.
        - Máximo 12 palavras.

        CENA 4 — PROVA / AUTORIDADE (Credibilidade):
        - Demonstre que isso funciona. Use dados, tecnologia, experiência ou lógica poderosa.
        - Ex: "Nossa IA processa mais dados em 1s do que um departamento inteiro."
        - Máximo 12 palavras.

        CENA 5 — CTA FINAL (Ação Imediata Contextual):
        - O CTA DEVE ESTAR CONECTADO COESAMENTE COM A HISTÓRIA. Não jogue um CTA genérico.
        - Se a mensagem for de revelação, peça para seguir: "Se quiser continuar descobrindo a verdade, siga o perfil."
        - Se a mensagem for um método, peça comentário: "Quer o método completo? Comenta 'QUERO'."
        - Máximo 12 palavras. O tom deve ser imperativo e inegociável.

        LEGENDA DO POST (separada das cenas do vídeo):
        - Máximo 3 linhas. Reforce a dor e o CTA.
        - NÃO use hashtags. Apenas ação direta.

        Responda APENAS em formato JSON válido assim:
        {{
          "pexels_query": "3 palavras em INGLÊS para buscar vídeo de fundo inspirador e premium (ex: golden city sunrise)",
          "slides": [
            "Texto da CENA 1 — Dor/Problema",
            "Texto da CENA 2 — Solução",
            "Texto da CENA 3 — Benefício/Resultado",
            "Texto da CENA 4 — Prova/Autoridade",
            "Texto da CENA 5 — CTA Final"
          ],
          "legenda": "Legenda do post com CTA forte sem hashtags"
        }}
        """

    elif tipo == "pexels_story":
        prompt = f"""
        Você é um mestre de storytelling cinematográfico aplicado ao Instagram.
        Sua missão é criar uma história em formato de vídeo B-roll que prenda o espectador do primeiro ao último segundo.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA NARRATIVA MAGNÉTICA em 6 a 8 frases curtas seguindo esta arquitetura OBRIGATÓRIA:

        FASE 1 — GANCHO INICIAL (frases 1-2):
        - Quebre o padrão imediatamente. Uma observação perturbadora, uma cena do cotidiano vista de ângulo diferente.
        - O espectador deve pensar: "isso é diferente de tudo que vi hoje".
        - Cada frase: máximo 10 palavras. Simples, direta, visceral.

        FASE 2 — ABERTURA DE POSSIBILIDADES (frases 3-4):
        - Expanda o universo. Mostre que existe um caminho, um padrão, uma verdade oculta.
        - Crie o "loop aberto" — o espectador precisa continuar assistindo para fechar o raciocínio.
        - Dica prática REAL que o espectador pode aplicar hoje. Algo concreto, não filosófico vago.

        FASE 3 — CHOQUE E VALIDAÇÃO (frases 5-6):
        - Bata na ferida com uma verdade difícil que destrói a desculpa favorita do espectador.
        - Imediatamente depois, ELEVE: elogie a inteligência de quem chegou até aqui.
        - Faça-o sentir que pertence a um grupo especial de pessoas que "entendem".

        FASE 4 — FECHAMENTO QUE GERA RETORNO (frases 7-8):
        - Feche com uma frase que o espectador vai querer guardar mentalmente.
        - Plante a semente do retorno: uma ideia inacabada, uma pergunta que ele vai continuar pensando.
        - Deve criar o desejo instintivo de voltar ao seu perfil amanhã.

        PEXELS QUERY: Escolha um clima visual que CASE com a emoção da história.
        - Use buscas em inglês evocativas: dark moody reading, lonely city rain, candlelight silence, foggy mountain path.
        
        LEGENDA:
        - Máximo 3 linhas. Tom próximo e pessoal, como uma mensagem de voz transcrita.
        - CTA OBRIGATÓRIO DE COMENTÁRIO: Termine com uma pergunta visceral que ataque diretamente a identidade do espectador. Use uma das abaixo como modelo:
          → "O que esse vídeo te fez lembrar? Me fala nos comentários, vou ler todos."
          → "Em qual frase você se viu? Comenta o número."
          → "Você ficou com raiva de alguma parte? Ótimo. Qual foi?"
        - NUNCA termine com uma mensagem positiva e fechada. Sempre com uma pergunta que exija resposta.
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 6 a 8 frases):
        {{
          "slides": [
            "Frase 1 aqui",
            "Frase 2 aqui",
            "Frase 3 aqui",
            "Frase 4 aqui",
            "Frase 5 aqui",
            "Frase 6 aqui"
          ],
          "pexels_query": "your evocative english search here",
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_noite":
        prompt = f"""
        Você é um contador de histórias que entende que o final do dia é o momento mais emocional da jornada humana.
        O seu Reels é o último do dia. A pessoa está voltando para casa ou já está deitada.
        Estilo obrigatório para este Reels: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA SEQUÊNCIA NARRATIVA DE 4 A 6 SLIDES que funcione como o CAPÍTULO FINAL de uma história que começou de manhã.
        A mensagem deve colocar quem assiste dentro da história: identifique a dor, gere empatia real e ofereça a solução.

        SLIDE 1 — A DOR E A EMPATIA (A Fisgada da Noite):
        - Comece espelhando uma dor solitária que bate forte à noite. 
        - O tom deve ser: "Eu já passei por isso à noite, sozinho, e sei exatamente como dói."
        - Coloque o espectador dentro da narrativa. Máximo 10 palavras.

        SLIDE 2 — O FUNDO DO POÇO (A História Continua):
        - Aprofunde o que acontece quando a pessoa cede a essa dor ou medo.
        - Não julgue, apenas narre o cenário que ele conhece muito bem.
        - Máximo 12 palavras.

        SLIDE 3 — A RUPTURA E A SOLUÇÃO (O "Mas eu superei fazendo isso"):
        - Apresente a virada. Mostre o que você (ou quem tem o controle) fez para sair desse ciclo.
        - Entregue o método prático ou a perspectiva que quebra o feitiço da dor.
        - Máximo 12 palavras.

        SLIDE 4 — FECHAMENTO E BENEFÍCIO (A Promessa do Amanhã):
        - Termine com a promessa de como a vida muda quando essa chave vira.
        - Algo que cria expectativa de acordar diferente amanhã.
        - Máximo 10 palavras.

        (OPCIONAL) SLIDE 5 e 6 — Use se a narrativa pedir um desenvolvimento maior da história.

        LEGENDA:
        - Máximo 3 linhas. Tom íntimo e intrusivo.
        - CTA ESTRATÉGICO E SEDUTOR (OBRIGATÓRIO): NUNCA faça perguntas bobas como "Como foi seu dia?". Use CTAs focados em AÇÃO e COMUNIDADE.
        - Modelos obrigatórios (use variações baseadas nisso):
          → "Se isso faz sentido para o momento que você está vivendo, já me segue para continuarmos evoluindo juntos."
          → "Você já passou por isso? Me conte aqui como você superou e ajude quem está lendo a passar por essa noite."
          → "Se você quer que essa realidade mude antes de amanhã, siga a página agora. Informação assim o sistema esconde."
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim:
        {{
          "slides": [
            "Slide 1 aqui",
            "Slide 2 aqui",
            "Slide 3 aqui",
            "Slide 4 aqui"
          ],
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "pexels_story_noite":
        prompt = f"""
        Você é um diretor de cinema que cria micro-documentários noturnos para o Instagram.
        Este é o vídeo B-roll do fim do dia. A pessoa está em modo de descanso, processando o que viveu.
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}

        CRIE UMA NARRATIVA CINEMATOGRÁFICA NOTURNA em 6 a 8 frases que coloque o espectador dentro de uma história de dor e superação.
        O ritmo deve ser: mais lento, mais denso, mais íntimo. Como uma voz que sussurra "eu te entendo, eu também passei por isso".

        FASE 1 — O RECONHECIMENTO DA DOR (frases 1-2):
        - Descreva exatamente o sentimento pesado ou a frustração que bate quando a pessoa deita a cabeça no travesseiro.
        - O espectador deve sentir que você invadiu a mente dele. Empatia visceral.
        - Cada frase: máximo 10 palavras.

        FASE 2 — A PROFUNDIDADE DA HISTÓRIA (frases 3-4):
        - Mostre como manter essa dor vai destruir o futuro dele. 
        - Uma narrativa de "se continuar assim, a vida passa e nada muda".

        FASE 3 — A SOLUÇÃO (frases 5-6):
        - O alívio. "Mas eu descobri que a chave é fazer isso...".
        - Entregue o método ou insight que resolve essa dor oculta da noite.

        FASE 4 — O FECHAMENTO E BENEFÍCIO (frases 7-8):
        - A promessa. Como o amanhã será diferente porque ele aprendeu isso agora.
        - Termine com um soco no estômago que exija uma tomada de posição.

        PEXELS QUERY: Escolha um clima visual noturno e contemplativo.
        - Use buscas em inglês evocativas: night city lights rain, candle flame night silence, dark forest stars, person alone window night, sunset silhouette reflection.

        LEGENDA:
        - Máximo 3 linhas. Tom íntimo e persuasivo.
        - CTA ESTRATÉGICO E SEDUTOR (OBRIGATÓRIO): Focado em envolver e converter.
        - Modelos obrigatórios (use variações baseadas nisso):
          → "Se você quer parar de acordar com o mesmo sentimento de ontem, já me segue para mudar esse jogo."
          → "Você também já sentiu isso à noite? Me conte como você lidou com essa dor e ajude alguém aqui nos comentários."
          → "O algoritmo vai tentar esconder esse perfil de você. Siga agora se quiser continuar recebendo a verdade sem filtro."
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 6 a 8 frases):
        {{
          "slides": [
            "Frase 1 aqui",
            "Frase 2 aqui",
            "Frase 3 aqui",
            "Frase 4 aqui",
            "Frase 5 aqui",
            "Frase 6 aqui"
          ],
          "pexels_query": "your evocative night english search here",
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    elif tipo == "reels_leads":
        resumo_pdf = ler_resumo_ultimo_pdf() or "Nenhum PDF anterior encontrado. Crie um roteiro genérico focando em 'Hábitos Inquebráveis'."
        
        prompt = f"""
        Você é um estrategista de vendas e mestre em copywriting focado em conversão e geração de leads.
        Sua missão é criar um vídeo longo (2:30 a 3:00) focado em capturar leads através da entrega de um "Manual Prático" em PDF 100% gratuito.
        O roteiro usará a Técnica Psicológica do Usopp (10 fases).
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}

        ==== CONTEÚDO BASE PARA O VÍDEO (EXTRAÍDO DO ÚLTIMO PDF GERADO) ====
        {resumo_pdf}
        ======================================================================
        
        INSTRUÇÃO CRUCIAL: O gancho inicial (Fase 1) DEVE atacar diretamente a dor/problema citada no resumo acima. O vídeo inteiro é um "trailer magnético" para as pessoas desejarem desesperadamente baixar este PDF específico para resolverem esse problema.


        CRIE UM ROTEIRO LONGO COM 25 A 35 SLIDES seguindo OBRIGATORIAMENTE este funil de 10 Fases:

        FASE 1 — INTERRUPÇÃO DO PADRÃO (Pattern Interrupt) - Slides 1 a 3:
        Comece com algo impossível de ignorar. Não venda. Não fale do PDF. Choque a audiência.

        FASE 2 — CURIOSIDADE (Curiosity Gap) - Slides 4 a 6:
        Crie tensão e deixe perguntas sem resposta. Aumente o mistério.

        FASE 3 — AUMENTO DA TENSÃO - Slides 7 a 9:
        Não entregue a resposta cedo. Aumente a expectativa. A dor começa a se formar.

        FASE 4 — CRIAÇÃO DO PROBLEMA - Slides 10 a 12:
        Mostre uma dor oculta e profunda da audiência. Eles não sabiam que precisavam de algo, agora precisam.

        FASE 5 — SOLUÇÃO - Slides 13 a 15:
        Apresente a ideia da solução no momento de maior tensão. O alívio imediato.

        FASE 6 — DEMONSTRAÇÃO - Slides 16 a 18:
        Demonstre visualmente (em palavras) como essa solução age na vida prática. Elimine objeções.

        FASE 7 — AUTORIDADE - Slides 19 a 21:
        Explique o porquê de funcionar. Só explique depois de demonstrar. Seja o especialista.

        FASE 8 — PROVA SOCIAL - Slides 22 a 24:
        Mostre que pessoas normais estão alcançando resultados. Reduza o risco e o medo da mudança.

        FASE 9 — DESEJO - Slides 25 a 27:
        Foque na transformação de vida. A pessoa não quer o PDF, ela quer o resultado que o PDF traz.

        FASE 10 — OFERTA E CTA - Últimos Slides:
        Faça a oferta irresistível. É 100% gratuito.
        O CTA deve ter DUAS PARTES obrigatórias, distribuídas nos últimos slides:

        PARTE 1 — ENTREGA DE VALOR (1 slide): Use uma das frases abaixo, escolhendo a palavra que melhor casa com o conteúdo do vídeo:
        - "Eu preparei um guia completo para você."
        - "Eu preparei um método passo a passo para você."
        - "Eu preparei um material exclusivo para você."
        - "Eu preparei uma estratégia pronta para você aplicar."
        - "Eu preparei um plano de ação para você."
        - "Eu preparei um e-book gratuito para você."
        - "Eu preparei uma técnica que poucos conhecem."
        - "Eu preparei um kit completo para você."
        - "Eu preparei um checklist para facilitar sua jornada."
        NUNCA use os termos: "manual prático", "baixe o PDF", "pegue seu guia", "acesse o PDF".

        PARTE 2 — URGÊNCIA E AÇÃO (1 a 2 slides): Após a entrega de valor, adicione a urgência. Use UMA das frases abaixo:
        - "Link na bio. Só essa semana. Vai lá antes que saia do ar."
        - "É gratuito. É só essa semana. O link tá na bio. Vai lá."
        - "Clica no link da bio agora. Depois que a semana acabar, fecha."
        - "Vai no link da bio agora. Esse conteúdo não fica pra sempre."
        - Conecte a ação de acessar com a transformação que a narrativa promoveu.


        PEXELS QUERY: Escolha um clima visual cinematográfico. Ex: 'cinematic mysterious city', 'dark elegant texture'.
        
        LEGENDA:
        - Máximo 3 linhas. Focada na urgência e na escassez (ex: "só essa semana").
        - CTA OBRIGATÓRIO NA LEGENDA: Crie uma frase chamando para acessar o Link na Bio (ex: "Link na bio só essa semana, vai lá garantir o seu antes que saia do ar").
        - NÃO inclua hashtags.

        Responda APENAS em formato JSON válido assim (o array 'slides' DEVE ter de 25 a 35 frases curtas):
        {{
          "slides": [
            "Frase 1 aqui",
            "...",
            "Frase 35 aqui"
          ],
          "pexels_query": "your evocative english search here",
          "legenda": "Sua legenda aqui sem hashtags"
        }}
        """
    else:
        raise ValueError(f"Tipo inválido: {tipo}")

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
                
                # Injeta o prompt cinematografico procedural para a Pollinations
                # (gerado localmente, sem depender de cliches da IA de texto)
                tipos_imagem = ["story", "story_manha", "story_tarde", "carousel", "reels", "reels_noite", "reels_conquistador", "reels_leads", "test"]
                if tipo in tipos_imagem:
                    prompt_visual = gerar_prompt_cinematografico(tema_escolhido or "espiritualidade")
                    dados["prompt_imagem"] = prompt_visual
                    logger.info(f"Cena cinematografica gerada (Gemini): {prompt_visual}")
                
                # Injeta as hashtags específicas do tema na legenda
                if "legenda" in dados:
                    tags = " ".join(detalhes_tema["hashtags"])
                    dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
                    
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
                # Injeta o prompt cinematografico procedural para a Pollinations
                tipos_imagem = ["story", "story_manha", "story_tarde", "carousel", "reels", "reels_noite", "reels_conquistador", "reels_leads", "test"]
                if tipo in tipos_imagem:
                    prompt_visual = gerar_prompt_cinematografico(tema_escolhido or "espiritualidade")
                    dados["prompt_imagem"] = prompt_visual
                    logger.info(f"Cena cinematografica gerada (Groq): {prompt_visual}")
                
                if "legenda" in dados:
                    tags = " ".join(detalhes_tema["hashtags"])
                    dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
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
                # Injeta o prompt cinematografico procedural para a Pollinations
                tipos_imagem = ["story", "story_manha", "story_tarde", "carousel", "reels", "reels_noite", "reels_conquistador", "reels_leads", "test"]
                if tipo in tipos_imagem:
                    prompt_visual = gerar_prompt_cinematografico(tema_escolhido or "espiritualidade")
                    dados["prompt_imagem"] = prompt_visual
                    logger.info(f"Cena cinematografica gerada (OpenRouter): {prompt_visual}")
                
                if "legenda" in dados:
                    tags = " ".join(detalhes_tema["hashtags"])
                    dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
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
                
                # Injeta o prompt cinematografico procedural para a Pollinations
                tipos_imagem = ["story", "story_manha", "story_tarde", "carousel", "reels", "reels_noite", "reels_conquistador", "reels_leads", "test"]
                if tipo in tipos_imagem:
                    prompt_visual = gerar_prompt_cinematografico(tema_escolhido or "espiritualidade")
                    dados["prompt_imagem"] = prompt_visual
                    logger.info(f"Cena cinematografica gerada (Emergencia): {prompt_visual}")
                
                # Injeta as hashtags específicas do tema na legenda se houver legenda
                if "legenda" in dados:
                    tags = " ".join(detalhes_tema["hashtags"])
                    if not any(tag in dados["legenda"] for tag in detalhes_tema["hashtags"]):
                        dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
                
                logger.success(f"🛡️ [SAÍDA DE EMERGÊNCIA] Mensagem de contingência recuperada para Tema: {tema_key.upper()} | Formato: {tipo_key.upper()}")
                return dados, tema_escolhido, estilo_escolhido
                
    except Exception as e_emergencia:
        logger.error(f"❌ Erro grave no sistema de emergência: {e_emergencia}")

    raise ValueError(f"❌ Falha crítica: Todas as {len(GEMINI_KEYS)} chaves do Gemini falharam ou estão sem cota.")

