
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient, models

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "phoenix_chunks"
EMBEDDING_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 768

if not all([GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
    raise ValueError("Missing API configuration in .env")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30,
)

with open(BASE_DIR / "chunks.json", "r", encoding="utf-8") as file:
    chunks = json.load(file)

test_chunks = chunks[:5]

print(f"Loaded {len(chunks)} chunks.")
print(f"Uploading {len(test_chunks)} test chunks...")

points = []

for index, chunk in enumerate(test_chunks):
    text = chunk["text"]

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=VECTOR_SIZE,
        ),
    )

    vector = response.embeddings[0].values

    if len(vector) != VECTOR_SIZE:
        raise ValueError("Unexpected embedding dimensions")

    point = models.PointStruct(
        id=index + 1,
        vector=vector,
        payload={
            "chunk_id": chunk["id"],
            "text": text,
            "url": chunk["url"],
            "page_title": chunk["page_title"],
            "section_title": chunk["section_title"],
            "chunk_index": chunk["chunk_index"],
        },
    )

    points.append(point)
    print(f"Embedding {index + 1}/{len(test_chunks)} created.")

qdrant_client.upsert(
    collection_name=COLLECTION_NAME,
    points=points,
    wait=True,
)

collection_info = qdrant_client.get_collection(COLLECTION_NAME)

print("Upload completed successfully!")
print("Stored points:", collection_info.points_count)
