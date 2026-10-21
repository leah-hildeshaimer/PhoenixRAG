
import os
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env")

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY in backend/.env")

client = genai.Client(api_key=API_KEY)

MODEL_NAME = "gemini-3.5-flash-lite"


class ScopeDecision(BaseModel):
    classification: Literal[
        "in_scope",
        "out_of_scope",
        "uncertain",
    ]


SYSTEM_INSTRUCTION = """
You classify user questions for PhoenixRAG,
a customer-facing assistant for Phoenix Insurance.

Classify the question into exactly one category:

in_scope:
Questions about Phoenix Insurance, its products,
insurance, pensions, savings, claims, policies,
customer service, contact details, forms,
procedures, payments, and related services.

out_of_scope:
Clearly unrelated general-knowledge questions,
trivia, entertainment, or unrelated topics.

uncertain:
Questions that might reasonably relate to
Phoenix Insurance services but lack context.

Important rules:
- Do not answer the question.
- Only classify it.
- A question does not need to mention "Phoenix"
  or "insurance" to be in scope.
- For ambiguous service-related questions,
  prefer uncertain over out_of_scope.
- Classify based on the user's actual intent.
"""


def check_scope(question: str) -> ScopeDecision:
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=question,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            temperature=0,
            response_mime_type="application/json",
            response_schema=ScopeDecision,
        ),
    )

    if not response.text:
        raise RuntimeError("Scope classifier returned empty response")

    return ScopeDecision.model_validate_json(response.text)
