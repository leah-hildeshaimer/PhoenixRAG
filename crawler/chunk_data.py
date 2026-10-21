
import json
import re
import hashlib
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

INPUT_FILE = BASE_DIR / "cleaned_data.json"
OUTPUT_FILE = BASE_DIR / "chunks.json"

MAX_CHARS = 1200
OVERLAP_CHARS = 150
MIN_CHARS = 40


def normalize_text(text):
    return re.sub(r"\s+", " ", text or "").strip()


def split_long_text(text):
    if len(text) <= MAX_CHARS:
        return [text] if text else []

    chunks = []
    remaining = text

    while len(remaining) > MAX_CHARS:
        window = remaining[:MAX_CHARS]

        # Prefer a sentence or paragraph boundary
        candidates = [
            window.rfind("\n"),
            window.rfind(". "),
            window.rfind("! "),
            window.rfind("? "),
        ]

        split_at = max(candidates)

        if split_at < MAX_CHARS // 2:
            split_at = window.rfind(" ")

        if split_at < MAX_CHARS // 2:
            split_at = MAX_CHARS
        else:
            split_at += 1

        part = remaining[:split_at].strip()

        if part:
            chunks.append(part)

        # Find an overlap starting at a word boundary
        overlap_start = max(
            0,
            split_at - OVERLAP_CHARS
        )

        if overlap_start > 0:
            space_position = remaining.find(
                " ",
                overlap_start,
                split_at
            )

            if space_position != -1:
                overlap_start = space_position + 1
            else:
                overlap_start = split_at

        remaining = remaining[overlap_start:].strip()

    if remaining:
        chunks.append(remaining)

    return chunks


def make_chunk_id(url, section, index):
    raw = f"{url}|{section}|{index}"

    return hashlib.sha256(
        raw.encode("utf-8")
    ).hexdigest()[:16]


def chunk_page(page):
    url = page.get("url", "")
    page_title = normalize_text(page.get("title"))

    chunks = []
    section_title = page_title
    section_parts = []

    def save_section():
        if not section_parts:
            return

        section_text = "\n".join(section_parts).strip()

        if len(section_text) < MIN_CHARS:
            return

        for text in split_long_text(section_text):
            if len(text) < MIN_CHARS:
                continue

            index = len(chunks)

            chunks.append({
                "id": make_chunk_id(
                    url,
                    section_title,
                    index
                ),
                "url": url,
                "page_title": page_title,
                "section_title": section_title,
                "chunk_index": index,
                "text": text
            })

    for element in page.get("content", []):
        element_type = element.get("type", "")
        text = normalize_text(element.get("text"))

        if not text:
            continue

        if element_type in {"h1", "h2", "h3"}:
            save_section()

            section_parts = []
            section_title = text

        else:
            section_parts.append(text)

    save_section()

    return chunks


def main():
    with INPUT_FILE.open(
        "r",
        encoding="utf-8"
    ) as file:
        pages = json.load(file)

    all_chunks = []
    empty_pages = []

    for page in pages:
        page_chunks = chunk_page(page)

        if not page_chunks:
            empty_pages.append(page.get("url"))

        all_chunks.extend(page_chunks)

    with OUTPUT_FILE.open(
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            all_chunks,
            file,
            ensure_ascii=False,
            indent=2
        )

    print(f"Pages processed: {len(pages)}")
    print(f"Chunks created: {len(all_chunks)}")

    if all_chunks:
        lengths = [
            len(chunk["text"])
            for chunk in all_chunks
        ]

        print(
            f"Average chunk length: "
            f"{sum(lengths) / len(lengths):.0f}"
        )

        print(f"Shortest chunk: {min(lengths)}")
        print(f"Longest chunk: {max(lengths)}")

    print(f"Pages without chunks: {len(empty_pages)}")

    for url in empty_pages:
        print(f"  - {url}")

    print(f"Saved to: {OUTPUT_FILE.name}")


if __name__ == "__main__":
    main()
