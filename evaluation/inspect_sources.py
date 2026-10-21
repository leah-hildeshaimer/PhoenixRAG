
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

QUESTIONS_PATH = BASE_DIR / "evaluation" / "questions.json"
CHUNKS_PATH = BASE_DIR / "crawler" / "chunks.json"


def load_json(path):
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def search_chunks(chunks, keywords, limit=5):
    results = []

    for chunk in chunks:
        text = chunk.get("text", "")
        title = chunk.get("page_title", "")
        section = chunk.get("section_title", "")

        searchable = f"{title} {section} {text}".lower()

        score = sum(
            1 for keyword in keywords
            if keyword.lower() in searchable
        )

        if score > 0:
            results.append((score, chunk))

    results.sort(key=lambda item: item[0], reverse=True)

    return results[:limit]


def main():
    questions_data = load_json(QUESTIONS_PATH)
    chunks = load_json(CHUNKS_PATH)

    print(f"Loaded {len(chunks)} chunks")

    keywords_by_question = {
        1: ["ביטוח מקיף", "רכב"],
        2: ["ביטוח חובה", "ביטוח מקיף"],
        3: ["ביטוח דירה", "כיסויים"],
        4: ["תביעה", "רכב"],
        5: ["קרן פנסיה", "פנסיה"],
    }

    for question in questions_data["questions"]:
        question_id = question["id"]

        if not question["expected_to_be_answerable"]:
            continue

        keywords = keywords_by_question.get(question_id, [])

        if not keywords:
            continue

        print("\n" + "=" * 70)
        print(f"QUESTION {question_id}: {question['question']}")
        print("=" * 70)

        results = search_chunks(chunks, keywords)

        if not results:
            print("No matching chunks found.")
            continue

        for score, chunk in results:
            print(f"\nScore: {score}")
            print(f"Title: {chunk.get('page_title')}")
            print(f"Section: {chunk.get('section_title')}")
            print(f"URL: {chunk.get('url')}")
            print(f"Text: {chunk.get('text', '')[:600]}")
            print("-" * 50)


if __name__ == "__main__":
    main()
