
import json
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "results_full.jsonl"
OUTPUT_FILE = BASE_DIR / "cleaned_data.json"


STOP_HEADINGS = {
    "אולי יעניין אותך גם…",
    "אולי יעניין אותך גם...",
}

UNWANTED_TEXTS = {
    "דף הבית",
    "מידע שימושי",
    "עוד בנושא",
    "למידע נוסף",
}

DISCLAIMER_START = "מידע זה הינו כללי אודות התכנית בלבד"


def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def is_reading_time(text):
    return bool(
        re.fullmatch(r"\d+(?:\.\d+)?\s*דקות?", text)
    )


def is_date(text):
    return bool(
        re.fullmatch(
            r"\d{1,2}\s+ב\S+\s+\d{4}",
            text
        )
    )


def clean_page(page):
    original_elements = page.get("content", [])

    # Keep the original heading if it exists
    h1_texts = {
        normalize_text(element.get("text"))
        for element in original_elements
        if element.get("type") == "h1"
    }

    cleaned_content = []
    seen_texts = set()
    disclaimer = None

    for element in original_elements:
        element_type = element.get("type", "")
        text = normalize_text(element.get("text"))

        if not text:
            continue

        # Related articles are not part of the article
        if (
            element_type in {"h2", "h3"}
            and text in STOP_HEADINGS
        ):
            break

        # Store legal disclaimer separately
        if text.startswith(DISCLAIMER_START):
            disclaimer = text
            continue

        if text in UNWANTED_TEXTS:
            continue

        if text.startswith("למידע נוסף על "):
            continue

        if is_reading_time(text) or is_date(text):
            continue

        # Breadcrumb title should not replace H1
        if element_type == "li" and text in h1_texts:
            continue

        # Keep H1 even if the text appeared elsewhere
        if text in seen_texts:
            continue

        seen_texts.add(text)

        cleaned_content.append({
            "type": element_type,
            "text": text
        })

    return {
        "url": page.get("url"),
        "title": page.get("title"),
        "content": cleaned_content,
        "disclaimer": disclaimer,
        "element_count": len(cleaned_content)
    }


def main():
    
    pages_by_url = {}

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue

            page = json.loads(line)
            url = page.get("url")

            if url:
                pages_by_url[url] = page

    pages = list(pages_by_url.values())


    cleaned_pages = [
        clean_page(page)
        for page in pages
    ]

    with OUTPUT_FILE.open("w", encoding="utf-8") as file:
        json.dump(
            cleaned_pages,
            file,
            ensure_ascii=False,
            indent=2
        )

    before = sum(
        len(page.get("content", []))
        for page in pages
    )

    after = sum(
        len(page["content"])
        for page in cleaned_pages
    )

    h1_count = sum(
        1
        for page in cleaned_pages
        if any(
            element["type"] == "h1"
            for element in page["content"]
        )
    )

    print(f"Pages: {len(cleaned_pages)}")
    print(f"Elements before: {before}")
    print(f"Elements after: {after}")
    print(f"Removed: {before - after}")
    print(f"Pages with H1: {h1_count}")
    print(f"Saved to: {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()
