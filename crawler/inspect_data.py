
import json
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent
INPUT_FILE = BASE_DIR / "results_full.jsonl"


def main():
    pages_by_url = {}

    with INPUT_FILE.open("r", encoding="utf-8") as file:
        for line in file:
            if not line.strip():
                continue

            page = json.loads(line)
            url = page.get("url", "")

            if url:
                pages_by_url[url] = page

    pages = list(pages_by_url.values())

    empty_pages = []
    short_pages = []
    element_types = Counter()

    for page in pages:
        content = page.get("content", [])

        text = " ".join(
            element.get("text", "")
            for element in content
        )

        for element in content:
            element_types[element.get("type", "unknown")] += 1

        if not text.strip():
            empty_pages.append(page["url"])

        elif len(text.strip()) < 100:
            short_pages.append(page["url"])

    print("=== DATA QUALITY REPORT ===")
    print(f"Unique pages: {len(pages)}")
    print(f"Empty pages: {len(empty_pages)}")
    print(f"Short pages (<100 chars): {len(short_pages)}")

    print("\nElement types:")
    for element_type, count in element_types.most_common():
        print(f"  {element_type}: {count}")

    print("\nEmpty pages (first 15):")
    for url in empty_pages[:15]:
        print(f"  {url}")

    print("\nShort pages (first 15):")
    for url in short_pages[:15]:
        print(f"  {url}")


if __name__ == "__main__":
    main()
