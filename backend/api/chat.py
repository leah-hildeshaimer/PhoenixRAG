
import os
import time

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, BackgroundTasks

from schemas.chat import ChatRequest, ChatResponse, Source
from services.evidence_verifier import verify_answer
from services.generation import generate_answer
from services.retrieval import search_chunks, build_context
from services.scope_guard import check_scope


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

ENABLE_EVIDENCE_VERIFICATION = (
    os.getenv("ENABLE_EVIDENCE_VERIFICATION", "false")
    .strip()
    .lower()
    == "true"
)

router = APIRouter(prefix="/api", tags=["Chat"])

OUT_OF_SCOPE_ANSWER = (
    "אני העוזר הדיגיטלי של הפניקס, "
    "ואוכל לסייע בשאלות על מוצרי הביטוח, "
    "הפנסיה, התביעות והשירותים של החברה."
)


def verify_answer_in_background(
    question: str,
    answer: str,
    context: str,
):
    start = time.perf_counter()

    try:
        result = verify_answer(
            question=question,
            answer=answer,
            context=context,
        )

        status = "VERIFIED" if result.verified else "FLAGGED"

        print("\n" + "=" * 45, flush=True)
        print("PHOENIXRAG BACKGROUND VERIFICATION", flush=True)
        print("=" * 45, flush=True)
        print(f"Status: {status}", flush=True)
        print(f"Issues: {result.issues}", flush=True)
        print(
            f"Supported source IDs: {result.supported_source_ids}",
            flush=True,
        )

    except Exception as error:
        print(
            f"Background verification error: {error}",
            flush=True,
        )

    finally:
        duration = time.perf_counter() - start

        print(
            f"Background verification duration: {duration:.2f}s",
            flush=True,
        )
        print("=" * 45 + "\n", flush=True)


def timed_scope_check(question: str):
    start = time.perf_counter()

    try:
        result = check_scope(question)
        return result, time.perf_counter() - start
    except Exception:
        print(
            f"Scope Guard failed after "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )
        raise


def timed_retrieval(question: str):
    start = time.perf_counter()

    try:
        chunks = search_chunks(
            question=question,
            limit=5,
        )
        return chunks, time.perf_counter() - start
    except Exception:
        print(
            f"Retrieval failed after "
            f"{time.perf_counter() - start:.2f}s",
            flush=True,
        )
        raise


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, background_tasks: BackgroundTasks):
    total_start = time.perf_counter()

    scope_time = 0.0
    retrieval_time = 0.0
    context_time = 0.0
    generation_time = 0.0

    # --------------------------------------------------
    # Step 1: Run Scope Guard and Retrieval in parallel
    # --------------------------------------------------

    parallel_start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=2) as executor:

        scope_future = executor.submit(
            timed_scope_check,
            request.question,
        )

        retrieval_future = executor.submit(
            timed_retrieval,
            request.question,
        )

        try:
            scope_result, scope_time = scope_future.result()
        except Exception as error:
            print(f"Scope Guard error: {error}", flush=True)

            raise HTTPException(
                status_code=503,
                detail=(
                    "שירות סיווג השאלות אינו זמין כרגע. "
                    "נסו שוב מאוחר יותר."
                ),
            )

        print(
            f"Scope Guard: {scope_result.classification} "
            f"({scope_time:.2f}s)",
            flush=True,
        )

        # Out-of-scope requests do not need a generated answer.
        if scope_result.classification == "out_of_scope":
            print(
                "Request rejected by Scope Guard.",
                flush=True,
            )

            return ChatResponse(
                answer=OUT_OF_SCOPE_ANSWER,
                sources=[],
            )

        try:
            chunks, retrieval_time = retrieval_future.result()
        except Exception as error:
            print(f"Retrieval error: {error}", flush=True)

            raise HTTPException(
                status_code=503,
                detail=(
                    "שירות החיפוש אינו זמין כרגע. "
                    "נסו שוב מאוחר יותר."
                ),
            )

    parallel_time = time.perf_counter() - parallel_start

    # --------------------------------------------------
    # Step 2: Build context
    # --------------------------------------------------

    context_start = time.perf_counter()
    context = build_context(chunks)
    context_time = time.perf_counter() - context_start

    # --------------------------------------------------
    # Step 3: Generate answer
    # --------------------------------------------------

    generation_start = time.perf_counter()

    try:
        result = generate_answer(
            question=request.question,
            context=context,
        )
    except Exception as error:
        print(f"Generation error: {error}", flush=True)

        raise HTTPException(
            status_code=503,
            detail=(
                "שירות יצירת התשובות אינו זמין כרגע. "
                "נסו שוב מאוחר יותר."
            ),
        )

    generation_time = time.perf_counter() - generation_start

    # --------------------------------------------------
    # Step 4: Build response and select sources
    # --------------------------------------------------

    if not result.answerable:

        response = ChatResponse(
            answer=result.answer,
            sources=[],
        )

    else:

        sources = []
        seen_urls = set()

        for source_id in result.source_ids:

            index = source_id - 1

            if index < 0 or index >= len(chunks):
                continue

            chunk = chunks[index]

            url = chunk.get("url", "")
            title = chunk.get("page_title", "")

            if not url or url in seen_urls:
                continue

            sources.append(
                Source(
                    title=title,
                    url=url,
                )
            )

            seen_urls.add(url)

        if not sources:

            response = ChatResponse(
                answer=(
                    "לא נמצאו מקורות מספקים באתר הפניקס "
                    "למענה על שאלה זו."
                ),
                sources=[],
            )

        else:

            response = ChatResponse(
                answer=result.answer,
                sources=sources,
            )

    # --------------------------------------------------
    # Step 5: Background evidence verification
    # --------------------------------------------------

    verification_status = "DISABLED"

    if ENABLE_EVIDENCE_VERIFICATION:

        if result.answerable and response.sources:

            background_tasks.add_task(
                verify_answer_in_background,
                question=request.question,
                answer=response.answer,
                context=context,
            )

            verification_status = "SCHEDULED"

        else:
            verification_status = "SKIPPED"

    # --------------------------------------------------
    # Step 6: Performance report
    # --------------------------------------------------

    total_time = time.perf_counter() - total_start

    print("\n" + "=" * 45, flush=True)
    print("PHOENIXRAG PERFORMANCE", flush=True)
    print("=" * 45, flush=True)

    print(f"Scope Guard:     {scope_time:.2f}s", flush=True)
    print(f"Retrieval:       {retrieval_time:.2f}s", flush=True)
    print(f"Parallel stage:  {parallel_time:.2f}s", flush=True)
    print(f"Context:         {context_time:.4f}s", flush=True)
    print(f"Generation:      {generation_time:.2f}s", flush=True)
    print(f"Total:           {total_time:.2f}s", flush=True)

    print(f"Chunks:          {len(chunks)}", flush=True)
    print(f"Sources:         {len(response.sources)}", flush=True)
    print(
        f"Verification:    {verification_status}",
        flush=True,
    )

    print("=" * 45 + "\n", flush=True)

    return response
