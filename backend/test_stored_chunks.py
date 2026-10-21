
from services.retrieval import qdrant_client, COLLECTION_NAME

points, next_offset = qdrant_client.scroll(
    collection_name=COLLECTION_NAME,
    limit=3,
    with_payload=True,
    with_vectors=False,
)

print(f"Retrieved {len(points)} stored chunks")

for index, point in enumerate(points, start=1):
    payload = point.payload or {}

    print("\n" + "=" * 60)
    print(f"CHUNK {index}")
    print("=" * 60)

    print("Title:", payload.get("page_title"))
    print("Section:", payload.get("section_title"))
    print("URL:", payload.get("url"))
    print("Text:", payload.get("text", "")[:500])
