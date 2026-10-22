"""PhoenixRAG chat endpoint. Verifies supported answers before returning them.

Keeps the existing public /api/chat request and response schema unchanged.
"""
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse, Source
from services.evidence_verifier import verify_answer
from services.generation import generate_answer, repair_answer
from services.retrieval import build_context, search_chunks
from services.scope_guard import check_scope

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

ENABLE_EVIDENCE_VERIFICATION = (
    os.getenv("ENABLE_EVIDENCE_VERIFICATION", "true").strip().lower() == "true"
)
DEBUG_RAG = os.getenv("RAG_DEBUG", "false").strip().lower() == "true"

router = APIRouter(prefix="/api", tags=["Chat"])

OUT_OF_SCOPE_ANSWER = (
    "אני העוזר הדיגיטלי של הפניקס, ואוכל לסייע בשאלות על "
    "מוצרי הביטוח, הפנסיה, התביעות והשירותים של החברה."
)
UNVERIFIED_ANSWER = (
    "לא הצלחתי לאמת תשובה מדויקת לשאלה הזאת מתוך המקורות "
    "שנשלפו מאתר הפניקס. אפשר לנסות שאלה ממוקדת יותר."
)


def _timed(action, *args, **kwargs):
    started = time.perf_counter()
    result = action(*args, **kwargs)
    return result, time.perf_counter() - started


