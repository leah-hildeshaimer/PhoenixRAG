
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "results_full.jsonl"
OUTPUT_FILE = BASE_DIR / "short_pages_report.txt"

pages_by_url = {}

with INPUT_FILE.open("r", encoding="utf-8") as file:
    for line in file:
        if not line.strip():
            continue

        page = json.loads(line)
        url = page.get("url", "")

        if url:
            pages_by_url[url] = page

short_pages = []

for page in pages_by_url.values():
    content = page.get("content", [])

    text = " ".join(
        element.get("text", "")
        for element in content
    ).strip()

    if len(text) < 100:
        short_pages.append({
            "url": page.get("url", ""),
            "title": page.get("title", ""),
            "length": len(text),
            "text": text
        })

short_pages.sort(key=lambda page: page["length"])

with OUTPUT_FILE.open("w", encoding="utf-8") as file:
    for page in short_pages:
        file.write("=" * 70 + "\n")
        file.write(f"URL: {page['url']}\n")
        file.write(f"TITLE: {page['title']}\n")
        file.write(f"LENGTH: {page['length']}\n")
        file.write(f"TEXT: {page['text']}\n\n")

print(f"Short/empty pages: {len(short_pages)}")
print(f"Report saved to: {OUTPUT_FILE.name}")
