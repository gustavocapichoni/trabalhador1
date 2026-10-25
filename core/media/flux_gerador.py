"""
flux_gerador.py
---------------
Modulo de geracao de imagens via FLUX.1-schnell (Hugging Face).

Responsabilidades:
  - Gerenciar rodizio entre 5 tokens HF (conta 1, 40, 04, 05, 03)
  - Montar prompts variados via matriz: Tema -> Subtema -> Angulo -> Ambiente -> Horario
  - Retry inteligente: outro erro -> tenta 3x com pausa; cota excedida -> pula imediatamente
  - Retornar caminho da imagem gerada, ou None se todos os tokens falharem
"""

import os
import time
import random
import shutil
from datetime import datetime
from loguru import logger

# ============================================================
# TOKENS HF (5 contas em rodizio via variaveis de ambiente)
# ============================================================
HF_TOKENS = [
    os.getenv("HF_TOKEN_1"),
    os.getenv("HF_TOKEN_2"),
    os.getenv("HF_TOKEN_3"),
    os.getenv("HF_TOKEN_4"),
    os.getenv("HF_TOKEN_5"),
]
HF_TOKENS = [t for t in HF_TOKENS if t]

# Palavras-chave que identificam erro de cota excedida (pula imediatamente)
COTA_EXCEDIDA_KEYWORDS = ["zerogpu quota", "quota", "exceeded"]

# ============================================================
# POOL DE CIDADES (variacao aleatoria a cada geracao)
# ============================================================
_CIDADES = [
    "Tokyo", "New York", "London", "Paris", "Shanghai",
    "Seoul", "Sao Paulo", "Chicago", "Hong Kong", "Amsterdam",
    "Berlin", "Bangkok", "Singapore", "Dubai", "Buenos Aires",
    "Mexico City", "Istanbul", "Toronto", "Sydney", "Milan",
]

# ============================================================
# POOL DE EFEITOS ATMOSFERICOS (um selecionado aleatoriamente)
# ============================================================
_EFEITOS_ATMOSFERICOS = [
    "light drizzle with wet reflections on the pavement",
    "heavy rain with water puddles reflecting neon lights",
    "dense urban fog with glowing halos around streetlights",
    "thin mist drifting between buildings",
    "light snowfall with snowflakes visible under streetlamps",
    "blizzard with snow swirling in the wind",
    "freezing fog with ice crystals in the air",
    "low-hanging storm clouds with distant lightning",
    "wet streets after rain with mirror-like reflections",
    "humid night air with visible condensation on glass surfaces",
]

# ============================================================
# POOL DE ANGULOS / PERSPECTIVAS (um selecionado aleatoriamente)
# ============================================================
_ANGULOS = [
    "shot from the rooftop of a skyscraper looking down at the streets below",
    "aerial view from a high-rise building terrace, looking down diagonally",
    "bird's-eye view from a drone hovering above the city",
    "shot from a high-floor apartment window looking down at the street",
    "top-down perspective from a pedestrian bridge above the scene",
    "low angle looking up at towering buildings disappearing into the fog",
    "eye-level shot on the street with deep perspective vanishing point",
    "shot through a rain-covered floor-to-ceiling glass window from inside a high floor",
    "counter-plunge angle from a fire escape high above the alley",
    "wide establishing shot from a rooftop edge at night",
]

