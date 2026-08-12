"""
PFOR API — Strategy Generation Endpoints
Accepts a business problem, runs the Ollama-backed pipeline,
persists the result, and returns the structured Markdown report.
"""
import logging

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from pfor.api.auth import get_user_from_token
from pfor.core.agents import MultiAgentPipeline
from pfor.core.config import get_settings
from pfor.db.database import get_db
from pfor.db.models import StrategyRequest as StrategyRequestModel, User
from pfor.schemas.strategy import (
    StrategyGenerateRequest,
    StrategyGenerateResponse,
    StrategyHistoryResponse,
)

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/api/v1", tags=["Strategy"])
_pipeline = MultiAgentPipeline(
    base_url=settings.OLLAMA_BASE_URL,
    model=settings.OLLAMA_MODEL,
)


def _optional_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User | None:
    """Resolve the current user from a Bearer token if present."""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return get_user_from_token(token, db)
    except HTTPException:
        return None


@router.post(
    "/generate-strategy",
    response_model=StrategyGenerateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate a strategic report from a business problem via Ollama",
)
async def generate_strategy(
    payload: StrategyGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(_optional_user),
):
    """Create a processing record, generate a report in Ollama, and persist the result."""
    user_id = current_user.id if current_user else None
    logger.info(
        "Generating strategy for user_id=%s | prompt='%.80s...'",
        user_id,
        payload.prompt_text,
    )

    record = StrategyRequestModel(
        user_id=user_id,
        prompt_text=payload.prompt_text,
        language=payload.language,
        status="processing",
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    try:
        report_text = await _pipeline.run(payload.prompt_text, payload.language)
        record.result_markdown = report_text
        record.status = "completed"
        db.commit()
        db.refresh(record)
        logger.info("Strategy record id=%s completed successfully.", record.id)
        return StrategyGenerateResponse.model_validate(record)
    except Exception as exc:
        record.status = "failed"
        record.result_markdown = str(exc)
        try:
            db.commit()
        except Exception:
            db.rollback()
        logger.exception("Strategy generation failed for record id=%s", record.id)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Strategy generation is currently unavailable because the backend dependencies are unreachable.",
        ) from exc


@router.get(
    "/history",
    response_model=StrategyHistoryResponse,
    summary="Return the strategy report history for the authenticated user",
)
def get_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(_optional_user),
):
    """Return recent strategy records for the current user, or an empty list for anonymous views."""
    if current_user is None:
        return StrategyHistoryResponse(total=0, items=[])

    query = db.query(StrategyRequestModel).filter(StrategyRequestModel.user_id == current_user.id)
    total = query.count()
    items = (
        query.order_by(StrategyRequestModel.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    return StrategyHistoryResponse(
        total=total,
        items=[StrategyGenerateResponse.model_validate(item) for item in items],
    )


# Backward-compatible legacy routes.
legacy_router = APIRouter(prefix="/api", tags=["Legacy Strategy"])


@legacy_router.post(
    "/strategy/generate",
    response_model=StrategyGenerateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def legacy_generate(
    payload: StrategyGenerateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(_optional_user),
):
    return await generate_strategy(payload, db, current_user)


@legacy_router.get("/strategy/history", response_model=StrategyHistoryResponse)
def legacy_history(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(_optional_user),
):
    return get_history(skip=skip, limit=limit, db=db, current_user=current_user)


router.include_router(legacy_router)
