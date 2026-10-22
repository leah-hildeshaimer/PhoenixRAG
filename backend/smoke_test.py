# -*- coding: utf-8 -*-
r"""One-command PhoenixRAG API smoke test with persistent JSON results.

From backend, while the local server runs:
    .\.venv\Scripts\python.exe smoke_test.py

This test CALLS live Gemini and Qdrant through the local API.
The checks are structural; manual review is still needed for policy accuracy.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_URL = "http://127.0.0.1:8000/api/chat"
OUT = Path(__file__).with_name("smoke_results.json")

CASES = [
    (
        "COMPARISON",
        "מה ההבדל בין כיסוי נזקי הצפה לרכב לבין כיסוי נזקי הצפה בדירה?",
    ),
    (
        "GENERAL_CAR",
        "מה מכסה ביטוח מקיף רגיל לרכב של הפניקס?",
    ),
    (
        "CAR_EARTHQUAKE",
        "האם ביטוח מקיף לרכב כולל כיסוי לנזקי רעידת אדמה בכל המסלולים ללא תוספת?",
    ),
    (
        "PRIVATE_CLAIM",
        "מה מספר התביעה האישית שלי בהפניקס?",
    ),
    (
        "NONEXISTENT_PRODUCT",
        "מה הכיסויים והמחיר של פוליסת Phoenix Ultra 9000?",
    ),
]


def request_answer(question: str) -> dict:
    data = json.dumps({"question": question}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        API_URL,
        data=data,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=100) as response:
        result = json.loads(response.read().decode("utf-8"))
    if not isinstance(result, dict):
        raise ValueError("Response is not a JSON object")
    return result


def structural_issues(case_id: str, result: dict) -> list[str]:
    issues = []
    answer = result.get("answer", "")
    sources = result.get("sources", [])
    if not isinstance(answer, str) or not isinstance(sources, list):
        return ["Unexpected API response shape"]
    urls = [s.get("url", "") for s in sources if isinstance(s, dict)]
    if "[SOURCE" in answer:
        issues.append("Citation marker leaked to answer")
    if any(not url.startswith("https://www.fnx.co.il/") for url in urls):
        issues.append("Non-Phoenix source returned")
    if case_id == "COMPARISON":
        if not any("/car-insurance/" in url for url in urls):
            issues.append("Missing car source")
        if not any("/apartment-insurance/" in url for url in urls):
            issues.append("Missing apartment source")
    if case_id == "GENERAL_CAR":
        if not any("/car-insurance/" in url for url in urls):
            issues.append("Missing general car insurance source")
        if "טסלה" in answer or "סוללה" in answer:
            issues.append("Unrequested specialized vehicle detail")
    if case_id == "CAR_EARTHQUAKE":
        if sources and not any("/car-insurance/" in url for url in urls):
            issues.append("Earthquake answer cited wrong insurance family")
        if not sources:
            issues.append("No grounded answer for explicit car coverage question")
    if case_id in ("PRIVATE_CLAIM", "NONEXISTENT_PRODUCT") and sources:
        issues.append("Sources unexpectedly returned for unknown/personal request")
    return issues


def main() -> int:
    report = {"checked_at_utc": datetime.now(timezone.utc).isoformat(),
              "api_url": API_URL, "cases": []}
    for case_id, question in CASES:
        start = time.perf_counter()
        record = {"id": case_id, "question": question}
        try:
            response = request_answer(question)
            record["response"] = response
            record["issues"] = structural_issues(case_id, response)
            record["status"] = "PASS" if not record["issues"] else "REVIEW"
        except Exception as exc:
            record["status"] = "ERROR"
            record["error"] = f"{type(exc).__name__}: {exc}"
            record["issues"] = [record["error"]]
        record["seconds"] = round(time.perf_counter() - start, 2)
        report["cases"].append(record)
        print(f'{case_id}: {record["status"]} ({record["seconds"]}s)')
        for issue in record["issues"]:
            print(f"    {issue}")
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nReport saved: {OUT.name}")
    return 1 if any(item["status"] != "PASS" for item in report["cases"]) else 0


if __name__ == "__main__":
    sys.exit(main())