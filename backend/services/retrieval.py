
import os
import re
import time

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


def tokenize_hebrew(text: str) -> set[str]:
    """
    Extract meaningful Hebrew and English words.
    """
    words = re.findall(r"[\u0590-\u05FFa-zA-Z0-9]+", text.lower())

    stop_words = {
        "מה", "איך", "האם", "של", "על", "עם",
        "את", "או", "גם", "יש", "זה", "זו",
        "בין", "אילו", "כיצד", "למה", "מתי",
        "הפניקס"
    }

    return {
        word for word in words
        if len(word) >= 2 and word not in stop_words
    }


def calculate_keyword_score(question: str, chunk: dict) -> float:
    """
    Calculate how well the chunk matches the question's words.
    """
    question_words = tokenize_hebrew(question)

    if not question_words:
        return 0.0

    text_words = tokenize_hebrew(chunk.get("text", ""))
    title_words = tokenize_hebrew(chunk.get("page_title", ""))
    section_words = tokenize_hebrew(chunk.get("section_title", ""))

    text_matches = len(question_words & text_words)
    title_matches = len(question_words & title_words)
    section_matches = len(question_words & section_words)

    max_possible = len(question_words) * 2.0

    score = (
        text_matches
        + title_matches * 0.6
        + section_matches * 0.4
    ) / max_possible

    return min(score, 1.0)


def rerank_chunks(
    question: str,
    chunks: list[dict],
    limit: int = 5
) -> list[dict]:
    """
    Combine semantic similarity with keyword relevance.
    """
    for chunk in chunks:
        semantic_score = float(chunk.get("score") or 0.0)
        keyword_score = calculate_keyword_score(question, chunk)

        chunk["semantic_score"] = semantic_score
        chunk["keyword_score"] = keyword_score

        chunk["combined_score"] = (
            semantic_score * 0.75
            + keyword_score * 0.25
        )

    chunks.sort(
        key=lambda chunk: chunk["combined_score"],
        reverse=True
    )

    return chunks[:limit]


def search_chunks(question: str, limit: int = 5) -> list[dict]:
    """
    Search Qdrant for Phoenix website excerpts
    relevant to the user's question.

    Measure each retrieval stage separately.
    """

    total_start = time.perf_counter()

    # Step 1: Gemini query embedding
    embedding_start = time.perf_counter()

    response = gemini_client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=question,
        config=types.EmbedContentConfig(
            task_type="RETRIEVAL_QUERY",
            output_dimensionality=VECTOR_SIZE,
        ),
    )

    embedding_time = time.perf_counter() - embedding_start

    if not response.embeddings:
        raise RuntimeError("Gemini returned no query embedding")

    query_vector = response.embeddings[0].values

    if query_vector is None or len(query_vector) != VECTOR_SIZE:
        raise RuntimeError("Invalid query embedding dimensions")

    # Step 2: Qdrant vector search
    qdrant_start = time.perf_counter()

    results = qdrant_client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=max(limit * 4, 20),
        with_payload=True,
    )

    qdrant_time = time.perf_counter() - qdrant_start

    # Step 3: Convert Qdrant results into chunks
    processing_start = time.perf_counter()

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

    processing_time = time.perf_counter() - processing_start

    # Step 4: Reranking
    reranking_start = time.perf_counter()

    ranked_chunks = rerank_chunks(
        question,
        chunks,
        limit=limit,
    )

    reranking_time = time.perf_counter() - reranking_start

    total_time = time.perf_counter() - total_start

    # Performance report
    print("\n" + "=" * 45, flush=True)
    print("PHOENIXRAG RETRIEVAL BREAKDOWN", flush=True)
    print("=" * 45, flush=True)
    print(f"Embedding:       {embedding_time:.2f}s", flush=True)
    print(f"Qdrant Search:   {qdrant_time:.2f}s", flush=True)
    print(f"Processing:      {processing_time:.4f}s", flush=True)
    print(f"Reranking:       {reranking_time:.4f}s", flush=True)
    print(f"Total Retrieval: {total_time:.2f}s", flush=True)
    print(f"Candidates:      {len(chunks)}", flush=True)
    print(f"Selected Chunks: {len(ranked_chunks)}", flush=True)
    print("=" * 45 + "\n", flush=True)

    return ranked_chunks


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
