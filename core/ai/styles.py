import random

# ==========================================
# ESTILOS DE COPY (abordagem narrativa)
# ==========================================
ESTILOS_COPY = [
    "opinião polêmica: defenda um ponto de vista que a maioria evita dizer",
    "verdade incômoda: diga algo que as pessoas sabem mas não admitem",
    "pergunta perturbadora: faça uma pergunta que o leitor não consegue responder facilmente",
    "inversão de lógica: pegue uma crença comum e vire ela de cabeça pra baixo",
    "confissão honesta: fale como alguém que já errou e aprendeu, sem heroísmo",
    "contraste brutal: mostre a diferença entre quem age e quem fica na intenção",
    "diagnóstico direto: identifique um padrão de comportamento que o leitor reconhece em si",
    "efeito espelho: descreva uma situação tão específica que o leitor sente que foi escrita pra ele",
]

# ==========================================
# GANCHOS NARRATIVOS (para abrir histórias)
# ==========================================
GANCHOS_NARRATIVOS = [
    "Comece com uma cena específica do cotidiano que o leitor reconhece instantaneamente.",
    "Comece com uma contradição: algo que parece errado mas faz sentido.",
    "Comece com uma pergunta que o leitor nunca se fez mas deveria.",
    "Comece com uma observação que a maioria das pessoas nota mas nunca articula em palavras.",
    "Comece com o final da história e depois explique como chegou lá.",
    "Comece com uma afirmação polêmica que provoca discordância imediata.",
]

# ==========================================
# CTAS VARIADOS (chamadas para ação)
# ==========================================
CTAS_VARIAVEIS = [
    "Comente EU QUERO que te envio o PDF com o conteúdo completo.",
    "Salva esse post para quando precisar lembrar disso.",
    "Manda pra alguém que precisa ouvir isso hoje.",
    "Comenta uma palavra que te veio à cabeça depois de ler.",
    "Comente EU QUERO e te envio o material gratuito.",
    "Salva. Você vai precisar ler de novo num dia difícil.",
]

# ==========================================
# REGRAS DE COPY (compartilhadas por todos os prompts)
# ==========================================
REGRAS_COPY_BASE = """
REGRAS ABSOLUTAS DE COPY (violá-las é inaceitável):

❌ PROIBIDO — nunca use estas frases ou variações delas:
- "Acredite em você", "Você é capaz", "Nunca desista", "Foco e determinação"
- "Seja a melhor versão de si mesmo", "Saia da zona de conforto"
- "O sucesso é para quem corre atrás", "A vida é uma jornada"
- "Faça acontecer", "Você tem o poder", "Hoje é o dia"
- NUNCA cite autores, livros, filmes, séries, marcas ou personagens pelo nome.
- NUNCA escreva de forma genérica. Cada frase deve parecer que foi escrita para UMA pessoa específica.

✅ OBRIGATÓRIO — o que torna um copy memorável:
- Começa com uma observação ESPECÍFICA que poucas pessoas dizem em voz alta.
- Usa linguagem coloquial brasileira — como uma conversa real, não um discurso.
- Provoca uma reação: "nossa, nunca tinha pensado assim" ou "isso me deu raiva mas é verdade".
- A frase de impacto deve ser IMPREVISÍVEL. Evite o óbvio.
- Prefira verdades desconfortáveis a frases de encorajamento vazio.
- Tom: direto, íntimo, sem pedantismo. Como um amigo que fala o que os outros têm medo de dizer.

🧠 FUNDAMENTOS DE NEUROCIÊNCIA E PERSUASÃO (use implicitamente, nunca declare):
- INTERRUPÇÃO DE PADRÃO: O cérebro humano ignora o previsível. Comece com algo inesperado
  que force o sistema nervoso a prestar atenção. Contradição, ironia ou inversão de lógica são armas poderosas.
- LOOP ABERTO (Efeito Zeigarnik): O cérebro é biologicamente incapaz de ignorar uma história inacabada.
  Sempre deixe uma pergunta implícita no ar que só o próximo slide resolve.
- DOPAMINA E RECOMPENSA: Entregue valor prático e concreto que o leitor pode aplicar em 5 minutos.
  O cérebro libera dopamina ao sentir que aprendeu algo útil de graça — isso cria dependência positiva do conteúdo.
- ANCORAGEM DE IDENTIDADE (PNL): Faça o leitor se identificar com um grupo de pessoas "que entendem".
  Frases como "quem está nesse nível sabe que..." ou "pessoas que chegaram até aqui..." criam pertencimento.
- AVERSÃO À PERDA: O cérebro humano reage 2x mais forte a possibilidade de perda do que a ganho.
  Use para criar urgência sem parecer vendedor. Ex: "cada dia que passa sem isso é um dia desperdiçado".
- REFORÇO POSITIVO E VALIDAÇÃO: Elogie a inteligência do leitor por estar lendo até ali.
  Faça-o sentir especial, acima da média. Isso cria laço emocional com o criador do conteúdo.
  Ex: "O fato de você estar aqui prova que sua mente funciona diferente da maioria."
- PROVA SOCIAL IMPLÍCITA: Mencione padrões de comportamento de pessoas bem-sucedidas sem citar nomes.
  Isso ativa o instinto de imitação social do cérebro.
"""

def sortear_estilo():
    return random.choice(ESTILOS_COPY)

def sortear_gancho():
    return random.choice(GANCHOS_NARRATIVOS)

def sortear_cta():
    return random.choice(CTAS_VARIAVEIS)
