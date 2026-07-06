"""
Script de preview: gera o vídeo do Reels Conquistador
sem publicar nada no Instagram.
"""
import sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.ai.gemini import gerar_conteudo_gemini
from core.media.pexels_story import gerar_pexels_story

print("🎬 Gerando preview do Reels Conquistador...")

conteudo, tema, estilo = gerar_conteudo_gemini("reels_conquistador")

slides = conteudo.get("slides", [])
query  = conteudo.get("pexels_query", "cinematic inspiring city")

print(f"\n🎯 Tema: {tema} | Query de vídeo: '{query}'")
print("📝 Slides gerados:")
for i, s in enumerate(slides, 1):
    print(f"  Slide {i}: {s}")

ts = int(time.time())
saida = f"preview_conquistador_{ts}.mp4"

print(f"\n⬇️  Baixando vídeo e montando... (aguarde)")
resultado = gerar_pexels_story(query, slides, caminho_saida=saida, tema=tema)

print(f"\n✅ Vídeo de preview gerado: {resultado}")
print("👀 Abra o arquivo acima para ver como ficou antes de publicar!")
