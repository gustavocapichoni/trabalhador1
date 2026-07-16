import random

# =====================================================================
# BIBLIOTECA DE ELEMENTOS CINEMATOGRÁFICOS (Baseada na sua sugestão)
# =====================================================================


CLIMAS = [
    "light mist", "gentle rain", "dramatic storm clouds", "crystal clear blue sky",
    "falling snow flakes", "soft wind blowing", "bright golden dawn sunrise",
    "warm glowing sunset", "glowing full moon", "starry night sky"
]

ENQUADRAMENTOS = [
    "Close-up shot of", "Medium shot of", "Wide angle shot of", "Aerial view of",
    "Low angle view of", "High angle view of", "Macro shot of", "Silhouette shot of"
]

ESTILOS = [
    "raw photograph, photo", "candid photography", "captured on 35mm film", 
    "shot on DSLR camera", "natural skin texture with pores and imperfections", 
    "kodak portra 400 style", "authentic daylight", "real life documentary style"
]

# =====================================================================
# MAPEAMENTO DE SÍMBOLOS POR TEMA
# =====================================================================
TEMAS_SIMBOLOS = {
    "espiritualidade": {
        "personagens": ["old wise monk", "wanderer traveler", "child looking up"],
        "objetos": ["glowing wax candle", "single white rose", "old brass lantern", "wooden ladder going up"],
        "cenarios": ["secluded mountaintop monastery", "grand cathedral with stained glass", "ancient stone temple", "zen japanese garden with bonsai"]
    },
    "filosofia": {
        "personagens": ["thoughtful philosopher", "focused writer at work", "old wise monk"],
        "objetos": ["ancient leather book", "glass hourglass", "writing quill and ink"],
        "cenarios": ["massive library with high ceilings", "ancient roman ruins", "secluded mountaintop monastery"]
    },
    "psicologia": {
        "personagens": ["thoughtful philosopher", "focused writer at work", "scientist looking at device"],
        "objetos": ["antique hand mirror", "glass hourglass", "partially open wooden door", "large glass window"],
        "cenarios": ["massive library with high ceilings", "serene sunlit desert", "zen japanese garden with bonsai"]
    },
    "financas": {
        "personagens": ["elegant man in suit", "focused writer at work", "scientist looking at device"],
        "objetos": ["vintage pocket watch", "glowing golden key", "large glass window"],
        "cenarios": ["luxurious executive office", "state of the art modern laboratory", "futuristic cyberpunk city skyline"]
    },
    "liberdade": {
        "personagens": ["wanderer traveler", "explorer holding map", "photographer taking picture"],
        "objetos": ["old brass compass", "small wooden boat", "glowing golden key"],
        "cenarios": ["vast open ocean", "coastal cliff side", "green sunlit valley", "suspension bridge over foggy canyon", "old vintage railway station"]
    },
    "conexoes": {
        "personagens": ["loving couple walking", "elderly woman smiling", "child looking up"],
        "objetos": ["single white rose", "classic wooden violin", "glowing wax candle"],
        "cenarios": ["zen japanese garden with bonsai", "cozy warm room", "green sunlit valley"]
    },
    "superacao": {
        "personagens": ["carpenter working wood", "sculptor chisel in hand", "wanderer traveler"],
        "objetos": ["ancient sword", "old brass lantern", "old stone bridge"],
        "cenarios": ["abandoned medieval castle", "pristine snow plains", "deep cavern with glowing crystals", "coastal cliff side"]
    },
    "proposito": {
        "personagens": ["creative artist painting", "painter at easel", "musician holding instrument", "focused writer at work"],
        "objetos": ["old brass compass", "majestic old oak tree", "glowing golden key", "writing quill and ink"],
        "cenarios": ["green sunlit valley", "massive library with high ceilings", "secluded mountaintop monastery"]
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
