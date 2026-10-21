
from services.retrieval import qdrant_client, COLLECTION_NAME


# Retrieve one existing point including its vector
points, _ = qdrant_client.scroll(
    collection_name=COLLECTION_NAME,
    limit=1,
    with_payload=True,
    with_vectors=True,
)

if not points:
    raise RuntimeError("No points found in Qdrant")

original = points[0]

print("Original chunk:")
print("Title:", original.payload.get("page_title"))
print("URL:", original.payload.get("url"))

# Search using the stored vector
results = qdrant_client.query_points(
    collection_name=COLLECTION_NAME,
    query=original.vector,
    limit=5,
    with_payload=True,
)

print("\nSearch results:")

for index, point in enumerate(results.points, start=1):
    payload = point.payload or {}

    print(f"\nResult {index}")
    print("Score:", round(point.score, 4))
    print("Title:", payload.get("page_title"))
    print("URL:", payload.get("url"))
    print("Text:", payload.get("text", "")[:200])
