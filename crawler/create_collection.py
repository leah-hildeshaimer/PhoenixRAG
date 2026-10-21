
import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "phoenix_chunks"
VECTOR_SIZE = 768

if not QDRANT_URL or not QDRANT_API_KEY:
    raise ValueError("Qdrant configuration is missing from .env")

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=30,
)

if client.collection_exists(COLLECTION_NAME):
    print(f"Collection '{COLLECTION_NAME}' already exists.")
else:
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )

    print(f"Collection '{COLLECTION_NAME}' created successfully!")

collection_info = client.get_collection(COLLECTION_NAME)

print("Collection status:", collection_info.status)
print("Stored points:", collection_info.points_count)
