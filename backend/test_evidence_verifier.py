
import json
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from services.evidence_verifier import verify_answer


# --------------------------------------------------
# Configuration
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
RESULTS_FILE = BASE_DIR / "evidence_verification_results.json"


# --------------------------------------------------
# Test case model
# --------------------------------------------------

@dataclass
class TestCase:
    name: str
    question: str
    answer: str
    context: str
    expected_verified: bool


# --------------------------------------------------
# Shared source context
# --------------------------------------------------

BASIC_CONTEXT = """
[SOURCE 1]
Title: ביטוח דירה - מדריך כיסויים והרחבות
URL: https://www.fnx.co.il/apartment-insurance/apartment-information/guide-covers-and-extensions/
Content:
בפוליסת ביטוח הדירה של הפניקס קיים כיסוי
לאובדן שכר דירה לתקופה של עד 12 חודשים
ממועד האירוע, אם שמאי מטעם החברה קובע
שהדירה אינה ראויה למגורים בעקבות אירוע מכוסה.
[/SOURCE 1]
"""

CALCULATION_CONTEXT = """
[SOURCE 1]
Title: ביטוח דירה - מדריך כיסויים והרחבות
Content:
הפיצוי לאובדן שכר דירה ניתן לתקופה של עד
12 חודשים ממועד האירוע, לפי שכר דירה מקובל
לדירה דומה, ובסכום שלא יעלה על 15% מסכום
ביטוח הדירה, לפי הנמוך מבין שני הסכומים.
[/SOURCE 1]
"""


# --------------------------------------------------
# Test definitions
# --------------------------------------------------

TEST_CASES = [
    TestCase(
        name="Correct answer",
        question="לכמה זמן ניתן כיסוי לאובדן שכר דירה?",
        answer=(
            "הכיסוי לאובדן שכר דירה ניתן לתקופה "
            "של עד 12 חודשים ממועד האירוע, "
            "בכפוף לקביעת שמאי שהדירה אינה "
            "ראויה למגורים בעקבות אירוע מכוסה."
        ),
        context=BASIC_CONTEXT,
        expected_verified=True,
    ),

    TestCase(
        name="Incorrect duration",
        question="לכמה זמן ניתן כיסוי לאובדן שכר דירה?",
        answer="הכיסוי לאובדן שכר דירה ניתן לתקופה של עד 24 חודשים.",
        context=BASIC_CONTEXT,
        expected_verified=False,
    ),

    TestCase(
        name="Incorrect eligibility condition",
        question="מתי ניתן כיסוי לאובדן שכר דירה?",
        answer=(
            "הכיסוי ניתן לכל מבוטח לתקופה של עד "
            "12 חודשים, גם אם הדירה עדיין ראויה למגורים."
        ),
        context=BASIC_CONTEXT,
        expected_verified=False,
    ),

    TestCase(
        name="Unsupported monetary claim",
        question="מה כולל הכיסוי לאובדן שכר דירה?",
        answer=(
            "הכיסוי ניתן לתקופה של עד 12 חודשים, "
            "בכפוף לקביעת שמאי שהדירה אינה ראויה "
            "למגורים בעקבות אירוע מכוסה. "
            "בנוסף, הפניקס משלמת פיצוי קבוע "
            "של 5,000 ש״ח לכל מבוטח."
        ),
        context=BASIC_CONTEXT,
        expected_verified=False,
    ),

    TestCase(
        name="Incorrect comparison of units",
        question="מהי מגבלת הפיצוי לאובדן שכר דירה?",
        answer=(
            "גובה הפיצוי נקבע לפי הנמוך מבין "
            "12 חודשים לבין 15% מסכום ביטוח הדירה."
        ),
        context=CALCULATION_CONTEXT,
        expected_verified=False,
    ),

    TestCase(
        name="Correct compensation explanation",
        question="מהי מגבלת הפיצוי לאובדן שכר דירה?",
        answer=(
            "הכיסוי ניתן לתקופה של עד 12 חודשים. "
            "סכום הפיצוי מוגבל לשכר הדירה המקובל "
            "לדירה דומה או ל-15% מסכום ביטוח הדירה, "
            "לפי הנמוך מבין שני הסכומים."
        ),
        context=CALCULATION_CONTEXT,
        expected_verified=True,
    ),

    TestCase(
        name="Correct concise answer",
        question="לכמה זמן ניתן כיסוי לאובדן שכר דירה?",
        answer="עד 12 חודשים ממועד האירוע.",
        context=BASIC_CONTEXT,
        expected_verified=True,
    ),
]


# --------------------------------------------------
# Test execution
# --------------------------------------------------

def run_test(test: TestCase, index: int, total: int) -> dict:
    print("\n" + "=" * 60)
    print(f"TEST {index}/{total}: {test.name}")
    print("=" * 60)

    print(f"Question: {test.question}")
    print(f"Answer being verified: {test.answer}")
    print(f"Expected verified: {test.expected_verified}")

    start = time.perf_counter()

    try:
        result = verify_answer(
            question=test.question,
            answer=test.answer,
            context=test.context,
        )

        duration = time.perf_counter() - start

        passed = result.verified == test.expected_verified

        print(f"\nActual verified: {result.verified}")
        print(f"Issues: {result.issues}")
        print(f"Supporting sources: {result.supported_source_ids}")
        print(f"Duration: {duration:.2f}s")
        print(f"RESULT: {'PASS' if passed else 'FAIL'}")

        return {
            "name": test.name,
            "question": test.question,
            "answer": test.answer,
            "expected_verified": test.expected_verified,
            "actual_verified": result.verified,
            "issues": result.issues,
            "supported_source_ids": result.supported_source_ids,
            "duration_seconds": round(duration, 3),
            "passed": passed,
            "error": None,
        }

    except Exception as error:
        duration = time.perf_counter() - start

        print(f"\nERROR: {type(error).__name__}: {error}")
        print(f"Duration: {duration:.2f}s")
        print("RESULT: ERROR")

        return {
            "name": test.name,
            "question": test.question,
            "answer": test.answer,
            "expected_verified": test.expected_verified,
            "actual_verified": None,
            "issues": [],
            "supported_source_ids": [],
            "duration_seconds": round(duration, 3),
            "passed": False,
            "error": f"{type(error).__name__}: {error}",
        }


# --------------------------------------------------
# Main
# --------------------------------------------------

def main():
    results = []

    total_start = time.perf_counter()

    for index, test in enumerate(TEST_CASES, start=1):
        result = run_test(
            test=test,
            index=index,
            total=len(TEST_CASES),
        )
        results.append(result)

    total_duration = time.perf_counter() - total_start

    passed = sum(1 for item in results if item["passed"])
    failed = sum(
        1 for item in results
        if not item["passed"] and item["error"] is None
    )
    errors = sum(1 for item in results if item["error"] is not None)

    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "total_tests": len(results),
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "pass_rate": round(100 * passed / len(results), 2),
        "total_duration_seconds": round(total_duration, 3),
        "results": results,
    }

    RESULTS_FILE.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print("\n" + "=" * 60)
    print("PHOENIXRAG EVIDENCE VERIFICATION REPORT")
    print("=" * 60)

    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Errors: {errors}")
    print(f"Pass rate: {report['pass_rate']}%")
    print(f"Total duration: {total_duration:.2f}s")
    print(f"Report saved to: {RESULTS_FILE}")

    print("=" * 60)

    if failed or errors:
        print("\nTests requiring attention:")
        for item in results:
            if not item["passed"]:
                print(f"- {item['name']}")


if __name__ == "__main__":
    main()
