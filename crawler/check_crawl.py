
import json
from pathlib import Path
from collections import Counter


BASE_DIR = Path(__file__).resolve().parent

FILE = BASE_DIR / "results_full.jsonl"


def main():

    if not FILE.exists():
        print("No crawl results found.")
        return

    pages = []

    with FILE.open(
        "r",
        encoding="utf-8"
    ) as file:

        for line in file:
            if line.strip():
                pages.append(json.loads(line))

    urls = {
        page["url"]
        for page in pages
    }

    categories = Counter()

    for url in urls:
        path = url.replace(
            "https://www.fnx.co.il/",
            ""
        )

        category = path.split("/")[0]

        categories[category] += 1

    print(f"Total saved records: {len(pages)}")
    print(f"Unique pages: {len(urls)}")

    print("\nPages by category:")

    for category, count in categories.most_common():
        print(f"  {category}: {count}")


if __name__ == "__main__":
    main()
