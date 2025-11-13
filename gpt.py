from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt(question: str, attachments: list):
    # базовый prompt
    input_items = [
        {"role": "user", "content": question}
    ]

    # добавляем файлы
    for a in attachments:
        input_items.append({
            "role": "user",
            "content": {
                "type": "input_file",
                "data": a["data"],
                "mime_type": a["mime_type"],
                "filename": a["filename"]
            }
        })

    # делаем запрос
    resp = client.responses.create(
        model="gpt-5",
        input=input_items
    )

    # Универсальный способ получить текст
    return resp.output_text

