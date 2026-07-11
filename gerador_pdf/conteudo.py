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
Você é um escritor especialista em conteúdo transformador que combina narrativa emocional com ensinamentos práticos.

BRIEFING DA SEMANA:
- Tema central: {nome_display}
- Livro base de inspiração: "{livro_base}"
- Dor central da audiência: "{dor_central}"

CONTEXTO DO MUNDO REAL NESTA SEMANA:
{contexto_semana}

SUA MISSÃO:
Escreva o conteúdo completo de um PDF de 8 páginas seguindo EXATAMENTE a estrutura abaixo.
O conteúdo deve ser 100% original, inspirado nos princípios do livro "{livro_base}".
NUNCA cite o livro pelo nome no texto final. Use o conhecimento como se fosse seu.
Conecte o tema com o que está acontecendo no mundo real nesta semana.

IMPORTANTE - NOME DO PDF:
Crie um título magnético que remete ao PROBLEMA + SOLUÇÃO (nunca use "Manual" ou "Guia").
Ex: "O Código da Consistência", "A Virada do Hábito", "Quando a Mente Para de Lutar".

REGRAS DE FORMATAÇÃO DE TEXTO E JSON:
- Use apenas texto simples, pontos e vírgulas.
- É PROIBIDO usar emojis, caracteres especiais (como ◎, 🎯, ✨), aspas redondas (smart quotes) ou travessões longos. Use apenas aspas duplas retas (") e hífens simples (-).
- NÃO crie formatações complexas, mantenha o texto o mais limpo e legível possível.
- CRÍTICO: NUNCA use quebras de linha literais (Enter) dentro dos textos do JSON. Se o texto for longo, escreva tudo na mesma linha contínua, sem pular linha dentro da string. Pular linha dentro do valor do JSON vai corromper o sistema.

ESTRUTURA OBRIGATÓRIA (retorne em formato JSON):

{{
  "titulo_pdf": "Título magnético aqui",
  "subtitulo_pdf": "Uma frase curta de impacto aqui",
  "capa_cards": [
    {{"titulo": "A Névoa", "texto": "Escreva uma explicacao poderosa e emocional de POR QUE a voz interna sabota toda tentativa de mudanca. Explique o mecanismo psicologico: o loop mental do 'amanha comeco', o medo disfarçado de preguica, a autossabotagem que surge exatamente quando voce esta prestes a mudar. Seja impactante e profundo. Minimo 35 palavras, maximo 45, sem pular linha, sem aspas."}},
    {{"titulo": "A Solucao", "texto": "Escreva uma descricao envolvente e que gera desejo da solucao: o metodo preciso que vai silenciar essa voz interna e transformar a inercia em habitos solidos. Mostre a transformacao de forma visceral. Minimo 35 palavras, maximo 45, sem pular linha, sem aspas."}},
    {{"titulo": "O Proposito", "texto": "Uma frase direta e inspiradora sobre o que a pessoa vai conquistar ao seguir esse metodo. Maximo 18 palavras, sem aspas."}},
    {{"titulo": "A Verdade", "texto": "Uma provocacao curta e cirurgica sobre a realidade da situacao. Maximo 14 palavras, sem aspas."}}
  ],
  "capitulos": [
    {{
      "numero": 1,
      "titulo": "A Névoa do Cotidiano",
      "paragrafos": [
        "Parágrafo 1 — Apresenta a cena do personagem (Arthur ou outro nome) no momento de maior dor. Seja altamente cinematográfico e detalhado. Mínimo 80 palavras e sem pular linha.",
        "Parágrafo 2 — Aprofunda a dor. Uma reflexão profunda em itálico que é o pensamento interno do personagem. Mínimo 60 palavras e sem pular linha.",
        "Parágrafo 3 — Contextualiza e amplia: essa não é só a dor dele, é a dor de milhões. Mostre o peso da realidade. Mínimo 80 palavras e sem pular linha."
      ]
    }},
    {{
      "numero": 2,
      "titulo": "O Espelho Partido",
      "paragrafos": [
        "Parágrafo 1 — Um evento catalisador ou uma conversa dura que o faz perceber a urgência de mudar. Mínimo 80 palavras e sem pular linha.",
        "Parágrafo 2 — O conflito interno entre querer desistir e a necessidade de continuar. Mínimo 60 palavras e sem pular linha.",
        "Parágrafo 3 — A decisão. O exato momento em que ele recusa a inércia. Mínimo 80 palavras e sem pular linha."
      ]
    }},
    {{
      "numero": 3,
      "titulo": "A Arma Secreta",
      "paragrafos": [
        "Parágrafo 1 — O personagem encontra um insight, um livro velho, uma estratégia. Mínimo 80 palavras e sem pular linha.",
        "Parágrafo 2 — O conceito principal do livro explicado de forma rica, densa e original. Mínimo 60 palavras e sem pular linha.",
        "Parágrafo 3 — A metáfora poderosa: como isso se aplica à vida real de forma implacável. Mínimo 80 palavras e sem pular linha."
      ]
    }},
    {{
      "numero": 4,
      "titulo": "O Campo de Batalha",
      "paragrafos": [
        "Parágrafo 1 — O personagem começa a aplicar na prática. As primeiras dificuldades e o peso do início. Mínimo 80 palavras e sem pular linha.",
        "Parágrafo 2 — O atrito. A força da velha rotina tentando puxá-lo de volta, e a disciplina forjada na dor. Mínimo 60 palavras e sem pular linha.",
        "Parágrafo 3 — A virada. A pequena vitória que mostra que o método funciona. Mínimo 80 palavras e sem pular linha."
      ]
    }},
    {{
      "numero": 5,
      "titulo": "A Nova Ordem",
      "paragrafos": [
        "Parágrafo 1 — A progressão ao longo do tempo. O hábito se instala e vira parte da identidade. Mínimo 80 palavras e sem pular linha.",
        "Parágrafo 2 — A paz após a guerra. O contraste entre quem ele era no início e quem é agora. Mínimo 60 palavras e sem pular linha.",
        "Parágrafo 3 — A moral da história. A mensagem final e inspiradora para quem lê e vive a mesma situação. Mínimo 80 palavras e sem pular linha."
      ]
    }}
  ],
  "citacao_destaque": "Uma citação poderosa e original (não do livro) que resume a transformação. 2-3 linhas.",
  "plano_acao": {{
    "titulo_secao": "Plano de Ação Diário",
    "subtitulo": "Comece pequeno. Construa grande.",
    "passos": [
      {{"numero": 1, "titulo": "Nome do Passo 1", "descricao": "O que fazer, como fazer, por que funciona. 3-4 linhas."}},
      {{"numero": 2, "titulo": "Nome do Passo 2", "descricao": "O que fazer, como fazer, por que funciona. 3-4 linhas."}},
      {{"numero": 3, "titulo": "Nome do Passo 3", "descricao": "O que fazer, como fazer, por que funciona. 3-4 linhas."}},
      {{"numero": 4, "titulo": "Nome do Passo 4", "descricao": "O que fazer, como fazer, por que funciona. 3-4 linhas."}}
    ]
  }},
  "fechamento": "O parágrafo final inspiracional. A hora é agora. Deixe sua luz brilhar. 4-5 linhas.",
  "rodape": "Produzido com zelo, fé e propósito."
}}

Retorne APENAS o JSON, sem texto antes ou depois.
"""


def gerar_conteudo_pdf(briefing: dict) -> dict:
    print("[Conteudo] Chamando Gemini AI para gerar o conteudo do PDF...")

    prompt = PROMPT_TEMPLATE.format(
        nome_display=briefing["nome_display"],
        livro_base=briefing["livro_base"],
        dor_central=briefing["dor_central"],
        contexto_semana=briefing["contexto_semana"]
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
      "capa_cards": [
        {"titulo": "A Névoa", "texto": "A autossabotagem não chega gritando. Ela sussurra que 'amanhã é um dia melhor'. Ela te convence de que o conforto de hoje vale mais que o orgulho de amanhã. É a prisão mais invisível que existe."},
        {"titulo": "A Solução", "texto": "O domínio não nasce da motivação, mas da clareza inegociável. Quando você decide que a dor da disciplina é menor que a dor do arrependimento, o jogo vira. O método é implacável."},
        {"titulo": "O Propósito", "texto": "Recuperar o poder sobre suas próprias decisões e destruir a procrastinação."},
        {"titulo": "A Verdade", "texto": "Você não tem um problema de tempo. Você tem um problema de prioridade."}
      ],
      "capitulos": [
        {
          "numero": 1,
          "titulo": "O Peso Invisível",
          "paragrafos": [
            "Existe uma guerra silenciosa acontecendo dentro de você todos os dias. Ela não usa armas de fogo, mas desculpas muito bem articuladas. Quando o despertador toca, quando o projeto exige atenção, quando a mudança precisa acontecer, uma voz interna entra em ação. Ela é persuasiva. Ela conhece suas fraquezas melhor do que ninguém, porque ela é você. E na maioria das vezes, ela vence sem você nem perceber que estava em uma batalha.",
            "Essa voz prospera no conforto. Ela te convence de que não há problema em adiar, de que você merece um descanso, de que amanhã você estará mais preparado. E assim, os dias viram semanas, e as semanas viram anos. O potencial não realizado começa a pesar nos ombros como chumbo. A frustração de saber do que você é capaz, mas ver-se paralisado pela própria mente, é a dor mais silenciosa que existe.",
            "Mas entenda isso: você não está sozinho nessa trincheira. A humanidade inteira luta contra a inércia. Nossos cérebros foram programados evolutivamente para economizar energia e evitar o desconforto. Cada vez que você tenta romper o padrão, seu sistema de defesa entra em alerta máximo. Reconhecer que isso não é uma falha de caráter, mas um mecanismo primitivo, é o primeiro passo para a verdadeira libertação."
          ]
        },
        {
          "numero": 2,
          "titulo": "O Ponto de Ruptura",
          "paragrafos": [
            "A mudança raramente acontece por inspiração; ela costuma nascer do puro e absoluto desconforto. Chega um momento em que a dor de permanecer exatamente onde você está se torna insuportável. É o instante em que você olha no espelho e não reconhece mais a pessoa acomodada do outro lado. Esse é o momento sagrado. O atrito. A faísca que pode incendiar a floresta das suas velhas desculpas.",
            "Nesse momento de clareza, a bifurcação aparece. De um lado, a estrada familiar do 'depois eu faço', pavimentada com justificativas confortáveis. Do outro, o caminho íngreme da disciplina, onde não há aplausos, apenas o som da sua própria respiração ofegante. É a escolha entre a dor momentânea do esforço ou a dor crônica do arrependimento.",
            "E então, você decide. Não com um grito, mas com um sussurro inegociável para si mesmo: 'Chega'. Essa decisão não é motivacional, é estrutural. É o exato segundo em que você para de negociar com a voz da preguiça. Você demite o gerente incompetente da sua mente e assume a diretoria da sua própria vida. A partir daqui, as regras mudam."
          ]
        },
        {
          "numero": 3,
          "titulo": "A Disciplina como Espada",
          "paragrafos": [
            "Motivação é um combustível adulterado. Ela te leva até a esquina e te abandona no primeiro obstáculo. A disciplina, por outro lado, é um motor a diesel: pesado para ligar, mas impossível de parar depois que ganha tração. A disciplina não pergunta como você está se sentindo. Ela não se importa se chove lá fora ou se você dormiu mal. Ela simplesmente exige execução.",
            "A grande chave é entender que a disciplina não é uma prisão, é a própria definição de liberdade. Quem não domina a si mesmo será eternamente escravo de seus impulsos e das circunstâncias. Ao forjar hábitos de ferro, você automatiza o sucesso. Você retira o peso da decisão diária e coloca sua mente no piloto automático para o crescimento constante.",
            "Imagine a disciplina como uma espada forjada no fogo do desconforto. Cada vez que você faz o que precisa ser feito, mesmo sem vontade, você dá uma marretada no aço quente, tornando-o mais forte, mais afiado. Com o tempo, essa espada se torna capaz de cortar qualquer adversidade, qualquer desculpa, com a precisão de um mestre."
          ]
        },
        {
          "numero": 4,
          "titulo": "A Forja do Hábito",
          "paragrafos": [
            "Não subestime o poder repulsivo da sua velha rotina. Quando você começa a implementar a nova ordem, o sistema reage com força total. Os primeiros dias são marcados por um entusiasmo ingênuo, mas logo o atrito se apresenta. A cama parece mais macia, as distrações parecem mais urgentes. Esse é o vale da sombra da morte da mudança de hábito. É aqui que 99% das pessoas desistem e voltam para o começo.",
            "Mas você não. Você sabe que o atrito é apenas o som da fraqueza abandonando seu corpo. Você se concentra na execução do micro-hábito. Não importa o quão pequeno seja o passo, importa que ele seja dado. A consistência é muito mais poderosa do que a intensidade. Uma gota d'água cavando uma rocha não precisa de força, precisa apenas de tempo e de uma direção imutável.",
            "E então, acontece. A primeira pequena vitória. Aquele dia em que você fez sem precisar se forçar tanto. O circuito neural começa a se fortalecer, o caminho de terra vira asfalto. A identidade começa a mudar. Você deixa de ser alguém que 'está tentando ser disciplinado' e passa a ser, intrinsecamente, uma pessoa inegociável com seus próprios padrões."
          ]
        },
        {
          "numero": 5,
          "titulo": "O Horizonte Silencioso",
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