# ============================================================
# MATRIZ DE SUBTEMAS - todos 100% noturnos
# Tupla: (subtema, descricao_da_cena)
# ============================================================
_MATRIZ_PROMPTS = [
    # ── 1. FAIXAS DE PEDESTRES E MULTIDÃO NA CHUVA ──
    (
        "crowded rainy crosswalk in London top-down",
        "A wet street crosswalk in London at night, high angle top-down view. Dozens of black umbrellas crossing under streetlamps, rain puddle reflections of headlights.",
    ),
    (
        "pedestrian shoes on wet crosswalk low angle",
        "Low angle ground view of shoes walking across a wet city crosswalk at night. Puddles reflecting glowing neon and amber streetlights.",
    ),
    (
        "motion blur crowd around motionless person",
        "A busy urban street crosswalk at night. One person stands completely still in sharp focus while the surrounding crowd passes by in motion blur.",
    ),
    (
        "oxford street london red bus rain night",
        "A rainy night at a London intersection. A classic red double-decker bus moving in the background, wet asphalt reflecting red and gold city lights.",
    ),

    # ── 2. METRÔ NOTURNO (SUBWAY / TUBE) ──
    (
        "subway car passenger looking out window",
        "Inside a dark metro subway car at night. A young thoughtful man in a dark coat sits near the window, looking out at dark tunnel wall reflections. Soft moody interior light.",
    ),
    (
        "empty london underground tube platform",
        "An empty curved London Underground subway platform at night. Soft warm vintage lighting, a single figure in a long coat waiting for the train.",
    ),
    (
        "deep subway escalator perspective",
        "Deep perspective view going down a long metallic escalator into a dark underground metro station at night. Cold shadows and warm highlights.",
    ),
    (
        "metro car door window glass face reflection",
        "Close detail shot of a person's face reflected on the glass window of a subway train door as it moves through the dark tunnel at night.",
    ),

    # ── 3. PRAÇAS E RUA HISTÓRICAS (PARIS / LONDRES) ──
    (
        "couple in a foggy Paris plaza bench",
        "A historic stone plaza in Paris at night under soft fog. A couple sitting on a wooden bench illuminated by a warm gas streetlight.",
    ),
    (
        "person leaning on stone bridge river seine",
        "A lonely figure leaning on the stone railing of a bridge over the Seine River in Paris at night. City palace lights reflecting on dark water.",
    ),
    (
        "paris cafe outdoor terrace rainy night",
        "A cozy outdoor terrace of a Parisian cafe at night under a drizzle. A solitary person sitting at a small round table under warm canopy lights.",
    ),
    (
        "cobblestone alley night walking away",
        "A narrow historic cobblestone street at night. A single person in a dark coat walking away into the distance under warm wall-mounted street lanterns.",
    ),

    # ── 4. VIDRO MOLHADO & EFEITO BOKEH ──
    (
        "looking through rain-streaked window at city lights",
        "Intimate indoor view looking out a rain-covered window glass at night. Outside, blurred golden and amber city lights create a bokeh effect while a silhouette of a person looks outside.",
    ),
    (
        "view from back of rainy taxi cab at night",
        "View from the back seat of a taxi cab driving through city rain at night. Raindrops streaks on the window pane with blurred red taillights ahead.",
    ),
    (
        "blurry cafe window rainy night bokeh",
        "Macro detail of water droplets on a warm cafe glass window at night. Golden bokeh light circles from the city traffic outside.",
    ),

    # ── 5. OUTROS NÚCLEOS DA SOLIDÃO URBANA ──
    (
        "solitude inside public transportation",
        "A crowded subway car at night. Everyone is physically close but each person is absorbed in their screen. One passenger stares out into space.",
    ),
    (
        "solitude facing the speed of the city",
        "A busy street at night captured with long exposure. Cars form trails of light in motion, people blurred shadows, one central figure standing sharp.",
    ),
    (
        "isolation surrounded by skyscrapers",
        "A person standing alone in the middle of an empty street between towering illuminated skyscrapers at night, looking up into cloudy skies.",
    ),
    (
        "the last one awake in the city diner",
        "A 24-hour diner at night, empty except for one customer sitting at the counter nursing a coffee. Wet street reflecting neon signs outside.",
    ),
]


