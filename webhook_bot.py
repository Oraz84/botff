import logging
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

from config import TELEGRAM_BOT_TOKEN
from gpt import ask_gpt
from gdrive import search_files

logging.basicConfig(level=logging.INFO)

app = FastAPI()
bot = Bot(token=TELEGRAM_BOT_TOKEN)
application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

initialized = False


async def init_app():
    global initialized
    if not initialized:
        logging.info("Initializing Telegram application...")
        await application.initialize()
        await application.start()
        initialized = True
        logging.info("Telegram application initialized.")


@app.post("/webhook")
async def webhook_handler(request: Request):
    try:
        await init_app()

        data = await request.json()
        logging.info(f"Webhook update: {data}")

        update = Update.de_json(data, bot)
        await application.process_update(update)

    except Exception as e:
        logging.error(f"Webhook error: {e}", exc_info=True)

    return {"ok": True}


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = None
    try:
        if not update.message:
            return

        question = update.message.text
        chat = update.message.chat_id

        await bot.send_message(chat, "🔎 Ищу документы в Google Drive...")

        files = search_files(question)
        attachments = []
        used = []

        for f in files:
            attachments.append({
                "data": f["data"],
                "mime_type": f["mimeType"],
                "filename": f["name"],
            })
            used.append(f["name"])

        if used:
            await bot.send_message(chat, "📄 Найдены файлы: " + ", ".join(used))

        await bot.send_message(chat, "🤖 Спрашиваю GPT-5...")

        answer = ask_gpt(question, attachments)

        await bot.send_message(chat, answer)

    except Exception as e:
        logging.error(f"Handler error: {e}", exc_info=True)
        if chat is not None:
            await bot.send_message(chat, "❌ Произошла внутренняя ошибка. Смотрю логи.")


application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
