
from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse, Source
from services.generation import generate_answer
from services.retrieval import search_chunks, build_context


router = APIRouter(prefix="/api", tags=["Chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    # 1. Retrieve relevant Phoenix website excerpts
    try:
        chunks = search_chunks(
            question=request.question,
            limit=5,
        )
    except Exception as error:
        print(f"Retrieval error: {error}")
        raise HTTPException(
            status_code=503,
            detail="שירות החיפוש אינו זמין כרגע. נסו שוב מאוחר יותר.",
        )

    # 2. Build context from retrieved excerpts
    context = build_context(chunks)

    # 3. Generate an answer based on the context
    answer = generate_answer(
        question=request.question,
        context=context,
    )

    # 4. Build source links from retrieved chunks
    sources = []
    seen_urls = set()

    for chunk in chunks:
        url = chunk.get("url", "")
        title = chunk.get("page_title", "")

        if url and url not in seen_urls:
            sources.append(
                Source(
                    title=title,
                    url=url,
                )
            )
            seen_urls.add(url)

    return ChatResponse(
        answer=answer,
        sources=sources,
    )
