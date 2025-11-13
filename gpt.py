from openai import OpenAI
from config import OPENAI_API_KEY

# Инициализация клиента OpenAI
client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# FREEDOM ASSISTANT — системный промпт
# ============================================================

SYSTEM_PROMPT = """
Ты — Freedom Assistant, интеллектуальный помощник экосистемы Freedom Holding Corp.
Ты работаешь как эксперт по всем направлениям холдинга и одновременно используешь
подключённую базу знаний из Google Drive (RAG) через файлы, которые передаются в запросе.

Твоя логика ответов:

=====================================================================
1) Если предоставлены файлы (из Google Drive):
=====================================================================
- Рассматривай их как приоритетный источник информации.
- Используй текст из файлов прежде всего.
- Если файлы содержат тарифы, правила, инструкции, описания —
  основывай ответ на них.
- В ответе указывай: "На основе данных из подключённой базы знаний..."

=====================================================================
2) Если файлов нет:
=====================================================================
Отвечай на основе собственных знаний модели GPT-5 об экосистеме Freedom:

- Freedom Bank: карты, тарифы, обслуживание, лимиты, депозиты
- Freedom Finance / Freedom Broker: инвестиции, комиссии, ИИС
- Freedom Insurance: ОГПО, КАСКО, страхование имущества
- Freedom Life: страхование жизни
- Arbuz.kz: логика каталога, примерные диапазоны цен
- Ticketon / Aviata / путешествия: примерные цены на билеты
- Freedom Pay / Freedom Mobile / Freedom Market и т.д.

=====================================================================
3) Правила ответа:
=====================================================================
- Форматируй текст красиво: заголовки, списки, таблицы.
- Если даёшь цены — делай разумные ориентиры.
- Если не уверен — указывай диапазон.
- Не придумывай несуществующие продукты или точные цифры.
- Если вопрос сложный — делай краткий анализ.
=====================================================================
"""


# ============================================================
# Конвертация документа из Google Drive в текст
# ============================================================

def _attachments_to_text(attachments):
    """
    attachments = список:
    [
        {
            "data": b"...",            # содержимое файла
            "mime_type": "text/plain"  # MIME тип
            "filename": "file.txt"     # имя файла
        }
    ]
    """

    if not attachments:
        return ""

    result_parts = []
    total_limit = 20000  # общая длина текста, чтобы не разрастался prompt
    consumed = 0

    for att in attachments:
        raw = att.get("data", b"")
        name = att.get("filename", "file")
        mime = att.get("mime_type", "application/octet-stream")

        # Пытаемся декодировать текст
        try:
            text = raw.decode("utf-8", errors="ignore")
        except Exception:
            text = ""

        # Если бинарный файл — только заголовок
        if not text.strip():
            snippet = f"[Файл {name} ({mime}) — бинарный, текст извлечь нельзя]\n"
        else:
            if len(text) > 4000:
                text = text[:4000] + "\n...[обрезано]"
            snippet = f"===== Файл: {name} ({mime}) =====\n{text}\n\n"

        if consumed + len(snippet) > total_limit:
            result_parts.append("\n[Часть файлов не включена — превышен лимит текста]\n")
            break

        result_parts.append(snippet)
        consumed += len(snippet)

    return "".join(result_parts)


# ============================================================
# Главная функция: запрос к GPT-5
# ============================================================

def ask_gpt(question, attachments):
    """
    question: строка
    attachments: список файлов Google Drive, см. _attachments_to_text
    """

    # Конвертация файлов в текст
    files_text = _attachments_to_text(attachments)

    # Готовим тело запроса
    if files_text:
        user_text = (
            f"Вопрос пользователя:\n{question}\n\n"
            f"Ниже приведено содержимое файлов из базы знаний Google Drive:\n\n"
            f"{files_text}"
        )
    else:
        user_text = question

    # Формируем messages
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": user_text}
    ]

    # Выполняем запрос
    response = client.responses.create(
        model="gpt-5",
        input=messages
    )

    # Возвращаем текст
    return response.output_text