def gerar_imagem_flux(tipo: str, tema_escolhido: str = None, nome_arquivo: str = None):
    """
    Gera uma imagem via FLUX.1-schnell com rodizio de tokens e retry inteligente.

    Args:
        tipo: Tipo de post ('reels', 'reels_noite', 'story_manha', 'carousel')
        tema_escolhido: Tema do post (apenas para log, nao altera o visual)
        nome_arquivo: Caminho de saida. Se None, usa nome automatico.

    Returns:
        Caminho absoluto da imagem gerada, ou None se todos os tokens falharem.
    """
    try:
        from gradio_client import Client
    except ImportError:
        logger.warning("[FLUX] gradio_client nao instalado. Pulando geracao por IA.")
        return None

    # Dimensoes por tipo de post
    if tipo == "carousel":
        width, height = 2160, 1080
    else:  # reels, reels_noite, story_manha
        width, height = 1080, 1920

    # Seleciona subtema aleatoriamente a cada postagem (evita repeticao no mesmo dia)
    subtema, cena = random.choice(_MATRIZ_PROMPTS)

    # Seleciona cidade, efeito atmosferico e angulo aleatoriamente (variacao por postagem)
    cidade = random.choice(_CIDADES)
    efeito = random.choice(_EFEITOS_ATMOSFERICOS)
    angulo = random.choice(_ANGULOS)

    prompt = (
        f"Theme: contemporary urban solitude. City: {cidade}, at night.\n"
        f"Subtheme: {subtema}.\n"
        f"{cena}\n"
        f"Atmospheric effect: {efeito}.\n"
        f"Camera angle: {angulo}.\n"
        f"Style: cinematic photography, realistic, 35mm camera, deep depth of field, "
        f"urban night lighting, golden and amber tones mixed with cool shadows, "
        f"Kodak Portra aesthetic, professional photographic quality, highly detailed textures.\n"
        f"No text, logos, watermarks or brands in the image."
    )

    logger.info(f"[FLUX] Subtema: '{subtema}' | Cidade: {cidade} | Efeito: {efeito[:30]}... | Dimensoes: {width}x{height}")


    # Carrega estado para saber qual token usar a seguir
    try:
        from core.config.state import carregar_estado, salvar_estado
        estado = carregar_estado()
        idx_token_inicio = (estado.get("ultimo_hf_token_idx", -1) + 1) % len(HF_TOKENS)
    except Exception:
        estado = {}
        idx_token_inicio = 0

    # Tenta cada token em sequencia a partir do proximo apos o ultimo usado
    for i in range(len(HF_TOKENS)):
        idx_token = (idx_token_inicio + i) % len(HF_TOKENS)
        token = HF_TOKENS[idx_token]
        token_label = f"token {idx_token + 1}"

        # Define o token no ambiente para o gradio_client usar
        os.environ["HF_TOKEN"] = token

        MAX_TENTATIVAS = 3
        for tentativa in range(1, MAX_TENTATIVAS + 1):
            try:
                logger.info(f"[FLUX] Usando {token_label} (tentativa {tentativa}/{MAX_TENTATIVAS})...")

                client = Client("black-forest-labs/FLUX.1-schnell")
                result = client.predict(
                    prompt=prompt,
                    seed=random.randint(0, 2147483647),
                    randomize_seed=True,
                    width=float(width),
                    height=float(height),
                    num_inference_steps=4,
                    api_name="/infer"
                )

                # Extrai o caminho do arquivo gerado
                if isinstance(result, tuple):
                    caminho_temp = result[0]
                elif isinstance(result, dict):
                    caminho_temp = result.get("path") or result.get("url")
                else:
                    caminho_temp = result

                if isinstance(caminho_temp, dict):
                    caminho_temp = caminho_temp.get("path") or caminho_temp.get("url")

                if not caminho_temp or not os.path.exists(str(caminho_temp)):
                    raise ValueError(f"Caminho invalido retornado pelo FLUX: {caminho_temp}")

                # Copia para caminho definitivo
                if nome_arquivo is None:
                    import uuid
                    nome_arquivo = f"flux_bg_{uuid.uuid4().hex}.png"

                shutil.copy(str(caminho_temp), nome_arquivo)
                logger.success(f"[FLUX] Imagem gerada com sucesso via {token_label}! Arquivo: {nome_arquivo}")

                # Salva qual token foi o ultimo usado
                try:
                    estado["ultimo_hf_token_idx"] = idx_token
                    salvar_estado(estado)
                except Exception:
                    pass

                return os.path.abspath(nome_arquivo)

            except Exception as e:
                erro_str = str(e).lower()

                # Erro de cota: pula imediatamente para o proximo token
                if any(kw in erro_str for kw in COTA_EXCEDIDA_KEYWORDS):
                    logger.warning(f"[FLUX] {token_label}: cota excedida. Pulando para proximo token...")
                    break  # Sai do loop de tentativas, vai para o proximo token

                # Outro erro: aguarda e tenta novamente
                logger.warning(f"[FLUX] {token_label} tentativa {tentativa}: {e}")
                if tentativa < MAX_TENTATIVAS:
                    espera = random.randint(3, 5)
                    logger.info(f"[FLUX] Aguardando {espera}s antes de tentar novamente...")
                    time.sleep(espera)
                else:
                    logger.warning(f"[FLUX] {token_label}: esgotou {MAX_TENTATIVAS} tentativas. Pulando...")

    logger.error("[FLUX] Todos os tokens falharam. Acionando fallback (banco de imagens).")
    return None
