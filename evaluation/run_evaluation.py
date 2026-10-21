
"""PhoenixRAG API evaluation suite.

Checks:
- Heuristic answerability
- Response structure
- Source URL validity and uniqueness
- Basic source relevance indicators
- Response latency
- HTTP and network errors

This does NOT establish factual correctness.
"""

import json
import math
import statistics
import time
import urllib.error
import urllib.parse
import urllib.request

from datetime import datetime, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
QUESTIONS_FILE = BASE_DIR / "questions.json"
RESULTS_FILE = BASE_DIR / "results.json"

API_URL = "http://127.0.0.1:8000/api/chat"
REQUEST_TIMEOUT = 120

ALLOWED_HOSTS = {"fnx.co.il", "www.fnx.co.il"}

NO_ANSWER_PHRASES = (
    "לא נמצא",
    "לא נמצאה",
    "אינו נמצא",
    "אינה נמצאת",
    "אין מידע",
    "לא ניתן לענות",
    "אין מספיק מידע",
    "אינו מופיע",
    "לא מופיע",
    "לא קיימת תשובה",
    "לא מצאתי",
    "לא ניתן לקבוע",
)

OUT_OF_SCOPE_MESSAGE = (
    "אני העוזר הדיגיטלי של הפניקס, "
    "ואוכל לסייע בשאלות על מוצרי הביטוח, "
    "הפנסיה, התביעות והשירותים של החברה."
)


