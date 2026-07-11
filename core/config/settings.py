import os
from dotenv import load_dotenv

# Carrega as variáveis do arquivo .env localmente, forçando sobrescrita
load_dotenv(override=True)

# ==========================================
# CHAVES DE API - GEMINI (ROTAÇÃO)
# ==========================================
GEMINI_KEYS = [
    os.getenv("GEMINI_API_KEY_1"),
    os.getenv("GEMINI_API_KEY_2"),
    os.getenv("GEMINI_API_KEY_3"),
    os.getenv("GEMINI_API_KEY_4"),
    os.getenv("GEMINI_API_KEY_5"),
]

# Remove chaves None/vazias caso alguma não tenha sido preenchida
GEMINI_KEYS = [k for k in GEMINI_KEYS if k]

# ==========================================
# CHAVES DE API - GROQ (BACKUP DO GEMINI)
# ==========================================
GROQ_KEYS = [
    os.getenv("GROQ_API_KEY_1"),
    os.getenv("GROQ_API_KEY_2"),
]
GROQ_KEYS = [k for k in GROQ_KEYS if k]

# ==========================================
# CHAVE DE API - OPENROUTER (BACKUP FINAL)
# ==========================================
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")


# ==========================================
# CHAVES DE API - MÍDIA E VOZ
# ==========================================
PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")
PIXABAY_API_KEY = os.getenv("PIXABAY_API_KEY")
UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
# ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY") # Futuro

# ==========================================
# CREDENCIAIS DO INSTAGRAM (META GRAPH API)
# ==========================================
IG_ACCESS_TOKEN = os.getenv("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.getenv("IG_ACCOUNT_ID")

# ==========================================
# CREDENCIAIS DE E-MAIL (SMTP)
# ==========================================
SMTP_EMAIL = os.getenv("SMTP_EMAIL")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL")
