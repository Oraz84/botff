# Freedom Assistant Telegram Bot (GPT-5 + Google Drive Semantic RAG)

## Переменные окружения (Render.com)

- TELEGRAM_BOT_TOKEN — токен бота Telegram
- OPENAI_API_KEY — API ключ OpenAI
- GOOGLE_SERVICE_ACCOUNT — JSON сервисного аккаунта Google (одной строкой)
- GOOGLE_DRIVE_FOLDER_ID — (опционально) ID папки Google Drive с базой знаний

## Команда запуска (Start Command)

uvicorn webhook_bot:app --host 0.0.0.0 --port 10000

## Настройка webhook в Telegram

https://api.telegram.org/bot<ТОКЕН>/setWebhook?url=https://<ИМЯ-СЕРВИСА>.onrender.com/webhook
