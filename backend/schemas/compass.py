"""Typed, size-bounded contracts for Phoenix Compass (new API only)."""

from typing import Literal

from pydantic import BaseModel, Field

from schemas.chat import Source


class CompassMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=600)


class CompassState(BaseModel):
    topic: str = Field(default="", max_length=120)
    goal: str = Field(default="", max_length=180)
    asked_questions: list[str] = Field(default_factory=list, max_length=3)
    clarification_count: int = Field(default=0, ge=0, le=3)


class CompassTurnRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    state: CompassState = Field(default_factory=CompassState)
    history: list[CompassMessage] = Field(default_factory=list, max_length=8)


class CompassTurnResponse(BaseModel):
    kind: Literal["question", "answer", "insufficient_evidence"]
    message: str
    choices: list[str] = Field(default_factory=list)
    state: CompassState
    sources: list[Source] = Field(default_factory=list)
