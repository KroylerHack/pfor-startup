"""
PFOR Pydantic Schemas — Strategy
Validation models for strategy generation and history endpoints.
"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class StrategyGenerateRequest(BaseModel):
    """Payload for POST /api/v1/generate-strategy."""

    prompt_text: str = Field(..., min_length=20)
    language: str = "ru"

    @field_validator("prompt_text")
    @classmethod
    def prompt_not_empty(cls, v: str) -> str:
        value = v.strip()
        if len(value) < 20:
            raise ValueError("prompt_text must be at least 20 characters long.")
        return value

    @field_validator("language")
    @classmethod
    def language_supported(cls, value: str) -> str:
        lang = value.strip().lower()
        if lang not in {"ru", "uz", "en"}:
            raise ValueError("language must be one of: ru, uz, en")
        return lang


class StrategyGenerateResponse(BaseModel):
    """Full strategy generation result returned by the API."""

    id: int
    user_id: int | None
    prompt_text: str
    language: str
    status: str
    result_markdown: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class StrategyHistoryResponse(BaseModel):
    """List of strategy generation records."""

    total: int
    items: list[StrategyGenerateResponse]


# Backward-compatible aliases for older imports.
StrategyRequest = StrategyGenerateRequest
StrategyReportResponse = StrategyGenerateResponse
StrategyListResponse = StrategyHistoryResponse
