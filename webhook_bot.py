import logging
from fastapi import FastAPI, Request
from telegram import Update, Bot
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)
from config import TELEGRAM_BOT_TOKEN
from gpt import ask_gpt
from gdrive import search_files, download_file

logging.basicConfig(level=logging.INFO)

app = FastAPI()

# Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()


# --------------------------
# INIT TELEGRAM APPLICATION
# --------------------------
initialized = False


async def init_telegram_app():
    global initialized
    if not initialized:
        await application.initialize()
        await application.start()
        initialized = True


# --------------------------
# WEBHOOK ENDPOINT
# --------------------------
@app.post("/webhook")
async def webhook_handler(request: Request):
    await init_telegram_app()

    data = await request.json()
    update = Update.de_json(data, bot)

    await application.process_update(update)

    return {"ok": True}


# --------------------------
# MESSAGE HANDLER
# --------------------------
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    question = update.message.text
    chat = update.message.chat_id

    await bot.send_message(chat, "🔎 Ищу документы в Google Drive...")

    files = search_files(question)
    attachments = []
    used_files = []

    for f in files[:3]:
        data = download_file(f["id"])
        attachments.append({
            "data": data,
            "mime_type": f["mimeType"],
            "filename": f["name"]
        })
        used_files.append(f["name"])

    await bot.send_message(chat, "🤖 Спрашиваю GPT-5...")

    answer = ask_gpt(question, attachments)

    result = (
        "📄 Файлы: " + ", ".join(used_files) +
        "\n\n💡 Ответ:\n" + answer
    )

    await bot.send_message(chat, result)


# Register handler
application.add_handler(
    MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
)
