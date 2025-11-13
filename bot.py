import logging
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram import Update
from config import TELEGRAM_BOT_TOKEN
from gdrive import search_files, download_file
from gpt import ask_gpt

logging.basicConfig(level=logging.INFO)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = update.message.text

    await update.message.reply_text("🔎 Ищу документы в Google Drive...")

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

    await update.message.reply_text("🤖 Спрашиваю GPT-5...")

    answer = ask_gpt(question, attachments)

    result = (
        "📄 Файлы: " + ", ".join(used_files) +
        "\n\n💡 Ответ:\n" + answer
    )

    await update.message.reply_text(result)

def main():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
