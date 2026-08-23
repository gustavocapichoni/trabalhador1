"""
conteudo.py — Gerador de Conteúdo Narrativo via Gemini AI

Recebe o briefing (tema + livro + contexto da semana) e retorna
o conteúdo completo do PDF em formato estruturado.
"""
import os
import json
import sys
import time

BOT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, BOT_PATH)

from google import genai
from google.genai import types
from google.genai import errors
from dotenv import load_dotenv

# Carrega variáveis de ambiente do bot
load_dotenv(os.path.join(BOT_PATH, ".env"))


PROMPT_TEMPLATE = """
Você é um estrategista de conteúdo e escritor da marca "@codigo.da.sabedoria". Sua especialidade é escrever masterclasses em formato de e-book focadas em "SABEDORIA EM AÇÃO" e "Sabedoria que Transforma Destinos".

Sua missão é entregar um e-book de AÇÃO DIRETA, preparando o leitor para um plano prático, consistente e transformador.

BRIEFING DA SEMANA:
- Tema central: {nome_display}
- Livro base de inspiração: "{livro_base}"
- Dor de ancoragem: "{dor_central}"

DADOS DE INTERAÇÃO DO PERFIL (O que mais chamou atenção da audiência recentemente):
{dados_performance_perfil}

CONTEXTO DO MUNDO REAL NESTA SEMANA (TENDÊNCIAS / OLHOS DA REDE):
{contexto_semana}

SUA MISSÃO:
Escreva um E-BOOK DE AÇÃO DIRETA E EXTREMAMENTE PRÁTICA. As pessoas estão saturadas de teoria vazia. O PDF deve entregar uma EXPERIÊNCIA guiada, estruturada em ensinamentos práticos e claros para o dia a dia.

DIRETRIZES DE TÍTULOS E SUBTÍTULOS (MODERNOS E SEM CLICHÊS):
- É TERMINANTEMENTE PROIBIDO usar clichês repetitivos como: "O Protocolo", "O Código de", "A Bússola", "O Mapa da", "O Salto Quântico", "Desbloqueando", "A Chave de".
- Crie títulos provocativos, elegantes, contemporâneos e fortes. Exemplos do estilo desejado:
  * "Como Parar de Ser Refém do Seu Próprio Cérebro"
  * "A Arte Invisível de Vencer em Silêncio"
  * "O Preço Oculto da Hesitação"
  * "A Ciência da Mente Inabalável"
  * "A Decisão que Separa Quem Tenta de Quem Conquista"
- O subtítulo deve ser curto, moderno e focado em benefício prático imediato, sem enrolação.

ESTRUTURA DA NARRATIVA (Obrigatório seguir em cada capítulo):
- Emoção: Provoque uma emoção forte (desconforto com a inércia, desejo de mudança, clareza brutal).
- História: Uma breve ilustração, metáfora ou fato (inspirado no livro base) que ancore a lição.
- Lição Útil Revelada: O ensinamento prático aplicado à vida real. O que fazer HOJE.

DIRETRIZES DE VALOR:
- Tom de voz: Autoridade moral, incisivo, direto, focado em libertar a pessoa da "vida no automático".
- Plano de Ação: O e-book deve culminar em um Plano de Ação prático (pode ser de dias, passos ou regras) que a pessoa consiga aplicar imediatamente. Crie um método dinâmico com base no {livro_base}.

REGRAS DE FORMATAÇÃO DE TEXTO E JSON:
- Use apenas texto simples, pontos e vírgulas.
- É PROIBIDO usar emojis, caracteres especiais, aspas redondas ou travessões longos. Use apenas aspas duplas retas (") e hífens simples (-).
- CRÍTICO: NUNCA use quebras de linha literais (Enter) dentro dos textos do JSON. Escreva tudo na mesma linha contínua.
- REGRA DE IMAGENS: Para a capa, cada capítulo e o plano de ação, crie um "prompt_imagem". Deve ser um descritivo em INGLÊS focado em fotografia hiper-realista, escura, cinematográfica.

ESTRUTURA OBRIGATÓRIA EM JSON (TUDO 100% DINÂMICO):

{{
  "frase_topo_capa": "Uma frase inspiradora e impactante em no máximo 10 palavras para o topo da capa (Ex: A SABEDORIA QUE CONSTRÓI DESTINOS INABALÁVEIS)",
  "titulo_pdf": "Título magnético, moderno e autêntico sem usar clichês",
  "subtitulo_pdf": "Subtítulo direto e elegante de benefício prático",
  "prompt_imagem_capa": "Cinematic dark moody photography of a glowing hourglass in the dark, 8k",
  "capa_cards": [
    {{"titulo": "Crie um título curto e inédito para o card de diagnóstico", "texto": "Escreva aqui o diagnóstico da dor {dor_central} em até 30 palavras — direto e incisivo.", "pergunta_destaque": "Crie uma pergunta que cutuca a ferida do leitor em no máximo 10 palavras."}},
    {{"titulo": "Crie um título curto e inédito para o card do método", "texto": "Descreva o método ou benefício central do livro {livro_base} em até 20 palavras."}},
    {{"titulo": "Crie um título curto e inédito para o card do ritmo ou ganho", "texto": "Qual o ganho concreto que o leitor tem ao aplicar isso? Até 15 palavras."}},
    {{"titulo": "Crie um título curto e inédito para o card da identidade ou princípio", "texto": "Escreva um princípio transformador em até 12 palavras.", "citacao_destaque": "Crie uma citação de até 10 palavras da essência do {livro_base}. Sempre termine com: Código da Sabedoria."}}
  ],
  "capitulos": [
    {{
      "numero": 1,
      "titulo": "Título inédito dinâmico para o Diagnóstico",
      "prompt_imagem": "Cinematic moody dark photography of a tired man looking at a mirror, 8k",
      "paragrafos": [
        "Parágrafo 1 — EMOÇÃO: Toque na dor {dor_central}. Mostre o custo invisível da rotina automática e da falta de clareza mental.",
        "Parágrafo 2 — HISTÓRIA: Conte um breve fato, estudo ou metáfora inspirada no livro {livro_base} sobre alguém que rompeu a inércia.",
        "Parágrafo 3 — LIÇÃO: Ensinamento prático — como identificar o que estava te segurando sem perceber e dar o primeiro passo hoje."
      ]
    }},
    {{
      "numero": 2,
      "titulo": "Título inédito dinâmico para o Controle ou Perspectiva",
      "prompt_imagem": "Cinematic dark moody photography of a glowing book and a sharp sword, 8k",
      "paragrafos": [
        "Parágrafo 1 — EMOÇÃO: A dificuldade de manter o foco e o cérebro que prefere o sofrimento conhecido à mudança.",
        "Parágrafo 2 — HISTÓRIA: Metáfora ou exemplo prático do livro {livro_base} sobre o controle dos próprios impulsos.",
        "Parágrafo 3 — LIÇÃO: Ensinamento prático — A técnica exata para dominar a própria atenção e reprogramar a mentalidade."
      ]
    }},
    {{
      "numero": 3,
      "titulo": "Título inédito dinâmico para Ação e Planejamento",
      "prompt_imagem": "Cinematic dark moody photography of a compass guiding the way in a storm, 8k",
      "paragrafos": [
        "Parágrafo 1 — EMOÇÃO: O sentimento de trabalhar exausto sem nunca sentir que está chegando a algum lugar.",
        "Parágrafo 2 — HISTÓRIA: Um insight poderoso do livro {livro_base} sobre planejamento, antecipação e escolha de metas reais.",
        "Parágrafo 3 — LIÇÃO: Ensinamento prático — Como desenhar um plano à prova de desculpas para a sua semana."
      ]
    }}
  ],
  "citacao_destaque": "Citação impactante do livro {livro_base} sobre ação e sabedoria.",
  "titulo_citacao": "A Regra de Ouro",
  "verso_base": "Um provérbio ou reflexão filosófica/bíblica que ancore a lição prática de sabedoria.",
  "referencia_verso": "Referência (ex: Provérbios ou Filosofia Estoica)",
  "plano_acao": {{
    "titulo_secao": "Crie um título totalmente original para este plano — pode ser um protocolo de qualquer número de dias, regras, pilares, ou o formato que melhor se encaixar no tema {nome_display} e no livro {livro_base}.",
    "prompt_imagem": "Crie um prompt cinematográfico em inglês para a imagem do plano de ação, hiper-realista e dark.",
    "subtitulo": "Crie um subtítulo que explique de forma instigante como executar este método específico.",
    "passos": [
      "ATENÇÃO: Crie entre 3 e 6 passos — o número exato deve ser o que faz mais sentido para o método criado. Cada passo deve ter: numero (inteiro), titulo (inédito e criativo) e descricao (prática e aplicável hoje, baseada em {livro_base})."
    ]
  }},
  "fechamento": "Seus resultados mudam quando suas atitudes mudam. O primeiro passo começa agora.",
  "titulo_fechamento": "SABEDORIA EM AÇÃO",
  "rodape": "Código da Sabedoria — Conhecimento que Transforma Destinos.",
  "landing_page": {{
    "promessa_clara": "Crie uma promessa forte em até 10 palavras (Ex: 10 DIAS PARA ATIVAR O MELHOR DE VOCÊ).",
    "beneficios": [
      "Escreva um benefício prático e instigante em até 15 palavras (Ex: 10 dias e você identifica o que estava te segurando sem perceber).",
      "Escreva um benefício prático e instigante em até 15 palavras.",
      "Escreva um benefício prático e instigante em até 15 palavras.",
      "Escreva um benefício prático e instigante em até 15 palavras.",
      "Escreva um benefício prático e instigante em até 15 palavras."
    ]
  }}
}}

Retorne APENAS o JSON, sem texto antes ou depois.
"""


