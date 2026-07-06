"""
Módulo TTS (Text-to-Speech) — Voz Profissional para o Bot
==========================================================
Usa a rede neural GRATUITA da Microsoft (edge-tts) para transformar
o texto da copy do Gemini em áudio com voz hiper-realista.

Vozes disponíveis (pt-BR):
  - pt-BR-AntonioNeural : Masculino, grave e sério (nosso padrão)
  - pt-BR-FranciscaNeural: Feminino, clara e profissional
"""
import asyncio
import os
import random

try:
    import edge_tts
    TTS_DISPONIVEL = True
except ImportError:
    TTS_DISPONIVEL = False

# Vozes configuradas por "energia" do post
VOZES = {
    "masculino_agressivo": "pt-BR-AntonioNeural",
    "feminino_firme":      "pt-BR-FranciscaNeural",
}

# Taxas de fala: +20% mais rápido para posts agressivos, normal para reflexivos
VELOCIDADES = {
    "agressivo": "+15%",
    "reflexivo": "+0%",
    "provocativo": "+10%",
}

async def _gerar_audio_async(texto: str, caminho_saida: str, voz: str, velocidade: str):
    """Função interna assíncrona do edge-tts."""
    communicate = edge_tts.Communicate(
        text=texto,
        voice=voz,
        rate=velocidade
    )
    await communicate.save(caminho_saida)

def gerar_narracao(
    texto: str,
    caminho_saida: str = "narracao.mp3",
    estilo: str = "agressivo"
) -> str | None:
    """
    Gera um arquivo de áudio narrado a partir de um texto.

    Args:
        texto:         O texto a ser narrado (copy do Gemini).
        caminho_saida: Caminho para salvar o .mp3 gerado.
        estilo:        'agressivo', 'reflexivo' ou 'provocativo'.

    Returns:
        O caminho do arquivo de áudio gerado, ou None se falhar.
    """
    if not TTS_DISPONIVEL:
        print("⚠️ [TTS] Biblioteca edge-tts não instalada. Pulando narração.")
        return None

    # Sorteia a voz entre masculino e feminino (para variedade)
    voz = random.choice(list(VOZES.values()))
    velocidade = VELOCIDADES.get(estilo, "+0%")

    print(f"🎙️ [TTS] Gerando narração com voz '{voz}' (estilo: {estilo})...")
    print(f"📝 Texto: \"{texto[:80]}...\"")

    try:
        asyncio.run(_gerar_audio_async(texto, caminho_saida, voz, velocidade))
        tamanho = os.path.getsize(caminho_saida) if os.path.exists(caminho_saida) else 0
        if tamanho > 0:
            print(f"✅ [TTS] Narração salva em: {caminho_saida} ({tamanho // 1024} KB)")
            return caminho_saida
        else:
            print("⚠️ [TTS] Arquivo gerado está vazio. Pulando narração.")
            return None
    except Exception as e:
        print(f"⚠️ [TTS] Erro ao gerar narração: {e}. Continuando sem voz.")
        return None

def concatenar_slides_para_narracao(slides: list[str]) -> str:
    """
    Junta todos os slides em um texto corrido para narração contínua.
    Adiciona uma pausa natural entre os slides com '...'
    """
    return " ... ".join(slides)
