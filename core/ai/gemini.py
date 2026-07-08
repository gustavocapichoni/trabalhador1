import json
import random
import time
import os
from google import genai
from google.genai import types
from datetime import datetime, timezone

from core.config.settings import GEMINI_KEYS
from core.ai.prompts import TEMAS_MAPEADOS, TEMAS_POR_DIA, montar_instrucoes_copy
from core.ai.styles import sortear_estilo
from core.config.state import carregar_estado, salvar_estado
from loguru import logger

def gerar_conteudo_gemini(tipo):
    if tipo == "test":
        logger.info("🤖 Gerando conteúdo de teste estático...")
        return {
            "frase": "Seja forte e corajoso. Não se apavore nem desanime, pois o Senhor, o seu Deus, estará com você por onde você andar.",
            "legenda": "Ambiente de automação inicializado com sucesso no GitHub Actions! 🚀\n\nEste é um teste integrado disparado pelo bot para validar as permissões e notificações do sistema.\n\n#bot #instagram #automacao #dev"
        }, "espiritualidade", "teste"
        
    logger.info(f"🤖 Solicitando texto ao Gemini para post do tipo: {tipo.upper()}...")
    if not GEMINI_KEYS:
        raise ValueError("Nenhuma variável GEMINI_API_KEY_X está configurada! Por favor, adicione-as ao arquivo .env ou Secrets.")
        
    # --- INTEGRAÇÃO COM ANALYTICS CRUZADO (ROLETA VICIADA) E CONQUISTADOR ---
    estado = carregar_estado()
    tema_escolhido = None
    contexto_analytics = ""
    
    agora = datetime.now(timezone.utc)
    dia_hoje_str = agora.strftime("%Y-%m-%d")
    dia_da_semana = agora.weekday()

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
        recomendacoes_semanais_file = "core/analytics/dados/recomendacoes_semanais.json"
        
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
            regras_slides = """        2. SLIDES DE CONTEÚDO (exatamente 3 slides):
        - Cada slide: frase de no máximo 10 palavras. Curta e impactante.
        - Slide 1: identifica o problema de um ângulo DIFERENTE do óbvio.
        - Slide 2: a virada — o insight que muda a perspectiva completamente.
        - Slide 3: a consequência real de aplicar (ou ignorar) esse insight."""
            formato_slides = '            "Conteúdo do slide 1 aqui",\n            "Conteúdo do slide 2 aqui",\n            "Conteúdo do slide 3 aqui"'
        else:
            regras_slides = """        2. SLIDES DE CONTEÚDO (exatamente 5 slides):
        - Cada slide: frase de no máximo 10 palavras. Curta e impactante.
        - Slide 1: identifica o problema de um ângulo DIFERENTE do óbvio.
        - Slide 2: a ilusão — a mentira que contamos a nós mesmos.
        - Slide 3: a virada — o insight que muda a perspectiva completamente.
        - Slide 4: a prática — o que muda no dia a dia com esse insight.
        - Slide 5: a consequência real de aplicar (ou ignorar) esse insight."""
            formato_slides = '            "Conteúdo do slide 1 aqui",\n            "Conteúdo do slide 2 aqui",\n            "Conteúdo do slide 3 aqui",\n            "Conteúdo do slide 4 aqui",\n            "Conteúdo do slide 5 aqui"'

        prompt = f"""
        Você cria Carrosséis de Instagram que as pessoas salvam e mandam para amigos.
        Estilo obrigatório para este carrossel: {estilo_escolhido}

        {instrucoes_copy}

        1. TÍTULO DA CAPA (máximo 7 palavras):
        - Deve gerar curiosidade imediata ou provocar discordância.
        - Formatos que funcionam: "O que ninguém te conta sobre...", "Por que você ainda...",
          "Pare de acreditar que...", "A diferença entre quem... e quem...", "Isso que você chama de X é na verdade Y"
        - PROIBIDO: títulos com "5 dicas", "aprenda a", "como ser melhor".

{regras_slides}

        3. LEGENDA:
        - Reforce a provocação do carrossel em 3-4 linhas.
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
        # Sorteia um estilo de CTA variado para cada vídeo
        import random as _r
        cta_opcoes = [
            # Foco em Seguidores
            "Siga o perfil. Informação assim ninguém te entrega de graça.",
            "Segue o perfil agora. O sistema não quer que você saiba disso.",
            "Se você quer evoluir mais rápido, siga o perfil.",
            # Foco em Comentários
            "Comenta QUERO abaixo e te mando o próximo passo.",
            "Comente FOGO se você também está nessa jornada.",
            "Deixa sua opinião nos comentários. Você concorda?"
        ]
        cta_escolhido = _r.choice(cta_opcoes)

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

        CENA 5 — CTA FINAL (Ação Imediata):
        - Esta é a cena mais importante. Ela aparece no final do vídeo em DESTAQUE VISUAL.
        - Use EXATAMENTE este CTA sorteado: "{cta_escolhido}"
        - Pode adaptar levemente mas mantenha a essência e a urgência.
        - Máximo 10 palavras.

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
        O tom deve ser: reflexivo, visceral, cinematográfico. Como um monólogo de quem olha para o dia e extrai o ouro.

        SLIDE 1 — DIAGNÓSTICO DO DIA (Espelho da Realidade):
        - Comece com uma observação sobre o dia que acabou. Algo que a maioria evita admitir.
        - O leitor deve sentir: "é exatamente isso que aconteceu comigo hoje."
        - Máximo 10 palavras. Pesado, honesto, sem filtro.

        SLIDE 2 — A VIRADA QUE NINGUÉM FALA (O insight da noite):
        - A sacada que só aparece quando a pressa do dia acaba.
        - Apresente a perspectiva que muda tudo — a interpretação alternativa do que ele viveu.
        - Máximo 12 palavras. Deve criar aquele silêncio mental de "nunca tinha pensado assim."

        SLIDE 3 — O QUE LEVAR PARA AMANHÃ (Ancoragem de Identidade):
        - Uma instrução prática e emocional para a manhã seguinte.
        - Não é conselho barato. É uma promessa que o leitor faz para si mesmo.
        - Máximo 12 palavras.

        SLIDE 4 — FECHAMENTO PODEROSO (Plantio de Retorno):
        - Termine com uma frase que ele vai dormir pensando.
        - Algo que cria expectativa de acordar diferente amanhã.
        - Não é motivacional clichê. É uma verdade que fica.
        - Máximo 10 palavras.

        (OPCIONAL) SLIDE 5 e 6 — Use se a narrativa pedir um desenvolvimento maior.

        LEGENDA:
        - Máximo 3 linhas. Tom de quem está sentado no escuro refletindo, não de quem está dando aula.
        - CTA OBRIGATÓRIO DE COMENTÁRIO: Termine com uma pergunta que force o leitor a fazer um balanço do dia:
          → "Como foi o seu dia hoje, de verdade? Comenta embaixo."
          → "Qual parte do dia você perdeu para o medo? Comenta 1 palavra."
          → "Você vai dormir orgulhoso de algo hoje? Me conta."
        - NUNCA termine com motivação positiva e fechada. Sempre com uma pergunta que exija reflexão.
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

        CRIE UMA NARRATIVA CINEMATOGRÁFICA NOTURNA em 6 a 8 frases que funcione como o EPÍLOGO do dia.
        O ritmo deve ser: mais lento, mais denso, mais íntimo. Como uma voz que sussurra, não grita.

        FASE 1 — CENA DE ABERTURA NOTURNA (frases 1-2):
        - Pinte uma cena mental de fim de dia. Algo que a pessoa vê ou sente quando para pela primeira vez.
        - O espectador deve sentir o peso gostoso do dia terminando.
        - Cada frase: máximo 10 palavras. Evocativa, sensorial, cinematográfica.

        FASE 2 — O INVENTÁRIO DA ALMA (frases 3-4):
        - O que ficou? O que passou? O que valeu?
        - Faça o espectador fazer um balanço silencioso do próprio dia sem perceber.
        - Crie o "loop aberto": uma verdade pela metade que só se fecha com reflexão.

        FASE 3 — A ENTREGA FINAL (frases 5-6):
        - Um insight de fechamento. A lição que o dia guardou para o final.
        - Visceral e específico — não pode ser um clichê motivacional.
        - Faça o espectador sentir que aquela frase foi escrita para ele.

        FASE 4 — A SEMENTE DO AMANHÃ (frases 7-8):
        - Termine plantando a semente de um recomeço.
        - Uma frase que ele vai acordar querendo agir.
        - Crie desejo de voltar ao perfil amanhã de manhã.

        PEXELS QUERY: Escolha um clima visual noturno e contemplativo.
        - Use buscas em inglês evocativas: night city lights rain, candle flame night silence, dark forest stars, person alone window night, sunset silhouette reflection.

        LEGENDA:
        - Máximo 3 linhas. Tom íntimo, como uma mensagem que um amigo manda à meia-noite.
        - CTA OBRIGATÓRIO DE COMENTÁRIO: Termine com uma pergunta de balanço noturno:
          → "Qual foi a melhor parte do seu dia? Comenta aqui."
          → "O que você vai fazer diferente amanhã? Me conta."
          → "Em qual frase você se reconheceu? Comenta o número."
        - NUNCA termine com uma mensagem positiva e fechada. Sempre com uma pergunta que convide ao diálogo.
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
        prompt = f"""
        Você é um estrategista de vendas e mestre em copywriting focado em conversão e geração de leads.
        Sua missão é criar um vídeo longo (2:30 a 3:00) focado em capturar leads através da entrega de um "Manual Prático" em PDF 100% gratuito.
        O roteiro usará a Técnica Psicológica do Usopp (10 fases).
        Estilo obrigatório: {estilo_escolhido}

        {instrucoes_copy}

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
        O CTA FINAL DEVE ENVIAR PARA O LINK DA BIO: Crie uma frase persuasiva (pode dividir em 2 slides) que direcione o usuário para clicar no link da Bio.
        - Deixe EXTREMAMENTE claro que estará disponível "SÓ ESSA SEMANA".
        - Deixe claro que o material é totalmente gratuito.
        - Varie os termos (ex: baixe o manual, pegue seu guia, acesse o PDF, veja o material).
        - Conecte a ação de baixar com o resultado/transformação que a pessoa quer ter.

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

    # Adiciona exigência do prompt de imagem para variar as artes do Pollinations
    if tipo in ["story", "story_manha", "story_tarde", "carousel", "reels", "reels_noite"]:
        prompt += """
        IMPORTANTE FINAL: Adicione OBRIGATORIAMENTE no seu JSON de resposta um campo extra chamado "prompt_imagem".
        - O valor deve ter MÁXIMO 15 PALAVRAS EM INGLÊS.
        - Deve descrever uma cena visual fotorealística, premium e cinemática que sirva de fundo para a mensagem.
        - Não coloque pessoas de frente, use silhuetas, paisagens, ambientes místicos ou abstratos ricos.
        - Exemplo: "dark stormy ocean cinematic lightning, premium, highly detailed" ou "mystical ancient ruins glowing light rays, epic".
        """

    # LOOP DE TENTATIVAS (Múltiplas chaves)
    max_tentativas_por_chave = 3
    
    for key_index, current_key in enumerate(GEMINI_KEYS):
        logger.info(f"🔑 Tentando usar chave Gemini {key_index + 1}/{len(GEMINI_KEYS)}...")
        client = genai.Client(api_key=current_key)
        
        for tentativa in range(max_tentativas_por_chave):
            try:
                resposta = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                
                # Extração e parse robusto
                try:
                    dados = extrair_json(resposta.text)
                except Exception as e:
                    logger.error(f"❌ Erro ao parsear JSON na Tentativa {tentativa+1}. Texto bruto: {resposta.text}")
                    raise Exception(f"Gemini não retornou um JSON válido: {e}")
                
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
                    
    # Se sair do loop externo, todas as chaves falharam. Entramos no modo Saída de Emergência!
    logger.warning("🚨 [SAÍDA DE EMERGÊNCIA] Todas as chaves falharam. Carregando post estático de contingência...")
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

