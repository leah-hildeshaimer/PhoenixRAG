
import json
import os
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

with open(
    BASE_DIR / "chunks.json",
    "r",
    encoding="utf-8"
) as file:
    chunks = json.load(file)

# Test only 3 chunks.
test_chunks = chunks[10:13]

texts = [chunk["text"] for chunk in test_chunks]

print("Sending", len(texts), "texts in one request...")

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=texts,
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_DOCUMENT",
        output_dimensionality=768,
    ),
)

embeddings = response.embeddings or []

print("Returned embeddings:", len(embeddings))

if len(embeddings) != len(texts):
    raise RuntimeError("Embedding count mismatch")

for index, embedding in enumerate(embeddings, start=1):
    vector = embedding.values

    if vector is None or len(vector) != 768:
        raise RuntimeError("Invalid vector dimensions")

    print(
        f"Chunk {index}: "
        f"{len(vector)} dimensions"
    )

print("Batch embedding test successful!")
