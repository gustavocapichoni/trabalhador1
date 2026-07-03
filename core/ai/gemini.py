import json
import random
import time
import os
from google import genai
from google.genai import types

from core.config.settings import GEMINI_KEYS
from core.ai.prompts import TEMAS_MAPEADOS, TEMAS_POR_DIA, montar_instrucoes_copy
from core.ai.styles import sortear_estilo
from core.config.state import carregar_estado, salvar_estado

def gerar_conteudo_gemini(tipo):
    if tipo == "test":
        print("🤖 Gerando conteúdo de teste estático...")
        return {
            "frase": "Seja forte e corajoso. Não se apavore nem desanime, pois o Senhor, o seu Deus, estará com você por onde você andar.",
            "legenda": "Ambiente de automação inicializado com sucesso no GitHub Actions! 🚀\n\nEste é um teste integrado disparado pelo bot para validar as permissões e notificações do sistema.\n\n#bot #instagram #automacao #dev"
        }, "espiritualidade", "teste"
        
    print(f"🤖 Solicitando texto ao Gemini para post do tipo: {tipo.upper()}...")
    if not GEMINI_KEYS:
        raise ValueError("Nenhuma variável GEMINI_API_KEY_X está configurada! Por favor, adicione-as ao arquivo .env ou Secrets.")
        
    # Lógica de tema diário fixo
    from datetime import datetime, timezone
    dia_hoje_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dia_da_semana = datetime.now(timezone.utc).weekday()
    
    estado = carregar_estado()
    
    if estado.get("data_tema_do_dia") == dia_hoje_str and estado.get("tema_do_dia"):
        tema_escolhido = estado["tema_do_dia"]
    else:
        if dia_da_semana == 6:  # Domingo
            tema_escolhido = random.choice(["superacao", "proposito"])
        else:
            tema_escolhido = TEMAS_POR_DIA[dia_da_semana]
            
        estado["tema_do_dia"] = tema_escolhido
        estado["data_tema_do_dia"] = dia_hoje_str
        salvar_estado(estado)
        
    # --- INTEGRAÇÃO COM ANALYTICS (AUTO-AJUSTE) ---
    contexto_analytics = ""
    try:
        # Prioridade 1: Recomendações semanais (7 dias de dados - mais ricas)
        recomendacoes_semanais_file = "core/analytics/dados/recomendacoes_semanais.json"
        recomendacoes_file = "core/analytics/dados/recomendacoes.json"

        contexto_semanal = ""
        contexto_diario = ""
        rec_semanal = {}
        
        # 1. Lê a visão macro (semanal) - "O bot da semana toca"
        if os.path.exists(recomendacoes_semanais_file):
            # Verifica se o arquivo semanal tem menos de 7 dias de idade
            idade_segundos = time.time() - os.path.getmtime(recomendacoes_semanais_file)
            
            if idade_segundos <= (7 * 24 * 60 * 60):  # 7 dias
                with open(recomendacoes_semanais_file, "r", encoding="utf-8") as f:
                    rec_semanal = json.load(f)
                contexto_semanal = rec_semanal.get("contexto_para_gemini", "")
            else:
                print("⚠️ Analytics semanal tem mais de 7 dias (desatualizado). Ignorando visão macro.")
            
        # 2. Lê a visão micro (diária) - "O bot do dia dança"
        if os.path.exists(recomendacoes_file):
            with open(recomendacoes_file, "r", encoding="utf-8") as f:
                rec_diaria = json.load(f)
            contexto_diario = rec_diaria.get("contexto_para_gemini", "")
            
            # O tema vem do diário (o que performou melhor ontem dita a execução de hoje)
            tema_rec = rec_diaria.get("tema_recomendado")
            if tema_rec and tema_rec in TEMAS_MAPEADOS:
                tema_escolhido = tema_rec
                print(f"📈 Analytics DIÁRIO recomendou o tema para hoje: {tema_escolhido}")
        else:
            # Se não tiver diário, usa o tema do semanal como fallback
            if rec_semanal:
                tema_rec = rec_semanal.get("tema_recomendado")
                if tema_rec and tema_rec in TEMAS_MAPEADOS:
                    tema_escolhido = tema_rec
                    print(f"📈 Analytics SEMANAL recomendou o tema fallback: {tema_escolhido}")

        # Junta os dois contextos:
        partes_contexto = []
        if contexto_semanal:
            partes_contexto.append("ESTRATÉGIA DA SEMANA (Visão Macro):\n" + contexto_semanal)
        if contexto_diario:
            partes_contexto.append("AJUSTE DE HOJE (Visão Micro):\n" + contexto_diario)
            
        contexto_analytics = "\n\n".join(partes_contexto)

    except Exception as e:
        print(f"⚠️ Erro ao ler recomendações do analytics: {e}")
    # ----------------------------------------------
        
    detalhes_tema = TEMAS_MAPEADOS[tema_escolhido]
    print(f"✨ Tema selecionado: {detalhes_tema['nome']} (Fixo para o dia de hoje)")

    # Monta instrucoes de copy via conteudo.py (com sub-ângulo e gancho sorteados)
    instrucoes_copy, sub_angulo = montar_instrucoes_copy(detalhes_tema, contexto_analytics)

    # Estilo de abordagem sorteado do conteudo.py
    estilo_escolhido = sortear_estilo()
    print(f"🎭 Estilo de abordagem sorteado: {estilo_escolhido.split(':')[0].upper()}")


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
    else:
        raise ValueError(f"Tipo inválido: {tipo}")

        
    max_tentativas_por_chave = 3
    
    for key_index, current_key in enumerate(GEMINI_KEYS):
        print(f"🔑 Tentando usar chave Gemini {key_index + 1}/{len(GEMINI_KEYS)}...")
        client = genai.Client(api_key=current_key)
        
        for tentativa in range(max_tentativas_por_chave):
            try:
                resposta = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
                texto_limpo = response_text = resposta.text.replace("```json", "").replace("```", "").strip()
                dados = json.loads(texto_limpo)
                
                # Injeta as hashtags específicas do tema na legenda
                if "legenda" in dados:
                    tags = " ".join(detalhes_tema["hashtags"])
                    dados["legenda"] = f"{dados['legenda'].strip()}\n\n{tags}"
                    
                return dados, tema_escolhido, estilo_escolhido
            except Exception as e:
                err_msg = str(e).lower()
                if "429" in err_msg or "resource_exhausted" in err_msg or "quota" in err_msg:
                    print(f"⚠️ Cota esgotada na chave {key_index + 1} (429). Passando para a próxima chave...")
                    break # Sai do loop de tentativas e vai para a próxima chave
                
                if tentativa < max_tentativas_por_chave - 1:
                    print(f"⚠️ Erro ao chamar Gemini (Chave {key_index + 1}, Tentativa {tentativa+1}/{max_tentativas_por_chave}): {e}. Tentando novamente em 5 segundos...")
                    time.sleep(5)
                else:
                    print(f"❌ Falha ao obter resposta na chave {key_index + 1} após {max_tentativas_por_chave} tentativas.")
                    
    # Se sair do loop externo, todas as chaves falharam
    raise ValueError(f"❌ Falha crítica: Todas as {len(GEMINI_KEYS)} chaves do Gemini falharam ou estão sem cota.")

