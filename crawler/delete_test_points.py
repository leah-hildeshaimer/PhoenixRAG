
import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient, models

load_dotenv()

client = QdrantClient(
    url=os.getenv("QDRANT_URL"),
    api_key=os.getenv("QDRANT_API_KEY"),
    timeout=30,
)

COLLECTION_NAME = "phoenix_chunks"

# These are the IDs used by upload_test_chunks.py.
TEST_POINT_IDS = [1, 2, 3, 4, 5]

print("Checking test points...")

existing_points = client.retrieve(
    collection_name=COLLECTION_NAME,
    ids=TEST_POINT_IDS,
    with_payload=False,
    with_vectors=False,
)

found_ids = [point.id for point in existing_points]

print("Found test point IDs:", found_ids)

if found_ids:
    client.delete(
        collection_name=COLLECTION_NAME,
        points_selector=models.PointIdsList(
            points=found_ids
        ),
        wait=True,
    )

    print("Test points deleted successfully!")
else:
    print("No test points found.")

collection_info = client.get_collection(COLLECTION_NAME)

print("Remaining points:", collection_info.points_count)
