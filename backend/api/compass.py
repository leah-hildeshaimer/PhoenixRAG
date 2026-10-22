"""Phoenix Compass: a separate, fail-closed conversation endpoint.

This module DOES NOT modify /api/chat, its prompts or its verification flow.
"""

from fastapi import APIRouter, HTTPException

from api.chat import ENABLE_EVIDENCE_VERIFICATION, chat
from schemas.chat import ChatRequest
from schemas.compass import CompassTurnRequest, CompassTurnResponse
from services.compass_engine import decide_next_turn

router = APIRouter(prefix="/api/compass", tags=["Compass"])


@router.post("/turn", response_model=CompassTurnResponse)
def compass_turn(request: CompassTurnRequest) -> CompassTurnResponse:
    if not request.message.strip():
        raise HTTPException(status_code=422, detail="יש להזין הודעה.")

    # Existing chat can run with verification disabled for development; Compass
    # must never present such a response as source-verified.
    if not ENABLE_EVIDENCE_VERIFICATION:
        raise HTTPException(
            status_code=503,
            detail="ליווי חכם זמין רק כאשר אימות המקורות מופעל.",
        )

    try:
        decision, state = decide_next_turn(request)
    except Exception as exc:
        print(f"Compass navigation error: {type(exc).__name__}", flush=True)
        raise HTTPException(
            status_code=503,
            detail="מנגנון הליווי החכם אינו זמין כרגע. אפשר לנסות שוב.",
        ) from exc

    if decision.next_step == "ask":
        return CompassTurnResponse(
            kind="question",
            message=decision.question,
            choices=decision.choices,
            state=state,
        )

    # The ONLY path that may produce insurance facts reuses the existing
    # /api/chat implementation including scope, retrieval, generation,
    # claim-level evidence verification and repair.
    verified_response = chat(ChatRequest(question=decision.retrieval_query))

    # Count clarification turns per completed answer, not for the entire session.
    state.clarification_count = 0

    if not verified_response.sources:
        return CompassTurnResponse(
            kind="insufficient_evidence",
            message=(
                "לא הצלחתי לבסס תשובה מדויקת מתוך המקורות שנשלפו מאתר הפניקס. "
                "אפשר לנסות שאלה ממוקדת יותר."
            ),
            state=state,
        )

    return CompassTurnResponse(
        kind="answer",
        message=verified_response.answer,
        sources=verified_response.sources,
        state=state,
    )
