# 🔍 Auditoria Completa do Bot — GUSTAVO_8K_

> Realizada em: 12/07/2026 · Todos os arquivos do projeto foram revisados.

---

## 🟢 O QUE ESTÁ FUNCIONANDO BEM

| Área | Descrição |
|---|---|
| **Fallback de IA** | Gemini → Groq → OpenRouter → Mensagens de Emergência. Cadeia sólida e robusta. |
| **Fallback de Upload** | catbox.moe → litterbox → file.io → tmpfiles.org → transfer.sh. Excelente. |
| **Fallback de Imagem** | Pollinations AI (Flux) → Unsplash → Biblioteca Local → Fundo Sólido. Ótimo. |
| **Retry do Instagram** | Sistema com backoff exponencial e mapa de erros conhecidos (190, 9007, 2207027). |
| **Estado/Firebase** | Dupla gravação (local + nuvem) com recuperação de emergência offline. |
| **Rotação de Temas** | Sistema sequencial diário com histórico para evitar repetição de ângulos e estilos. |
| **Anti-repetição** | `historico_angulos`, `historico_ganchos`, `historico_estilos` funcionando. |
| **Limpeza de Recursos** | Blocos `finally` com `close()` nas MoviePy clips para evitar WinError 32. |
| **Rotação de Músicas** | Rodízio de MP3s com memória das últimas 5 faixas. |
| **Marca d'água** | `GUSTAVO_8K_` em dourado padronizada em todos os formatos (Reels, Carrossel, Pexels Story). |

---

## 🔴 BUGS CONFIRMADOS E RISCOS CRÍTICOS

### 🔴 BUG 1 — `motor_visual.py`: Função `_gerar_carrossel` duplicada no arquivo
**Arquivo:** [motor_visual.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/design/motor_visual.py) — linha 169 e linha 214

A função `_gerar_carrossel` está **definida duas vezes** no mesmo arquivo. A que aparece primeiro (L169) é incompleta — termina no meio, sem corpo. A segunda (L214) é a versão completa. 

Python usa **somente a última definição**, então o bug "funciona por acidente" agora, mas é um código morto e confuso que pode causar problema no futuro caso alguém edite a primeira versão sem perceber que há uma segunda.

**Solução:** Apagar as linhas 169–196 (a versão incompleta/fantasma) e manter apenas a versão correta da L214.

---

### 🔴 BUG 2 — `pexels_story.py`: Variáveis não inicializadas no `except`
**Arquivo:** [pexels_story.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/media/pexels_story.py) — linhas 517–521 e 542–546

No bloco `except Exception`, o código tenta fechar `clip`, `final_clip` e `bg_audio`:
```python
if clip: clip.close()
if final_clip: final_clip.close()
if bg_audio: bg_audio.close()
```
Se o erro acontecer **antes** de qualquer uma dessas variáveis ser atribuída (ex: erro na linha `clip = VideoFileClip(...)`), o Python lança um `NameError: name 'clip' is not defined`, que **esmaga o erro real** e deixa o log confuso.

**Solução:** Inicializar `clip = None`, `final_clip = None`, `bg_audio = None` no topo da função antes do `try`.

---

### 🔴 BUG 3 — `instagram.py`: Retorno `None` silencioso no fluxo de Reels
**Arquivo:** [instagram.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/publisher/instagram.py) — linha 267

```python
published_id = res_publish_json['id']  # CRASH se res_publish_json for None
```

A função `_publicar_com_retry` pode retornar `None` quando o erro é do tipo `skip` (código 9007 — Story expirado). Para Stories, isso é tratado. Mas no fluxo de Reels (L267), o código assume que `res_publish_json` sempre terá `['id']`, sem checar se é `None`. Se um Reel receber um erro 9007 (improvável mas possível), o bot crasha com `TypeError`.

**Solução:** Adicionar `if res_publish_json is None: return None` antes da L267.

---

### 🟡 RISCO 4 — `reels.py`: Uso inconsistente de API do MoviePy
**Arquivo:** [reels.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/media/reels.py) — linhas 68–70 e 89–98

O código tenta importar `concatenate_videoclips` de duas formas diferentes e aplica efeitos com dois métodos diferentes (`with_effects([FadeIn...])` vs `.fx(vfx.fadein...)`). Isso cobre versões 1.x e 2.x do MoviePy mas o código é frágil — se nenhuma das duas funcionar, o `except` silencia o erro sem efeito de fade (o `pass` na L98 descarta o erro sem log).

**Solução:** Adicionar um `logger.warning` no `except` do fallback de efeitos para rastrear quando o fade não foi aplicado.

---

### 🟡 RISCO 5 — `motor_visual.py`: URL da Pollinations sem encode do prompt
**Arquivo:** [motor_visual.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/design/motor_visual.py) — linha 47

```python
url_pollinations = f"https://image.pollinations.ai/prompt/{ai_prompt}?width=..."
```

O `ai_prompt` é inserido diretamente na URL **sem URL-encoding**. Se o prompt tiver caracteres especiais como `&`, `?`, `#`, `/` ou acentos, a URL ficará malformada e a API da Pollinations retornará erro ou ignorará parte do prompt.

**Solução:** Usar `requests.utils.quote(ai_prompt)` antes de inserir na URL.

---

### 🟡 RISCO 6 — `gemini.py`: Código duplicado em 3 lugares (injeção de prompt_imagem e hashtags)
**Arquivo:** [gemini.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/gemini.py) — linhas 698–707, 741–749, 774–782

