from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt(question: str, attachments: list):
    input_items = [{"role": "user", "content": question}]
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
    resp = client.responses.create(model="gpt-5", input=input_items)
    return resp.output_text
