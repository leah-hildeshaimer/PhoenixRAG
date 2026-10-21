
from services.retrieval import qdrant_client, COLLECTION_NAME

info = qdrant_client.get_collection(COLLECTION_NAME)

print("Connected to Qdrant!")
print("Collection:", COLLECTION_NAME)
print("Stored points:", info.points_count)
