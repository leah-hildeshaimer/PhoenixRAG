import os
from dotenv import load_dotenv
from google import genai

# קריאת משתני הסביבה מקובץ .env
load_dotenv()

# קבלת מפתח ה-API
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise ValueError("GEMINI_API_KEY is missing from .env")

# יצירת חיבור ל-Gemini
client = genai.Client(api_key=api_key)

# משפט לדוגמה מתוך עולם הביטוח
text = "ביטוח חובה לרכב מכסה נזקי גוף במקרה של תאונת דרכים"

# בקשה ליצור Embedding למשפט
response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text,
    config={
        "task_type": "RETRIEVAL_DOCUMENT",
        "output_dimensionality": 768,
    },
)

# חילוץ הווקטור מהתשובה
vector = response.embeddings[0].values

print("Original text:", text)
print("Vector dimensions:", len(vector))
print("First 10 numbers:", vector[:10])