import random
from core.ai.styles import REGRAS_COPY_BASE, sortear_gancho

# ==========================================
# TEMAS E SUB-ÂNGULOS APROFUNDADOS
# ==========================================
TEMAS_MAPEADOS = {
    "espiritualidade": {
        "nome": "Espiritualidade e Fé",
        "inspira": "sabedoria bíblica, ensinamentos de Jesus Cristo, filosofia de Salomão e Provérbios",
        "query_unsplash": "cross,ancient,temple,monastery,light",
        "hashtags": ["#sabedoria", "#fe", "#proposito", "#espiritualidade", "#gratidao"],
        "sub_angulos": [
            "O silêncio como forma de escuta espiritual — quando parar de pedir e começar a ouvir",
            "A diferença entre religiosidade de fachada e uma fé que transforma por dentro",
            "Por que gratidão real muda a perspectiva antes de mudar a situação",
            "O paradoxo da fé: confiar no processo sem entender o plano",
            "Quando a oração muda quem ora, não apenas o que é pedido",
            "A armadilha de buscar sinais e ignorar o que já está na sua frente",
        ]
    },
    "filosofia": {
        "nome": "Filosofia e Autoconhecimento",
        "inspira": "pensamento de Platão, estoicismo, a ideia socrática de conhecer a si mesmo",
        "query_unsplash": "philosophy,ancient,wisdom,sculpture,monument,column",
        "hashtags": ["#autoconhecimento", "#filosofia", "#sabedoria", "#estoicismo", "#reflexao"],
        "sub_angulos": [
            "O que é realmente seu: separar o que você controla do que apenas te afeta",
            "A ilusão do ego — por que defendemos opiniões que nem são nossas",
            "Memento Mori: usar a ideia da morte para viver com mais intenção hoje",
            "Por que pessoas inteligentes se sabotam com excesso de análise",
            "A diferença entre ser sábio e simplesmente acumular informação",
            "Como a filosofia estoica lida com o medo que disfarçamos de precaução",
        ]
    },
    "psicologia": {
        "nome": "Psicologia e Comportamento Humano",
        "inspira": "vieses cognitivos, psicologia comportamental, como a mente racionaliza o que já decidiu por impulso",
        "query_unsplash": "abstract,mind,fog,psychology,puzzle",
        "hashtags": ["#psicologia", "#decisao", "#mentalidade", "#comportamento", "#habito"],
        "sub_angulos": [
            "Síndrome do impostor: por que quanto mais você sabe, mais sente que não sabe nada",
            "O viés de confirmação — como só enxergamos o que já acreditamos",
            "Trauma que virou identidade: quando o sofrimento passa mas a gente fica preso nele",
            "Por que o cérebro prefere o sofrimento familiar ao prazer desconhecido",
            "A psicologia por trás da procrastinação: não é preguiça, é regulação emocional",
            "Como o ambiente molda comportamento mais do que força de vontade",
        ]
    },
    "financas": {
        "nome": "Mentalidade Financeira e Riqueza",
        "inspira": "mentalidade de quem constrói riqueza com inteligência, ativos vs passivos, o preço da mediocridade financeira",
        "query_unsplash": "city,finance,gold,wealth,architecture,office",
        "hashtags": ["#financas", "#riqueza", "#mentalidadefinanceira", "#sucesso", "#dinheiro"],
        "sub_angulos": [
            "O que a classe média compra que a impede de sair da classe média",
            "A diferença entre ganhar muito e ficar rico — e por que confundimos os dois",
            "Por que pobres jogam na loteria e ricos investem na constância",
            "Ativos vs passivos: o que a escola nunca ensinou sobre dinheiro",
            "Como a identidade financeira sabotera pessoas que finalmente começam a ganhar",
            "O custo invisível de adiar decisões financeiras por mais um ano",
        ]
    },
    "liberdade": {
        "nome": "Liberdade, Sonhos e Coragem de Começar",
        "inspira": "o espírito de quem não desiste do seu sonho, aceita os riscos, dá o primeiro passo mesmo sem garantia",
        "query_unsplash": "ocean,freedom,adventure,sailing,climbing,mountain",
        "hashtags": ["#liberdade", "#sonhos", "#jornada", "#perseveranca", "#foco"],
        "sub_angulos": [
            "O medo de recomeçar do zero quando se tem muito a perder",
            "A diferença entre planejar e usar o planejamento como desculpa para não começar",
            "Por que a maioria desiste antes do ponto onde as coisas ficam interessantes",
            "Liberdade real vs liberdade de aparência — o que parece livre mas é só conforto",
            "Como saber quando é sabedoria desistir e quando é medo disfarçado",
            "A coragem que ninguém vê: os sacrifícios silenciosos de quem está construindo",
        ]
    },
    "conexoes": {
        "nome": "Relacionamentos e Inteligência Emocional",
        "inspira": "como a vulnerabilidade gera confiança, como ouvir é um ato de amor, o que une e o que separa pessoas de verdade",
        "query_unsplash": "connection,dialogue,warmth,hands,friendship",
        "hashtags": ["#relacionamentos", "#conexao", "#empatia", "#inteligenciaemocional", "#amor"],
        "sub_angulos": [
            "O que a maioria confunde com amor mas é só vício emocional",
            "Por que somos mais honestos com estranhos do que com quem amamos",
            "A solidão de estar rodeado de pessoas que não te entendem de verdade",
            "Como o orgulho destrói silenciosamente o que o amor construiu com esforço",
            "A diferença entre escutar para responder e escutar para entender",
            "Por que relacionamentos que começam com intensidade costumam terminar com vazio",
        ]
    },
    "superacao": {
        "nome": "Superação e Autossabotagem",
        "inspira": "o maior inimigo mora dentro da gente — crenças limitantes, conformismo, medo disfarçado de prudência",
        "query_unsplash": "storm,path,silhouette,climbing,dark,run",
        "hashtags": ["#superacao", "#foco", "#resiliencia", "#coragem", "#determinacao"],
        "sub_angulos": [
            "Autossabotagem silenciosa: quando você atrapalha o que mais quer sem perceber",
            "O conforto que te prende: por que a zona de conforto é tão boa e tão perigosa",
            "Procrastinação vs execução: a diferença entre quem planeja e quem faz",
            "Crenças herdadas: ideias que você nunca escolheu mas que governam suas decisões",
            "Por que mudar de vida assusta mesmo quando a vida atual não está boa",
            "A voz interna que sempre encontra uma razão para esperar mais um dia",
        ]
    },
    "proposito": {
        "nome": "Propósito e Legado",
        "inspira": "viver com intenção, escolher conscientemente quem você quer ser, o que você deixa no mundo e nas pessoas",
        "query_unsplash": "legacy,path,compass,forest,sunlight,sky",
        "hashtags": ["#proposito", "#legado", "#vida", "#intencao", "#evoluir"],
        "sub_angulos": [
            "A diferença entre ter objetivos e ter um propósito que te sustenta nos dias ruins",
            "O que você está construindo que vai existir quando você não estiver mais aqui",
            "Por que tantas pessoas bem-sucedidas se sentem vazias por dentro",
            "Como saber se você está no caminho certo ou apenas no caminho seguro",
            "A ilusão do futuro: por que adiamos viver com sentido para quando tiver dinheiro ou tempo",
            "Quem você está se tornando enquanto persegue o que quer conquistar",
        ]
    }
}

# ==========================================
# TEMA POR DIA DA SEMANA
# ==========================================
TEMAS_POR_DIA = {
    0: "espiritualidade",  # Segunda
    1: "filosofia",        # Terça
    2: "psicologia",       # Quarta
    3: "financas",         # Quinta
    4: "liberdade",        # Sexta
    5: "conexoes",         # Sábado
    # Domingo = sorteio entre superacao e proposito
}

def montar_instrucoes_copy(detalhes_tema, contexto_analytics=""):
    """Monta o bloco de instrução de copy injetado em todos os prompts."""
    sub_angulo = random.choice(detalhes_tema["sub_angulos"])
    gancho = sortear_gancho()

    instrucoes = f"""
    {REGRAS_COPY_BASE}
    
    Tema de inspiração (NÃO cite nomes, use apenas a essência): {detalhes_tema['inspira']}
    
    Ângulo específico para esta postagem: {sub_angulo}
    
    Gancho narrativo: {gancho}
    
    {contexto_analytics}
    """
    return instrucoes, sub_angulo
