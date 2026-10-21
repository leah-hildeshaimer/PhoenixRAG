
import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from qdrant_client import QdrantClient

load_dotenv()

gemini_client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

qdrant_client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30,
)

COLLECTION_NAME = "phoenix_chunks"

question = "מה הסכנות בטעינת סוללות של קורקינטים חשמליים בבית?"

print("Question:", question)
print("Creating query embedding...")

response = gemini_client.models.embed_content(
    model="gemini-embedding-001",
    contents=question,
    config=types.EmbedContentConfig(
        task_type="RETRIEVAL_QUERY",
        output_dimensionality=768,
    ),
)

query_vector = response.embeddings[0].values

print("Searching Qdrant...")

results = qdrant_client.query_points(
    collection_name=COLLECTION_NAME,
    query=query_vector,
    limit=3,
    with_payload=True,
)

for index, point in enumerate(results.points, start=1):
    payload = point.payload or {}

    print(f"\n--- Result {index} ---")
    print("Score:", round(point.score, 4))
    print("Title:", payload.get("page_title"))
    print("URL:", payload.get("url"))
    print("Text:", payload.get("text", "")[:500])
