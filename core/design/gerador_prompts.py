import random

# =====================================================================
# BIBLIOTECA DE ELEMENTOS CINEMATOGRÁFICOS (Baseada na sua sugestão)
# =====================================================================


CLIMAS = [
    "glowing neon reflections in rain", "dramatic cyberpunk night lights", "warm golden ambient illumination",
    "light mist with neon beam rays", "falling snow flakes with glowing city lights", "starry night sky over futuristic skyline"
]

ENQUADRAMENTOS = [
    "Close-up shot of", "Medium shot of", "Wide angle shot of", "Aerial view of",
    "Low angle view of", "High angle view of", "Macro shot of", "Silhouette shot of"
]

ESTILOS = [
    "cinematic photograph, high contrast, dark gold lighting", "candid cyberpunk photography",
    "shot on 35mm lens with vivid neon highlights", "natural skin texture with futuristic ambient glow",
    "dark luxury aesthetic with gold and cyan neon accents", "authentic night documentary style"
]

# =====================================================================
# MAPEAMENTO DE SÍMBOLOS POR TEMA
# =====================================================================
TEMAS_SIMBOLOS = {
    "espiritualidade": {
        "personagens": ["thoughtful wanderer", "person meditating in neon city", "glowing neural AI brain reflection"],
        "objetos": ["glowing golden brain circuit diagram", "ancient pillar with futuristic hologram", "glowing golden candle", "old brass lantern"],
        "cenarios": ["futuristic sacred temple night neon", "secluded mountaintop monastery over cyber city", "dark glass tower overlooking neon city"]
    },
    "filosofia": {
        "personagens": ["thoughtful philosopher", "focused writer at futuristic desk", "person looking at cyber skyline"],
        "objetos": ["ancient leather book with holographic glowing text", "glass hourglass with golden glowing sand", "glowing neural circuit pillar"],
        "cenarios": ["futuristic high tech library with neon lights", "ancient roman ruins with cyber hologram lights", "dark gold luxury cyber office"]
    },
    "psicologia": {
        "personagens": ["thoughtful person looking at neon city", "focused scientist looking at neural holographic interface", "person walking night street"],
        "objetos": ["antique hand mirror with neon reflection", "glowing neural network diagram", "large glass window over futuristic city"],
        "cenarios": ["futuristic cyberpunk apartment at night", "glowing dark gold reflection room", "neonlit metropolis night street"]
    },
    "financas": {
        "personagens": ["elegant person in dark suit", "visionary founder looking at skyline", "cyber executive"],
        "objetos": ["glowing golden key", "holographic financial chart", "luxury golden watch"],
        "cenarios": ["luxurious executive office overlooking cyberpunk night city skyline", "futuristic skyscraper terrace at night", "state of the art modern cyber laboratory"]
    },
    "liberdade": {
        "personagens": ["wanderer traveler looking at neon metropolis", "explorer walking night bridge", "person driving on futuristic highway"],
        "objetos": ["glowing golden compass", "futuristic motorcycle", "glowing golden key"],
        "cenarios": ["futuristic suspension bridge over foggy cyber canyon", "cyberpunk highway night motion", "coastal cliff overlooking glowing neon city"]
    },
    "conexoes": {
        "personagens": ["people walking together in neon city", "moving crowd in futuristic metropolis", "person looking at digital connections"],
        "objetos": ["glowing golden neural thread", "classic wooden violin with gold light", "glowing wax candle"],
        "cenarios": ["cyberpunk street with moving crowd at night", "cozy room overlooking neon city skyline", "futuristic urban plaza at night"]
    },
    "superacao": {
        "personagens": ["runner training in rain under neon lights", "person climbing futuristic glass tower", "wanderer in cyber city"],
        "objetos": ["glowing golden emblem", "ancient sword with cyber glow", "old stone bridge with neon lights"],
        "cenarios": ["cyberpunk skyscraper rooftop night", "futuristic rain drenched city street", "deep cavern with glowing golden crystals"]
    },
    "proposito": {
        "personagens": ["creative visionary looking at horizon", "artist working with holographic light", "focused writer in cyber room"],
        "objetos": ["glowing golden compass", "glowing golden brain circuit pillar", "glowing golden key"],
        "cenarios": ["futuristic glass observatory looking at night city", "high tech library with golden ambient glow", "cyberpunk city skyline night"]
    }
}

def gerar_prompt_cinematografico(tema: str) -> str:
    """
    Gera um prompt de imagem em inglês combinando proceduralmente enquadramento,
    personagem, cenário, objeto, clima e estilo visual baseados no tema.
    """
    tema = tema.lower()
    
    # Fallback se o tema não estiver mapeado
    if tema not in TEMAS_SIMBOLOS:
        tema = "espiritualidade"
        
    simbolos = TEMAS_SIMBOLOS[tema]
    
    # Sorteio dos elementos correspondentes ao tema
    personagem = random.choice(simbolos["personagens"])
    objeto = random.choice(simbolos["objetos"])
    cenario = random.choice(simbolos["cenarios"])
    
    # Sorteio dos elementos gerais para mistura
    enquadramento = random.choice(ENQUADRAMENTOS)
    clima = random.choice(CLIMAS)
    
    # Sorteia 2 a 3 estilos para riqueza de detalhes
    estilos_escolhidos = random.sample(ESTILOS, k=random.randint(2, 3))
    estilo_str = ", ".join(estilos_escolhidos)
    
    # Ajuste de pré-posição para o enquadramento fluir melhor em inglês
    art_pers = "an" if personagem[0] in "aeiou" else "a"
    art_obj = "an" if objeto[0] in "aeiou" else "a"
    
    prompt = (
        f"An authentic realistic photograph, {enquadramento} {art_pers} {personagem} interacting with {art_obj} {objeto}, "
        f"inside {cenario}, {clima}, {estilo_str}. Real life, photojournalism, realistic skin texture. Avoid digital art, 3d render, painting, CGI, illustration, cartoon, drawing, vector, anime, artwork."
    )
    
    return prompt

if __name__ == "__main__":
    # Teste rápido de geração
    for t in TEMAS_SIMBOLOS.keys():
        print(f"[{t.upper()}]: {gerar_prompt_cinematografico(t)}\n")
