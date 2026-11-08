import os

# Pega o token das variáveis de ambiente
# No Render/Railway: configure TELEGRAM_BOT_TOKEN
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "COLOQUE_SEU_TOKEN_AQUI")