def _sources_for_ids(chunks: list[dict], ids: list[int]) -> list[Source]:
    sources: list[Source] = []
    seen: set[str] = set()
    for source_id in ids:
        if not isinstance(source_id, int) or source_id < 1 or source_id > len(chunks):
            continue
        chunk = chunks[source_id - 1]
        url = chunk.get("url") or ""
        if not url or url in seen or not url.startswith("https://www.fnx.co.il/"):
            continue
        seen.add(url)
        sources.append(Source(title=chunk.get("page_title") or "מקור מאתר הפניקס", url=url))
    return sources


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    started = time.perf_counter()
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="יש להזין שאלה.")

    # Keep the existing concurrency of scope validation and retrieval.
    with ThreadPoolExecutor(max_workers=2) as executor:
        scope_future = executor.submit(_timed, check_scope, question)
        retrieval_future = executor.submit(_timed, search_chunks, question, 5)

        try:
            scope, scope_seconds = scope_future.result()
        except Exception as exc:
            print(f"Scope error: {type(exc).__name__}", flush=True)
            raise HTTPException(status_code=503, detail="שירות סיווג השאלות אינו זמין כרגע.") from exc

        print(f"Scope Guard: {scope.classification} ({scope_seconds:.2f}s)", flush=True)
        if scope.classification == "out_of_scope":
            return ChatResponse(answer=OUT_OF_SCOPE_ANSWER, sources=[])

        try:
            chunks, retrieval_seconds = retrieval_future.result()
        except Exception as exc:
            print(f"Retrieval error: {type(exc).__name__}", flush=True)
            raise HTTPException(status_code=503, detail="שירות החיפוש אינו זמין כרגע.") from exc

    if not chunks:
        return ChatResponse(
            answer="לא מצאתי מידע מספיק באתר הפניקס לשאלה הזאת.", sources=[]
        )

    context = build_context(chunks)
    if DEBUG_RAG:
        print("\nCHUNKS PROVIDED TO GENERATION", flush=True)
        for i, chunk in enumerate(chunks, 1):
            print(f"[{i}] {chunk.get('page_title')} | {chunk.get('url')}", flush=True)

    try:
        generated, generation_seconds = _timed(generate_answer, question, context)
    except Exception as exc:
        print(f"Generation error: {type(exc).__name__}", flush=True)
        raise HTTPException(status_code=503, detail="שירות יצירת התשובות אינו זמין כרגע.") from exc

    # One verification pass and at most ONE repair + re-verification.
    # A rejected answer never reaches the client, including on repair errors.
    verification_seconds = 0.0
    generation_total_seconds = generation_seconds
    verification_status = "DISABLED"
    approved_ids: list[int] = []
    sources: list[Source] = []

    for attempt in range(2):
        valid_generated_ids = [
            i for i in generated.source_ids
            if type(i) is int and 1 <= i <= len(chunks)
        ]
        if not generated.answerable or not valid_generated_ids:
            print(f"Answer not established by generation (attempt={attempt+1})", flush=True)
            if attempt == 0:
                return ChatResponse(answer=generated.answer, sources=[])
            return ChatResponse(answer=UNVERIFIED_ANSWER, sources=[])

        if not ENABLE_EVIDENCE_VERIFICATION:
            approved_ids = valid_generated_ids
            sources = _sources_for_ids(chunks, approved_ids)
            break

        try:
            verified, seconds = _timed(
                verify_answer, question, generated.answer, context
            )
            verification_seconds += seconds
        except Exception as exc:
            print(f"Evidence verification failed: {type(exc).__name__}", flush=True)
            raise HTTPException(
                status_code=503,
                detail="שירות אימות התשובות אינו זמין כרגע. נסו שוב מאוחר יותר.",
            ) from exc

        if verified.verified:
            # Source IDs are independently proven by the claim-level verifier.
            # Do NOT intersect with the generator's source_ids: that silently
            # erased references to other products in compound comparisons.
            approved_ids = [
                i for i in verified.supported_source_ids
                if type(i) is int and 1 <= i <= len(chunks)
            ]
            sources = _sources_for_ids(chunks, approved_ids)
            if sources:
                verification_status = "VERIFIED" if attempt == 0 else "REPAIRED+VERIFIED"
                break

        issues = list(getattr(verified, "issues", []))
        if not sources and verified.verified:
            issues.append("אין קישורים תקפים למקורות שהאימות אישר.")
        print(f"Evidence flagged (attempt={attempt+1}): {issues}", flush=True)
        if DEBUG_RAG:
            print(f"Scope issues: {getattr(verified, 'scope_issues', [])}", flush=True)
            print(f"Unaddressed parts: {getattr(verified, 'unaddressed_parts', [])}", flush=True)
        if attempt == 1:
            return ChatResponse(answer=UNVERIFIED_ANSWER, sources=[])

        # Recovery uses exactly the existing Phoenix excerpts. No web search,
        # no new policy claims, no iterative retries beyond this one attempt.
        try:
            generated, repair_seconds = _timed(
                repair_answer, question, context, generated.answer, issues
            )
            generation_total_seconds += repair_seconds
        except Exception as exc:
            print(f"Answer repair failed: {type(exc).__name__}", flush=True)
            return ChatResponse(answer=UNVERIFIED_ANSWER, sources=[])
    else:
        return ChatResponse(answer=UNVERIFIED_ANSWER, sources=[])

    if not sources:
        return ChatResponse(answer=UNVERIFIED_ANSWER, sources=[])

    print("\n" + "=" * 45, flush=True)
    print("PHOENIXRAG PERFORMANCE", flush=True)
    print("=" * 45, flush=True)
    print(f"Scope Guard:  {scope_seconds:.2f}s", flush=True)
    print(f"Retrieval:    {retrieval_seconds:.2f}s", flush=True)
    print(f"Generation:   {generation_total_seconds:.2f}s", flush=True)
    print(f"Verification: {verification_seconds:.2f}s ({verification_status})", flush=True)
    print(f"Total:        {time.perf_counter() - started:.2f}s", flush=True)
    print(f"Sources:      {len(sources)}", flush=True)
    print("=" * 45 + "\n", flush=True)
    # The frontend presents clickable sources separately; omit raw model markers.
    clean_answer = re.sub(
        r"\s*\[SOURCE\s+\d+(?:\s*,\s*(?:SOURCE\s+)?\d+)*\]",
        "", generated.answer, flags=re.IGNORECASE,
    ).strip()
    return ChatResponse(answer=clean_answer, sources=sources)