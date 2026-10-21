
import json
import os
import random
import time
import uuid
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai.errors import APIError
from qdrant_client import QdrantClient, models


# ==========================================
# 1. Configuration
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

COLLECTION_NAME = "phoenix_chunks"
EMBEDDING_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 768

CHUNKS_FILE = BASE_DIR / "chunks.json"
PROGRESS_FILE = BASE_DIR / "upload_progress.json"

BATCH_SIZE = 10
REQUEST_DELAY_SECONDS = 3
MAX_RETRIES = 5

# We will test 50 chunks before the full upload.
# This is the TOTAL number of chunks to consider,
# including the 10 already uploaded.
TEST_LIMIT = None

POINT_NAMESPACE = uuid.UUID(
    "8f7269ae-20aa-4e57-9b48-245f39a53140"
)


# ==========================================
# 2. Clients
# ==========================================

gemini_api_key = os.getenv("GEMINI_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not all([gemini_api_key, qdrant_url, qdrant_api_key]):
    raise ValueError("Missing API configuration in .env")

gemini_client = genai.Client(api_key=gemini_api_key)

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
    timeout=60,
)


# ==========================================
# 3. Progress helpers
# ==========================================

def point_id_for_chunk(chunk):
    return str(
        uuid.uuid5(POINT_NAMESPACE, str(chunk["id"]))
    )


def load_progress():
    if not PROGRESS_FILE.exists():
        return {"completed_ids": []}

    with open(PROGRESS_FILE, "r", encoding="utf-8") as file:
        return json.load(file)


def save_progress(completed_ids):
    temporary_file = PROGRESS_FILE.with_suffix(".tmp")

    with open(temporary_file, "w", encoding="utf-8") as file:
        json.dump(
            {"completed_ids": sorted(completed_ids)},
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_file.replace(PROGRESS_FILE)


# ==========================================
# 4. Batch embeddings
# ==========================================

def create_batch_embeddings(texts):
    for attempt in range(MAX_RETRIES):
        try:
            response = gemini_client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=texts,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_DOCUMENT",
                    output_dimensionality=VECTOR_SIZE,
                ),
            )

            embeddings = response.embeddings or []

            if len(embeddings) != len(texts):
                raise RuntimeError(
                    "Gemini returned an unexpected number "
                    "of embeddings"
                )

            vectors = []

            for embedding in embeddings:
                vector = embedding.values

                if vector is None or len(vector) != VECTOR_SIZE:
                    raise RuntimeError(
                        "Invalid embedding dimensions"
                    )

                vectors.append(vector)

            return vectors

        except APIError as error:
            status_code = getattr(error, "code", None)

            if status_code not in (429, 500, 502, 503, 504):
                raise

            if attempt == MAX_RETRIES - 1:
                raise

            delay = min(60, 2 ** (attempt + 1))
            delay += random.uniform(0, 1)

            print(
                f"Gemini error {status_code}. "
                f"Retrying in {delay:.1f}s..."
            )

            time.sleep(delay)

    raise RuntimeError("Batch embedding failed")


# ==========================================
# 5. Upload one batch
# ==========================================

def upload_batch(batch):
    texts = [chunk["text"] for chunk in batch]

    vectors = create_batch_embeddings(texts)

    points = []

    for chunk, vector in zip(batch, vectors):
        points.append(
            models.PointStruct(
                id=point_id_for_chunk(chunk),
                vector=vector,
                payload={
                    "chunk_id": chunk["id"],
                    "text": chunk["text"],
                    "url": chunk["url"],
                    "page_title": chunk["page_title"],
                    "section_title": chunk["section_title"],
                    "chunk_index": chunk["chunk_index"],
                },
            )
        )

    qdrant_client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )

    print(f"Uploaded {len(points)} points to Qdrant")


# ==========================================
# 6. Main
# ==========================================

def main():
    with open(CHUNKS_FILE, "r", encoding="utf-8") as file:
        all_chunks = json.load(file)

    if TEST_LIMIT is None:
        chunks = all_chunks
        print("FULL MODE")
    else:
        chunks = all_chunks[:TEST_LIMIT]
        print(f"TEST MODE: First {len(chunks)} chunks")

    if not qdrant_client.collection_exists(COLLECTION_NAME):
        raise RuntimeError("Qdrant collection does not exist")

    collection_info = qdrant_client.get_collection(
        COLLECTION_NAME
    )

    vector_config = collection_info.config.params.vectors

    if vector_config.size != VECTOR_SIZE:
        raise RuntimeError("Qdrant vector size mismatch")

    completed_ids = set(
        str(chunk_id)
        for chunk_id in load_progress().get("completed_ids", [])
    )

    pending_chunks = [
        chunk
        for chunk in chunks
        if str(chunk["id"]) not in completed_ids
    ]

    print("=" * 50)
    print("PhoenixRAG - Batch Upload")
    print("=" * 50)
    print("Total chunks:", len(all_chunks))
    print("Chunks in this run:", len(chunks))
    print("Already completed:", len(chunks) - len(pending_chunks))
    print("Remaining in this run:", len(pending_chunks))
    print("Batch size:", BATCH_SIZE)
    print("=" * 50)

    for start in range(0, len(pending_chunks), BATCH_SIZE):
        batch = pending_chunks[start:start + BATCH_SIZE]

        print(
            f"\nProcessing batch "
            f"{start // BATCH_SIZE + 1}..."
        )

        upload_batch(batch)

        for chunk in batch:
            completed_ids.add(str(chunk["id"]))

        save_progress(completed_ids)

        print(
            f"Progress: {len(completed_ids)}/{len(all_chunks)}"
        )

        if start + BATCH_SIZE < len(pending_chunks):
            time.sleep(REQUEST_DELAY_SECONDS)

    final_info = qdrant_client.get_collection(
        COLLECTION_NAME
    )

    print("\nUpload process completed!")
    print("Qdrant stored points:", final_info.points_count)


if __name__ == "__main__":
    main()
