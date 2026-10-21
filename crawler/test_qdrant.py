import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# טעינת משתני הסביבה
load_dotenv()

# קריאת פרטי החיבור
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

# בדיקה שכל הפרטים קיימים
if not qdrant_url or not qdrant_api_key:
    raise ValueError("Missing Qdrant credentials in .env")

# יצירת לקוח שמתחבר ל-Qdrant Cloud
client = QdrantClient(
    url=qdrant_url,
    api_key=qdrant_api_key,
    timeout=15
)

# ניסיון לקרוא את רשימת ה-Collections
collections = client.get_collections()

print("Connected to Qdrant successfully!")
print("Collections:", [c.name for c in collections.collections])