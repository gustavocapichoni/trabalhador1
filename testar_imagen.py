"""
TESTE: Verifica se a chave do Gemini tem acesso ao Imagen 3
===========================================================
CORRIGIDO: Usa o pacote novo 'google.genai' (o antigo foi aposentado).
Execute com:  python testar_imagen.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
]
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

if not GEMINI_KEYS:
    print("❌ Nenhuma chave GEMINI_API_KEY encontrada no .env")
    sys.exit(1)

# Verifica se o pacote novo está instalado
try:
    from google import genai
    from google.genai import types
except ImportError:
    print("⚠️  Pacote 'google-genai' não instalado.")
    print("   Rode: pip install google-genai")
    sys.exit(1)

print(f"🔑 Encontradas {len(GEMINI_KEYS)} chave(s) Gemini.")
print("🧪 Testando acesso ao Imagen 3 (pacote google-genai)...\n")

chave_valida = None

for i, chave in enumerate(GEMINI_KEYS, 1):
    print(f"  Testando chave {i}/{len(GEMINI_KEYS)} ({chave[:12]}...)...")
    try:
        client = genai.Client(api_key=chave)

        resultado = client.models.generate_images(
            model="imagen-3.0-generate-001",
            prompt="a serene mountain landscape at golden hour, photorealistic",
            config=types.GenerateImagesConfig(
                number_of_images=1,
                aspect_ratio="9:16",
            ),
        )

        if resultado.generated_images:
            chave_valida = chave
            imagem = resultado.generated_images[0].image
            caminho = "imagen_teste_resultado.png"
            with open(caminho, "wb") as f:
                f.write(imagem.image_bytes)
            print(f"\n✅ SUCESSO! Chave {i} tem acesso ao Imagen 3!")
            print(f"📸 Imagem de teste salva em: {caminho}")
            print(f"   → Abra o arquivo para ver a qualidade da imagem!")
            break
        else:
            print(f"  ⚠️  Chave {i}: Requisição OK, mas nenhuma imagem retornada.")

    except Exception as e:
        erro = str(e)
        if "billing" in erro.lower() or "payment" in erro.lower():
            print(f"  ❌ Chave {i}: Conta sem faturamento ativo (necessário para Imagen)")
        elif "quota" in erro.lower() or "429" in erro:
            print(f"  ⚠️  Chave {i}: Limite de requisições atingido")
        elif "not found" in erro.lower() or "404" in erro:
            print(f"  ❌ Chave {i}: Modelo Imagen não disponível para esta conta/região")
        elif "permission" in erro.lower() or "403" in erro:
            print(f"  ❌ Chave {i}: Sem permissão para usar Imagen")
        elif "invalid" in erro.lower() or "401" in erro:
            print(f"  ❌ Chave {i}: Chave inválida")
        else:
            print(f"  ❌ Chave {i}: {erro[:150]}")

print()
if chave_valida:
    print("=" * 55)
    print("🚀 SUA CONTA TEM ACESSO AO IMAGEN 3!")
    print("   Podemos ativar geração de imagens premium no bot.")
    print("=" * 55)
else:
    print("=" * 55)
    print("❌ Nenhuma chave tem acesso ao Imagen 3.")
    print()
    print("📋 ALTERNATIVAS GRATUITAS:")
    print("  1. Pollinations (já usamos)  — grátis, qualidade ok")
    print("  2. Stability AI              — tem plano gratuito")
    print("  3. Together AI               — $25 crédito grátis")
    print("  4. Fal.ai (Flux)             — imagens excelentes, plano grátis")
    print()
    print("   O bot continuará funcionando normalmente com Pollinations.")
    print("=" * 55)
