
import json
import random
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "chunks.json"

with INPUT_FILE.open("r", encoding="utf-8") as f:
    chunks = json.load(f)

print("Total chunks:", len(chunks))

random.seed(42)
sample = random.sample(chunks, min(5, len(chunks)))

for index, chunk in enumerate(sample, start=1):
    print(f"\n{'=' * 60}")
    print(f"CHUNK {index}")
    print("URL:", chunk.get("url"))
    print("Page title:", chunk.get("page_title"))
    print("Section:", chunk.get("section_title"))
    print("Length:", len(chunk.get("text", "")))
    print("\nTEXT:")
    print(chunk.get("text", "")[:1200])
