
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

with (BASE_DIR / "chunks.json").open(
    "r", encoding="utf-8"
) as file:
    chunks = json.load(file)

short_chunks = []
disclaimer_chunks = []

for chunk in chunks:
    text = chunk.get("text", "").strip()

    if len(text) < 100:
        short_chunks.append(chunk)

    if "החברה עושה מאמצים בכדי לוודא" in text:
        disclaimer_chunks.append(chunk)

print("=== CHUNK QUALITY REPORT ===")
print("Total chunks:", len(chunks))
print("Chunks under 100 chars:", len(short_chunks))
print("Chunks containing disclaimer:", len(disclaimer_chunks))

print("\n=== SHORT CHUNK EXAMPLES ===")

for chunk in short_chunks[:10]:
    print("---")
    print("URL:", chunk["url"])
    print("TEXT:", chunk["text"])
