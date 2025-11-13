from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY)

def ask_gpt(question: str, attachments: list):
    resp = client.responses.create(
        model="gpt-5",
        input=question,
        attachments=attachments
    )
    return resp.output[0].content[0].text
