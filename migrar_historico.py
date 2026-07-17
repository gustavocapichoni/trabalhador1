import sys
import os

# Adiciona o diretório atual ao PYTHONPATH para importar os módulos do core
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.config.state import carregar_estado, salvar_estado
from core.analytics.db import get_db

def migrar_historico():
    db = get_db()
    if not db:
        print("❌ Erro: Não foi possível conectar ao Firebase.")
        return

    estado = carregar_estado()
    
    historico = estado.get("historico", [])
    
    print(f"🔄 Iniciando migração de {len(historico)} posts do Instagram...")
    
    batch = db.batch()
    col_ref = db.collection("historico_posts")
    
    count = 0
    for post in historico:
        post_id = post.get("post_id")
        if not post_id or post_id == "ID_TESTE_LOCAL" or post_id.startswith("DRY_RUN"):
            continue
            
        doc_ref = col_ref.document(post_id)
        batch.set(doc_ref, post, merge=True)
        count += 1
        print(f"  - Preparando migração do post: {post_id}")
    
    if count > 0:
        print("⏳ Commitando batch no Firebase...")
        batch.commit()
        print(f"✅ {count} posts migrados com sucesso para a coleção 'historico_posts'!")
    else:
        print("ℹ️ Nenhum post válido para migrar do Instagram.")

    # Remove os campos pesados do bot_config
    if "historico" in estado:
        del estado["historico"]
        
    if "historico_youtube" in estado:
        del estado["historico_youtube"]
        
    print("🧹 Removendo campos 'historico' e 'historico_youtube' do bot_config...")
    salvar_estado(estado)
    
    # Precisamos deletar do firebase também
    try:
        doc_ref = db.collection("bot_config").document("app_state")
        doc_ref.update({
            "historico": firestore.DELETE_FIELD,
            "historico_youtube": firestore.DELETE_FIELD
        })
    except Exception as e:
        pass # Pode não existir no firebase ainda
    
    print("🚀 MIGRAÇÃO CONCLUÍDA COM SUCESSO!")

if __name__ == "__main__":
    from google.cloud import firestore
    migrar_historico()
