import re

with open('code.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Remove garantir_fonte
code = re.sub(r'def garantir_fonte\(\):.*?return font_path\n', '', code, flags=re.DOTALL)

# Remove criar_imagem_com_texto
code = re.sub(r'def criar_imagem_com_texto\(tipo, dados, tema_escolhido=None\):.*?return caminho_imagem\n', '', code, flags=re.DOTALL)

# Remove feed type from verificar_duplicidade_hoje
code = code.replace('"story": 1,\n        "feed": 1', '"story": 1')

# Remove feed block from gerar_conteudo_gemini
code = re.sub(r'    if tipo == "feed":\n        prompt = f"""[\s\S]*?        """\n    elif tipo == "story":', '    if tipo == "story":', code)

# Update postar_no_instagram feed check
code = code.replace('# 1. Feed estático, Story único, Teste\n    if tipo in ["feed", "story", "test"]:', '# 1. Story único, Teste\n    if tipo in ["story", "test"]:')
code = code.replace('if tipo in ["feed", "test"] and legenda:', 'if tipo == "test" and legenda:')

# Update argparse
code = code.replace('choices=["feed", "story",', 'choices=["story",')

# Update mensagens_sucesso
code = code.replace('        mensagens_sucesso = {\n            "feed": "Começando o dia: sua primeira postagem (Feed) foi feita com sucesso!",\n', '        mensagens_sucesso = {\n')

with open('code.py', 'w', encoding='utf-8') as f:
    f.write(code)
