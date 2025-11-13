import io
import json
import time

import numpy as np
from pypdf import PdfReader
from docx import Document
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from openai import OpenAI
from config import GOOGLE_SERVICE_ACCOUNT, GOOGLE_DRIVE_FOLDER, OPENAI_API_KEY

# Инициализация OpenAI для эмбеддингов
client = OpenAI(api_key=OPENAI_API_KEY)

# ===========================================
# Google Drive Init
# ===========================================

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

if not GOOGLE_SERVICE_ACCOUNT:
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT env var is not set")

SERVICE_ACCOUNT_INFO = json.loads(GOOGLE_SERVICE_ACCOUNT)

creds = Credentials.from_service_account_info(SERVICE_ACCOUNT_INFO, scopes=SCOPES)
drive = build("drive", "v3", credentials=creds)

# ===========================================
# Caching
# ===========================================

CACHE_META_TTL = 600       # 10 мин — кэш списка файлов
CACHE_EMB_TTL = 3600 * 24  # 24 часа — кэш эмбеддингов

CACHE_META = {"timestamp": 0, "items": []}
CACHE_EMB = {}


# ===========================================
# Load File List
# ===========================================

def load_file_list():
    """Загружаем список файлов из папки Google Drive с кэшированием."""
    now = time.time()

    if now - CACHE_META["timestamp"] < CACHE_META_TTL:
        return CACHE_META["items"]

    query = f"'{GOOGLE_DRIVE_FOLDER}' in parents and trashed = false"
    results = drive.files().list(
        q=query,
        fields="files(id,name,mimeType)"
    ).execute()

    files = results.get("files", [])
    CACHE_META["timestamp"] = now
    CACHE_META["items"] = files

    return files


# ===========================================
# Download File
# ===========================================

def download_file_raw(file_id: str) -> bytes:
    """Скачиваем файл из Google Drive в виде байтов."""
    request = drive.files().get_media(fileId=file_id)
    return request.execute()


# ===========================================
# Extract Text from File
# ===========================================

def extract_text(file_bytes: bytes, mime: str, filename: str) -> str:
    """
    Пытаемся извлечь текст из файла.
    Поддерживаем:
      - text/plain
      - application/pdf
      - application/vnd.openxmlformats-officedocument.wordprocessingml.document (DOCX)
    Остальное считаем бинарным и не индексируем.
    """
    if mime == "text/plain":
        return file_bytes.decode("utf-8", errors="ignore")

    if mime == "application/pdf":
        try:
            reader = PdfReader(io.BytesIO(file_bytes))
            texts = []
            for page in reader.pages:
                page_text = page.extract_text() or ""
                texts.append(page_text)
            return "\n".join(texts)
        except Exception:
            return ""

    if mime == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        try:
            doc = Document(io.BytesIO(file_bytes))
            return "\n".join(p.text for p in doc.paragraphs)
        except Exception:
            return ""

    # Фоллбек: остальные типы не индексируем
    return ""


# ===========================================
# Embeddings
# ===========================================

def embed_text(text: str):
    """Получаем эмбеддинг для текста через OpenAI."""
    text = (text or "").strip()
    if not text:
        return None

    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text[:15000],  # ограничиваем длину
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)


# ===========================================
# Build index: text + embeddings
# ===========================================

def build_embedding_for_file(file_meta: dict) -> dict:
    """
    Создаём/обновляем embedding для файла.
    file_meta: dict с ключами id, name, mimeType.
    """
    now = time.time()
    file_id = file_meta["id"]
    mime = file_meta.get("mimeType", "")
    name = file_meta.get("name", "")

    # Если в кэше есть свежий embedding — возвращаем его
    if file_id in CACHE_EMB:
        entry = CACHE_EMB[file_id]
        if now - entry["ts"] < CACHE_EMB_TTL:
            return entry

    # Иначе скачиваем файл и извлекаем текст
    raw_bytes = download_file_raw(file_id)
    text = extract_text(raw_bytes, mime, name)
    emb = embed_text(text)

    entry = {
        "id": file_id,
        "name": name,
        "mime": mime,
        "text": text,
        "embedding": emb,
        "ts": now,
    }

    CACHE_EMB[file_id] = entry
    return entry


# ===========================================
# Semantic Search
# ===========================================

def semantic_search(query: str, top_k: int = 3):
    """Возвращает top_k самых релевантных файлов по смыслу."""
    files = load_file_list()
    if not files:
        return []

    q_emb = embed_text(query)
    if q_emb is None:
        return []

    results = []

    for f in files:
        entry = build_embedding_for_file(f)
        emb = entry.get("embedding")
        if emb is None:
            continue

        denom = float(np.linalg.norm(q_emb) * np.linalg.norm(emb))
        if denom == 0.0:
            continue

        score = float(np.dot(q_emb, emb) / denom)
        results.append((score, entry))

    # сортируем по убыванию похожести
    results.sort(key=lambda x: x[0], reverse=True)

    return [entry for score, entry in results[:top_k]]


# ===========================================
# API для webhook_bot.py
# ===========================================

def search_files(query: str):
    """
    Интерфейс для бота.
    Возвращает список словарей формата:
    {
        "id": ...,
        "name": ...,
        "mimeType": ...,
        "data": <bytes>,
    }
    """
    entries = semantic_search(query, top_k=3)
    results = []

    for e in entries:
        raw = download_file_raw(e["id"])
        results.append(
            {
                "id": e["id"],
                "name": e["name"],
                "mimeType": e["mime"],
                "data": raw,
            }
        )

    return results