def gerar_conteudo_pdf(briefing: dict) -> dict:
    print("[Conteudo] Chamando Gemini AI para gerar o conteudo do PDF...")

    import random
    nomes_possiveis = ["Lucas", "Mateus", "Gabriel", "Thiago", "Felipe", "Daniel", "Andre", "Rafael", "Samuel", "Bruno", "Vitor", "Diego", "Guilherme", "Gustavo", "Leonardo"]
    nome_sorteado = random.choice(nomes_possiveis)
    print(f"[Conteudo] Nome do personagem sorteado para esta edicao: {nome_sorteado}")

    prompt = PROMPT_TEMPLATE.format(
        nome_display=briefing["nome_display"],
        livro_base=briefing["livro_base"],
        dor_central=briefing["dor_central"],
        dados_performance_perfil=briefing.get("dados_performance_perfil", "Sem dados recentes."),
        contexto_semana=briefing["contexto_semana"],
        nome_personagem=nome_sorteado
    )

    for num_chave in range(1, 11):
        chave_atual = os.getenv(f"GEMINI_API_KEY_{num_chave}")
        if not chave_atual:
            continue
            
        try:
            print(f"[Conteudo] Tentando gerar conteúdo com GEMINI_API_KEY_{num_chave}...")
            client_atual = genai.Client(api_key=chave_atual)
            
            response = client_atual.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.85,
                    max_output_tokens=8192,
                )
            )

            texto_resposta = response.text.strip()

            if texto_resposta.startswith("```json"):
                texto_resposta = texto_resposta[7:]
            if texto_resposta.startswith("```"):
                texto_resposta = texto_resposta[3:]
            if texto_resposta.endswith("```"):
                texto_resposta = texto_resposta[:-3]

            conteudo = json.loads(texto_resposta.strip())
            print(f"[Conteudo] Conteudo gerado com sucesso! Titulo: '{conteudo.get('titulo_pdf', 'N/A')}'")
            return conteudo

        except Exception as e:
            print(f"⚠️ Falha com GEMINI_API_KEY_{num_chave} (Erro: {str(e)[:100]}). Tentando próxima chave da fila...")
            import time
            time.sleep(2) # Pausa rapida para o Google respirar
            continue
                
    print("🚨 TODAS as chaves da API do Gemini falharam! Acionando SAÍDA DE EMERGÊNCIA (PDF Coringa)...")
    
    # SAÍDA DE EMERGÊNCIA: Retorna um conteúdo estático super profissional
    conteudo_emergencia = {
      "titulo_pdf": "O Domínio da Mente",
      "subtitulo_pdf": "O método para silenciar a autossabotagem e assumir o controle.",
      "prompt_imagem_capa": "Cinematic dark moody photography of a glowing brain structure in deep shadows, highly detailed, 8k",
      "capa_cards": [
        {"titulo": "A Névoa", "texto": "A autossabotagem não chega gritando. Ela sussurra que 'amanhã é um dia melhor'. Ela te convence de que o conforto de hoje vale mais que o orgulho de amanhã. É a prisão mais invisível que existe.", "pergunta_destaque": "Você sente que sua vida está travada nas desculpas de sempre?"},
        {"titulo": "A Solução", "texto": "O domínio não nasce da motivação, mas da clareza inegociável. Quando você decide que a dor da disciplina é menor que a dor do arrependimento, o jogo vira. O método é implacável."},
        {"titulo": "O Propósito", "texto": "Recuperar o poder sobre suas próprias decisões e destruir a procrastinação."},
        {"titulo": "A Verdade", "texto": "Você não tem um problema de tempo. Você tem um problema de prioridade.", "citacao_destaque": "\"Onde colocamos nossa energia, ali floresce o nosso destino.\""}
      ],
      "capitulos": [
        {
          "numero": 1,
          "titulo": "O Peso Invisível",
          "prompt_imagem": "Cinematic dark moody photography of a man carrying a heavy stone in the shadows, 8k",
          "paragrafos": [
            "Existe uma guerra silenciosa acontecendo dentro de você todos os dias. Ela não usa armas de fogo, mas desculpas muito bem articuladas. Quando o despertador toca, quando o projeto exige atenção, quando a mudança precisa acontecer, uma voz interna entra em ação. Ela é persuasiva. Ela conhece suas fraquezas melhor do que ninguém, porque ela é você. E na maioria das vezes, ela vence sem você nem perceber que estava em uma batalha.",
            "Essa voz prospera no conforto. Ela te convence de que não há problema em adiar, de que você merece um descanso, de que amanhã você estará mais preparado. E assim, os dias viram semanas, e as semanas viram anos. O potencial não realizado começa a pesar nos ombros como chumbo. A frustração de saber do que você é capaz, mas ver-se paralisado pela própria mente, é a dor mais silenciosa que existe.",
            "Mas entenda isso: você não está sozinho nessa trincheira. A humanidade inteira luta contra a inércia. Nossos cérebros foram programados evolutivamente para economizar energia e evitar o desconforto. Cada vez que você tenta romper o padrão, seu sistema de defesa entra em alerta máximo. Reconhecer que isso não é uma falha de caráter, mas um mecanismo primitivo, é o primeiro passo para a verdadeira libertação."
          ]
        },
        {
          "numero": 2,
          "titulo": "O Ponto de Ruptura",
          "prompt_imagem": "Cinematic dark moody photography of a cracked mirror reflecting a serious face in the dark, 8k",
          "paragrafos": [
            "A mudança raramente acontece por inspiração; ela costuma nascer do puro e absoluto desconforto. Chega um momento em que a dor de permanecer exatamente onde você está se torna insuportável. É o instante em que você olha no espelho e não reconhece mais a pessoa acomodada do outro lado. Esse é o momento sagrado. O atrito. A faísca que pode incendiar a floresta das suas velhas desculpas.",
            "Nesse momento de clareza, a bifurcação aparece. De um lado, a estrada familiar do 'depois eu faço', pavimentada com justificativas confortáveis. Do outro, o caminho íngreme da disciplina, onde não há aplausos, apenas o som da sua própria respiração ofegante. É a escolha entre a dor momentânea do esforço ou a dor crônica do arrependimento.",
            "E então, você decide. Não com um grito, mas com um sussurro inegociável para si mesmo: 'Chega'. Essa decisão não é motivacional, é estrutural. É o exato segundo em que você para de negociar com a voz da preguiça. Você demite o gerente incompetente da sua mente e assume a diretoria da sua própria vida. A partir daqui, as regras mudam."
          ]
        },
        {
          "numero": 3,
          "titulo": "A Disciplina como Espada",
          "prompt_imagem": "Cinematic dark moody photography of a glowing sword being forged in dark shadows, 8k",
          "paragrafos": [
            "Motivação é um combustível adulterado. Ela te leva até a esquina e te abandona no primeiro obstáculo. A disciplina, por outro lado, é um motor a diesel: pesado para ligar, mas impossível de parar depois que ganha tração. A disciplina não pergunta como você está se sentindo. Ela não se importa se chove lá fora ou se você dormiu mal. Ela simplesmente exige execução.",
            "A grande chave é entender que a disciplina não é uma prisão, é a própria definição de liberdade. Quem não domina a si mesmo será eternamente escravo de seus impulsos e das circunstâncias. Ao forjar hábitos de ferro, você automatiza o sucesso. Você retira o peso da decisão diária e coloca sua mente no piloto automático para o crescimento constante.",
            "Imagine a disciplina como uma espada forjada no fogo do desconforto. Cada vez que você faz o que precisa ser feito, mesmo sem vontade, você dá uma marretada no aço quente, tornando-o mais forte, mais afiado. Com o tempo, essa espada se torna capaz de cortar qualquer adversidade, qualquer desculpa, com a precisão de um mestre."
          ]
        },
        {
          "numero": 4,
          "titulo": "A Forja do Hábito",
          "prompt_imagem": "Cinematic dark moody photography of an anvil and hammer in the dark with sparks, 8k",
          "paragrafos": [
            "Não subestime o poder repulsivo da sua velha rotina. Quando você começa a implementar a nova ordem, o sistema reage com força total. Os primeiros dias são marcados por um entusiasmo ingênuo, mas logo o atrito se apresenta. A cama parece mais macia, as distrações parecem mais urgentes. Esse é o vale da sombra da morte da mudança de hábito. É aqui que 99% das pessoas desistem e voltam para o começo.",
            "Mas você não. Você sabe que o atrito é apenas o som da fraqueza abandonando seu corpo. Você se concentra na execução do micro-hábito. Não importa o quão pequeno seja o passo, importa que ele seja dado. A consistência é muito mais poderosa do que a intensidade. Uma gota d'água cavando uma rocha não precisa de força, precisa apenas de tempo e de uma direção imutável.",
            "E então, acontece. A primeira pequena vitória. Aquele dia em que você fez sem precisar se forçar tanto. O circuito neural começa a se fortalecer, o caminho de terra vira asfalto. A identidade começa a mudar. Você deixa de ser alguém que 'está tentando ser disciplinado' e passa a ser, intrinsecamente, uma pessoa inegociável com seus próprios padrões."
          ]
        },
        {
          "numero": 5,
          "titulo": "O Horizonte Silencioso",
          "prompt_imagem": "Cinematic dark moody photography of a man looking out of a window at a dark vast ocean, 8k",
          "paragrafos": [
            "Os anos passam. A guerra diária já não é mais exaustiva; tornou-se o seu habitat natural. A voz que antes gritava desculpas, agora apenas sussurra de vez em quando, sendo rapidamente silenciada pela autoridade das suas ações. O novo padrão não é mais algo que você faz, é quem você é. A estrutura de hábitos de ferro sustenta a sua vida como as fundações de um arranha-céu.",
            "Existe uma paz profunda que nasce do dever cumprido. Quando você encosta a cabeça no travesseiro à noite, não há sussurros de arrependimento, apenas o silêncio confortável de quem deixou tudo no campo de batalha. O contraste entre a sua versão antiga e a atual é tão abismal que você tem dificuldade de reconhecer quem costumava ser.",
            "A verdadeira transformação não está no destino final, mas em quem você se tornou durante a jornada. A disciplina te entregou a chave mestra da sua própria existência. E agora, com a mente silenciosa e o controle absoluto das suas ações, não há meta distante demais, nem objetivo grande demais. O jogo apenas começou."
          ]
        }
      ],
      "citacao_destaque": "Sofra a dor da disciplina ou sofra a dor do arrependimento. A diferença é que a disciplina pesa gramas, enquanto o arrependimento pesa toneladas.",
      "plano_acao": {
        "titulo_secao": "Plano de Ação",
        "prompt_imagem": "Cinematic dark moody photography of a glowing notebook and pen on a dark desk, 8k",
        "subtitulo": "Domínio Prático.",
        "passos": [
          {"numero": 1, "titulo": "A Regra dos 5 Minutos", "descricao": "Comprometa-se a fazer a tarefa difícil por apenas 5 minutos. Após começar, o atrito inicial some e a inércia joga a seu favor."},
          {"numero": 2, "titulo": "Corte as Negociações", "descricao": "Nunca dialogue com a voz da preguiça. Decidiu algo na noite anterior? Execute sem pensar pela manhã."},
          {"numero": 3, "titulo": "Micro-Vitórias", "descricao": "Não tente mudar a vida inteira num dia. Foque em ganhar a primeira hora do seu dia."},
          {"numero": 4, "titulo": "Documente o Progresso", "descricao": "Anote suas vitórias diárias. Ver seu próprio avanço cria o impulso psicológico para não quebrar a corrente."}
        ]
      },
      "fechamento": "A decisão é sua e apenas sua. O mundo não vai parar para esperar você se organizar. Tome as rédeas da sua mente hoje, ou deixe que as circunstâncias continuem escrevendo a sua história.",
      "rodape": "Produzido com foco, método e propósito."
    }
    
    return conteudo_emergencia