O bloco que injeta `prompt_imagem` e as hashtags na legenda está **copiado e colado 3 vezes** (Gemini, Groq, OpenRouter). Se precisar modificar essa lógica (ex: mudar a lista `tipos_imagem`), terá que alterar em 3 lugares — alto risco de bug por esquecimento.

**Solução:** Extrair para uma função `_pos_processar_dados(dados, tipo, tema_key, detalhes_tema)` e chamar nas 3 branches.

---

### 🟡 RISCO 7 — `uploader.py`: `file.io` apaga o arquivo após o primeiro download
**Arquivo:** [uploader.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/publisher/uploader.py) — linha 128

O `file.io` é um serviço de **"1 download único"**. Quando o Instagram fizer o download da mídia, o link expira imediatamente. Se o Instagram tentar revalidar ou acessar novamente (o que acontece durante o processamento de container), o arquivo já não estará disponível e a postagem falhará silenciosamente com erro 2207027.

**Solução:** Mover o `file.io` para o final da lista de fallbacks (antes do `transfer.sh`), priorizando serviços com links permanentes.

---

## 🟠 OPORTUNIDADES DE MELHORIA (NÃO SÃO BUGS, MAS VALEM A PENA)

### ⚡ MELHORIA 1 — Pexels Story: `typewriter` na última cena (CTA) pode cortar a mensagem
No CTA (último slide), se a animação `typewriter` for sorteada, o texto só aparece completamente nos últimos segundos do slide. Como o CTA precisa que a pessoa leia e tome ação ("Segue o perfil", "Link na bio"), animações lentas prejudicam a conversão.

**Sugestão:** Forçar `animacao_slide = "static"` para o slide do CTA (último slide), assim como já fazemos para o Slide 0 (gancho).

---

### ⚡ MELHORIA 2 — Carrossel: CTA fixo "Gostou deste conteúdo? Salva para não perder"
**Arquivo:** [motor_visual.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/design/motor_visual.py) — linha 259

O CTA do carrossel é sempre o mesmo texto hard-coded. Com o tempo, isso vai parecer repetitivo e mecânico para os seguidores que veem seus posts com frequência.

**Sugestão:** Criar uma lista com 5–8 variações de CTA que o sistema escolha aleatoriamente a cada carrossel gerado.

---

### ⚡ MELHORIA 3 — Carrossel: largura do texto na capa muito estreita (width=15)
**Arquivo:** [motor_visual.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/design/motor_visual.py) — linha 251

```python
linhas = textwrap.wrap(texto, width=15)
```
`width=15` significa que o título só pode ter 15 caracteres por linha, o que quebra títulos de 3–4 palavras em muitas linhas e pode ultrapassar a altura do slide. O sistema de Reels/Story usa quebra por pixels (mais preciso), mas o Carrossel ainda usa `width` em caracteres.

**Sugestão:** Substituir o `textwrap.wrap(width=15)` pelo sistema `_quebrar_texto_por_pixels` que já existe no `pexels_story.py`, ou ao menos aumentar para `width=18`.

---

### ⚡ MELHORIA 4 — `gemini.py`: Story simples não tem legenda
**Arquivo:** [gemini.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/gemini.py) — linha 149–153

O tipo `story` só retorna `{"frase": "..."}`, sem campo `legenda`. Quando o Instagram processa um Story, a legenda não é exibida, então faz sentido. Mas no `main.py` (L146), `conteudo.get("legenda", "")` retornará string vazia, e isso é enviado ao Instagram como caption vazio — tecnicamente inofensivo, mas pode ser aproveitado para fins de rastreamento de hashtags em stories de conteúdo.

---

### ⚡ MELHORIA 5 — Texto de "1 / N" no Reels fica na área do nome de usuário do Instagram
**Arquivo:** [motor_visual.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/design/motor_visual.py) — linha 294

```python
draw_text_with_shadow(draw, (W/2, H - 220), f"{idx+1} / {len(frases)}", ...)
```
`H - 220` e `H - 150` (marca d'água) ficam na faixa de `y = 1700–1770` em um vídeo de 1920px. A barra de progresso/curtida do Instagram aparece nessa região nos Reels. O texto pode ficar escondido atrás da interface do app.

**Sugestão:** Mover o contador para `H - 280` e a marca d'água para `H - 200`.

---

## 📋 RESUMO EXECUTIVO

| Prioridade | Item | Arquivo | Ação |
|---|---|---|---|
| 🔴 CRÍTICO | Função `_gerar_carrossel` duplicada | motor_visual.py | Remover a cópia fantasma (L169–196) |
| 🔴 CRÍTICO | Variáveis não inicializadas no `except` | pexels_story.py | Inicializar `clip = final_clip = bg_audio = None` |
| 🔴 CRÍTICO | `res_publish_json['id']` sem check de `None` | instagram.py | Adicionar guard `if res_publish_json is None` |
| 🟡 MÉDIO | URL da Pollinations sem encode | motor_visual.py | `requests.utils.quote(ai_prompt)` |
| 🟡 MÉDIO | `file.io` expira no 1º download | uploader.py | Mover `file.io` para depois de `tmpfiles.org` |
| 🟡 MÉDIO | Código de injeção duplicado 3x | gemini.py | Extrair para função auxiliar |
| 🟡 MÉDIO | Fade do MoviePy silenciado sem log | reels.py | Adicionar `logger.warning` no except |
| 🟢 MELHORIA | CTA do Carrossel sempre igual | motor_visual.py | Randomizar entre 6–8 variações |
| 🟢 MELHORIA | CTA do Pexels Story animado lentamente | pexels_story.py | Forçar `static` no último slide |
| 🟢 MELHORIA | Texto de contador na frente da UI do IG | motor_visual.py | Mover para `H - 280` |

