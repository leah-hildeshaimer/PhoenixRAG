
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.chat import router as chat_router


app = FastAPI(
    title="PhoenixRAG API",
    description="AI chatbot based on Phoenix website content",
    version="1.0.0",
)

# Local frontend addresses
allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Production frontend address, configured in Render
frontend_url = os.getenv("FRONTEND_URL", "").strip().rstrip("/")

if frontend_url:
    allowed_origins.append(frontend_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.get("/")
def root():
    return {
        "message": "PhoenixRAG API is running!",
        "status": "success",
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


app.include_router(chat_router)
