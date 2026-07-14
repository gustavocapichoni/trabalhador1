# Plano de Ação: Correção das Vulnerabilidades do Bot Instagram

Este plano visa solucionar as falhas críticas identificadas no bot para torná-lo mais estável, seguro e à prova de bloqueios pelo Instagram.

## Perguntas para o Usuário
> [!IMPORTANT]
> 1. Você tem acesso e controle ao console do seu projeto do **Firebase**? Para migrarmos os uploads do Catbox para o Firebase Storage, precisaremos de um Bucket ativo no painel do Firebase.
> 2. Para a notificação de e-mails, você prefere manter o SMTP do Gmail (que exige a configuração correta da "Senha de Aplicativo") ou prefere que integremos um serviço gratuito de envio de e-mails transacionais (como Brevo ou SendGrid)?

## Propostas de Alterações

---

### Componente 1: Armazenamento Seguro de Mídia (Firebase Storage)
Substituir os sites públicos de upload temporário pelo Firebase Storage do próprio projeto, que é seguro, privado e confiável.
> **Termo Técnico — Firebase Storage:** Serviço seguro da nuvem do Google que serve para guardar arquivos grandes (como fotos e vídeos) com alta velocidade e controle de acesso.

#### [MODIFY] [uploader.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/publisher/uploader.py)
* Criar a função `upload_firebase_storage(caminho_arquivo)` usando o SDK do Firebase Admin que já está inicializado no projeto.
* Retornar a URL pública gerada no Firebase com token temporário de leitura para que a API do Instagram consiga baixar a mídia.
* Manter os provedores antigos (Catbox/Litterbox) apenas como fallbacks secundários caso o Firebase Storage esteja offline.

---

### Componente 2: Estabilidade no Processamento de Vídeo (Liberação de Memória)
Prevenir erros do Windows de arquivo em uso (`WinError 32`) e vazamentos de memória na edição de vídeo.
> **Termo Técnico — Coletor de Lixo (Garbage Collector):** O sistema automático da linguagem de programação que limpa da memória RAM do computador os arquivos e dados que o bot não está mais usando.

#### [MODIFY] [reels.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/media/reels.py)
* Reescrever a criação de clipes usando blocos `with` ou adicionando chamadas explícitas de `.close()` para todos os objetos do MoviePy (ImageClip, AudioFileClip, VideoClip) em blocos `finally`.
* Adicionar um pequeno atraso (`time.sleep(1)`) antes de tentar deletar os arquivos temporários em disco, garantindo que o sistema operacional finalizou as conexões de escrita e leitura do arquivo.

#### [MODIFY] [pexels_story.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/media/pexels_story.py)
* Garantir o fechamento de todos os subclipes de vídeo temporários baixados das APIs públicas antes de tentar apagá-los do disco rígido.

---

### Componente 3: Tratamento de Limites e Roleta do Gemini
Evitar travamento do bot por esgotamento de APIs e evitar a postagem de conteúdo repetitivo e estático de emergência.
> **Termo Técnico — Cooldown (Tempo de Resfriamento):** Tempo de espera temporário imposto a um recurso (como uma chave de API) que atingiu seu limite de uso, para que ela possa se recuperar antes de ser usada novamente.

#### [MODIFY] [gemini.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/ai/gemini.py)
* Implementar um registro de "tempo de resfriamento" (*cooldown*) no estado do bot para qualquer chave que retornar erro HTTP 429 (Rate Limit). O bot ignorará essa chave nas execuções das próximas 3 horas, pulando direto para a próxima válida.

---

### Componente 4: Sincronização Obrigatória de Estado
Garantir que execuções locais e na nuvem compartilhem a mesma memória, evitando posts de temas ou músicas idênticas.

#### [MODIFY] [state.py](file:///c:/Users/kali/Desktop/my-bot-instagram-main/core/config/state.py)
* Tornar a sincronização com o Firebase obrigatória no início de cada execução importante do bot.
* Se a sincronização com a nuvem falhar por rede, o bot deverá alertar sobre o problema e tentar subir as alterações locais assim que a rede se restabelecer.

## Plano de Verificação

### Testes Manuais
- Rodar o script `main.py` com o parâmetro `--dry-run` para verificar se as chaves da API do Gemini selecionam os temas corretos considerando o cooldown.
- Gerar um vídeo de Reels de teste e validar se os arquivos temporários são limpos corretamente do disco sem gerar o erro `WinError 32`.
- Validar no painel do Firebase Console se as mídias temporárias enviadas pelo novo `uploader.py` aparecem na aba Storage.
