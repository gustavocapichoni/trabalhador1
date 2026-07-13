"""
Script de preview: gera o vídeo do Reels (Conquistador, Leads, etc)
localmente sem publicar nada no Instagram.
"""
import sys, io, time
import argparse

# Forçar UTF-8 no Windows para suportar emojis no print
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from core.ai.gemini import gerar_conteudo_gemini
from core.media.pexels_story import gerar_pexels_story

parser = argparse.ArgumentParser(description="Script de preview: gera vídeo local sem postar no Instagram")
parser.add_argument("--type", type=str, default="reels_conquistador", 
                    choices=["reels_conquistador", "reels_leads", "pexels_story", "pexels_story_noite"],
                    help="Tipo de reels/video a gerar para preview (default: reels_conquistador)")

args = parser.parse_args()

print(f"🎬 Gerando preview do tipo: {args.type.upper()}...")

conteudo, tema, estilo = gerar_conteudo_gemini(args.type)

slides = conteudo.get("slides", [])
query  = conteudo.get("pexels_query", "cinematic inspiring city")

print(f"\n🎯 Tema: {tema} | Query de vídeo: '{query}'")
print("📝 Slides gerados:")
for i, s in enumerate(slides, 1):
    print(f"  Slide {i}: {s}")

ts = int(time.time())
saida = f"preview_{args.type}_{ts}.mp4"

print(f"\n⬇️  Baixando vídeo e montando... (aguarde)")
resultado = gerar_pexels_story(
    query, 
    slides, 
    caminho_saida=saida, 
    tema=tema,
    is_conquistador=(args.type == "reels_conquistador"),
    is_reels_leads=(args.type == "reels_leads")
)

print(f"\n✅ Vídeo de preview gerado: {resultado}")
print("👀 Abra o arquivo acima para ver como ficou antes de publicar!")
