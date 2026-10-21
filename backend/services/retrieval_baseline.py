
import os

from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

COLLECTION_NAME = "phoenix_chunks"
EMBEDDING_MODEL = "gemini-embedding-001"
VECTOR_SIZE = 768

gemini_api_key = os.getenv("GEMINI_API_KEY")
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if not all([gemini_api_key, qdrant_url, qdrant_api_key]):
    raise RuntimeError("Missing API configuration in backend/.env")

gemini_client = genai.Client(api_key=gemini_api_key)

qdrant_client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
    timeout=60,
)


def search_chunks(question: str, limit: int = 5) -> list[dict]:
    """
    Search Qdrant for Phoenix website excerpts
    relevant to the user's question.
    """

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=VECTOR_SIZE,
        ),
    )

    if not response.embeddings:
        raise RuntimeError("Gemini returned no query embedding")

    query_vector = response.embeddings[0].values

    if query_vector is None or len(query_vector) != VECTOR_SIZE:
        raise RuntimeError("Invalid query embedding dimensions")

    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
    )

    chunks = []

    for point in results.points:
        payload = point.payload or {}

        if not payload.get("text"):
            continue

        chunks.append({
            "id": payload.get("chunk_id"),
            "text": payload.get("text", ""),
            "url": payload.get("url", ""),
            "page_title": payload.get("page_title", ""),
            "section_title": payload.get("section_title", ""),
            "chunk_index": payload.get("chunk_index"),
            "score": point.score,
        })

    return chunks


def build_context(chunks: list[dict]) -> str:
    """
    Format retrieved chunks as source excerpts for Gemini.
    """

    sections = []

    for index, chunk in enumerate(chunks, start=1):
        text = chunk.get("text", "").strip()

        if not text:
            continue

        title = chunk.get("page_title", "")
        url = chunk.get("url", "")
        section_title = chunk.get("section_title", "")

        sections.append(
            f"""
[SOURCE {index}]
Title: {title}
Section: {section_title}
URL: {url}
Content:
{text}
[/SOURCE {index}]
"""
        )

    return "\n".join(sections)