def load_questions():
    with QUESTIONS_FILE.open("r", encoding="utf-8-sig") as file:
        data = json.load(file)

    questions = (
        data.get("questions")
        if isinstance(data, dict)
        else data
    )

    if not isinstance(questions, list):
        raise ValueError(
            "questions.json must contain a list of questions"
        )

    for index, item in enumerate(questions, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Question #{index} must be an object")

        question = item.get("question")

        if not isinstance(question, str) or not question.strip():
            raise ValueError(
                f"Question #{index} must contain a nonempty question"
            )

        expected = item.get("expected_to_be_answerable")

        if expected is not None and not isinstance(expected, bool):
            raise ValueError(
                f"Question #{index} has invalid expected_to_be_answerable"
            )

    return questions


def ask_chatbot(question):
    payload = json.dumps(
        {"question": question},
        ensure_ascii=False,
    ).encode("utf-8")

    request = urllib.request.Request(
        API_URL,
        data=payload,
        headers={
            "Content-Type": "application/json; charset=utf-8",
            "Accept": "application/json",
        },
        method="POST",
    )

    with urllib.request.urlopen(
        request,
        timeout=REQUEST_TIMEOUT,
    ) as response:
        data = json.loads(response.read().decode("utf-8"))

    if not isinstance(data, dict):
        raise ValueError("API returned invalid JSON structure")

    if not isinstance(data.get("answer"), str):
        raise ValueError("API response is missing answer")

    if not isinstance(data.get("sources"), list):
        raise ValueError("API response is missing sources")

    return data


def infer_answerable(answer, sources):
    """Heuristic only, not the model's actual answerability flag."""

    if answer.strip() == OUT_OF_SCOPE_MESSAGE:
        return False

    if any(phrase in answer for phrase in NO_ANSWER_PHRASES):
        return False

    return bool(sources)


def validate_sources(sources):
    issues = []
    normalized_urls = set()

    for index, source in enumerate(sources, start=1):

        if not isinstance(source, dict):
            issues.append(f"Source #{index} is not an object")
            continue

        title = source.get("title")
        url = source.get("url")

        if not isinstance(title, str) or not title.strip():
            issues.append(f"Source #{index} has no valid title")

        if not isinstance(url, str):
            issues.append(f"Source #{index} has no valid URL")
            continue

        parsed = urllib.parse.urlparse(url)

        if (
            parsed.scheme != "https"
            or parsed.hostname not in ALLOWED_HOSTS
            or parsed.username is not None
            or parsed.password is not None
            or parsed.port not in (None, 443)
        ):
            issues.append(
                f"Source #{index} has invalid or external URL: {url}"
            )

        normalized = (
            parsed.scheme.lower(),
            (parsed.hostname or "").lower(),
            parsed.path.rstrip("/") or "/",
            parsed.query,
        )

        if normalized in normalized_urls:
            issues.append(f"Duplicate source URL: {url}")

        normalized_urls.add(normalized)

    return issues


def percentile(values, percent):
    if not values:
        return None

    ordered = sorted(values)

    rank = (len(ordered) - 1) * percent / 100
    lower = math.floor(rank)
    upper = math.ceil(rank)

    if lower == upper:
        return round(ordered[lower], 2)

    interpolated = (
        ordered[lower]
        + (ordered[upper] - ordered[lower]) * (rank - lower)
    )

    return round(interpolated, 2)


def evaluate_question(item, index, total):
    question = item["question"]
    expected = item.get("expected_to_be_answerable")

    print(f"\n[{index}/{total}] {question}", flush=True)

    result = {
        "id": item.get("id"),
        "question": question,
        "expected_to_be_answerable": expected,
        "predicted_answerable": None,
        "answerability_passed": None,
        "response_valid": False,
        "source_validation_passed": False,
        "source_issues": [],
        "response_time_seconds": None,
        "answer": None,
        "sources": [],
        "source_count": 0,
        "error": None,
    }

    started = time.perf_counter()

    try:
        response = ask_chatbot(question)

        answer = response["answer"]
        sources = response["sources"]

        predicted = infer_answerable(answer, sources)

        if isinstance(expected, bool):
            answerability_passed = predicted == expected
        else:
            answerability_passed = None

        source_issues = validate_sources(sources)

        if not answer.strip():
            source_issues.append("Empty answer")

        response_valid = bool(answer.strip())

        result.update({
            "predicted_answerable": predicted,
            "answerability_passed": answerability_passed,
            "response_valid": response_valid,
            "source_validation_passed": len(source_issues) == 0,
            "source_issues": source_issues,
            "answer": answer,
            "sources": sources,
            "source_count": len(sources),
        })

        label = (
            "PASS"
            if answerability_passed is True
            else "FAIL"
            if answerability_passed is False
            else "N/A"
        )

        print(
            f"Answerability: {label} | "
            f"Sources: {len(sources)} | "
            f"Source validation: "
            f"{'PASS' if not source_issues else 'FAIL'}",
            flush=True,
        )

        if source_issues:
            for issue in source_issues:
                print(f"  - {issue}", flush=True)

    except urllib.error.HTTPError as error:
        detail = error.read().decode(
            "utf-8", errors="replace"
        )[:500]

        result["error"] = f"HTTP {error.code}: {detail}"

    except Exception as error:
        result["error"] = (
            f"{type(error).__name__}: {error}"
        )

    finally:
        result["response_time_seconds"] = round(
            time.perf_counter() - started,
            2,
        )

        print(
            f"Time: {result['response_time_seconds']}s",
            flush=True,
        )

        if result["error"]:
            print(
                f"ERROR: {result['error']}",
                flush=True,
            )

    return result


def main():
    questions = load_questions()

    print("=" * 55)
    print("PHOENIXRAG EVALUATION SUITE")
    print("=" * 55)
    print(f"Questions: {len(questions)}")
    print(f"API: {API_URL}")

    results = []
    started = time.perf_counter()

    for index, item in enumerate(questions, start=1):
        results.append(
            evaluate_question(
                item,
                index,
                len(questions),
            )
        )

    total_duration = time.perf_counter() - started

    evaluated = [
        r for r in results
        if isinstance(r["answerability_passed"], bool)
    ]

    passed = sum(
        r["answerability_passed"] is True
        for r in evaluated
    )

    failed = sum(
        r["answerability_passed"] is False
        for r in evaluated
    )

    errors = sum(
        r["error"] is not None
        for r in results
    )

    source_failures = sum(
        r["error"] is None
        and not r["source_validation_passed"]
        for r in results
    )

    times = [
        r["response_time_seconds"]
        for r in results
        if r["error"] is None
    ]

    accuracy = (
        round(100 * passed / len(evaluated), 2)
        if evaluated
        else None
    )

    latency = {
        "mean_seconds": (
            round(statistics.mean(times), 2)
            if times else None
        ),
        "median_seconds": (
            round(statistics.median(times), 2)
            if times else None
        ),
        "p95_seconds": percentile(times, 95),
        "min_seconds": min(times) if times else None,
        "max_seconds": max(times) if times else None,
    }

    report = {
        "created_at_utc": datetime.now(
            timezone.utc
        ).isoformat(),
        "api_url": API_URL,
        "evaluation_type": "API smoke and performance",
        "factual_correctness_evaluated": False,
        "citation_support_evaluated": False,
        "total_questions": len(results),
        "evaluated_questions": len(evaluated),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "source_validation_failures": source_failures,
        "answerability_accuracy_percent": accuracy,
        "latency": latency,
        "total_duration_seconds": round(total_duration, 2),
        "results": results,
    }

    RESULTS_FILE.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n" + "=" * 55)
    print("PHOENIXRAG EVALUATION REPORT")
    print("=" * 55)

    print(f"Total questions: {len(results)}")
    print(f"Evaluated: {len(evaluated)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Source validation failures: {source_failures}")

    print(
        f"Answerability accuracy (heuristic): "
        f"{accuracy if accuracy is not None else 'N/A'}%"
    )

    print(f"Mean latency: {latency['mean_seconds']}s")
    print(f"Median latency: {latency['median_seconds']}s")
    print(f"P95 latency: {latency['p95_seconds']}s")
    print(f"Total evaluation time: {total_duration:.2f}s")

    print(f"Report saved to: {RESULTS_FILE}")
    print("=" * 55)


if __name__ == "__main__":
    main()
