import os

# Telegram bot token
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Google service account JSON (one-line string from env)
GOOGLE_SERVICE_ACCOUNT = os.getenv("GOOGLE_SERVICE_ACCOUNT")

# Google Drive folder ID with knowledge base
# Можно переопределить через переменную окружения GOOGLE_DRIVE_FOLDER_ID
GOOGLE_DRIVE_FOLDER = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "1zd9w6uiHhIzxI1JXciMXiVZ_aStThcTa")
