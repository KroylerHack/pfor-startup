"""
PFOR Platform — FastAPI Application Entry Point
Initializes the database, registers routers, and configures CORS.
"""
import logging
import os

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from pfor.api.auth import router as auth_router
from pfor.api.strategy import router as strategy_router
from pfor.core.config import get_settings
from pfor.db.database import engine, init_db

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_path = os.path.join(BASE_DIR, "frontend")

# Монтирование статики
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# App initialization
# ---------------------------------------------------------------------------
settings = get_settings()

app = FastAPI(
    title="PFOR — Operational Solutions Platform",
    description=(
        "Closed B2B SaaS API that transforms business problems into deep "
        "strategy documents via local Ollama + PostgreSQL infrastructure."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS — allow all origins in development; restrict in production
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Разрешаем доступ со всех IP, включая 178.218.207.173
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------
app.include_router(auth_router)
app.include_router(strategy_router)


# ---------------------------------------------------------------------------
# Dependency checks
# ---------------------------------------------------------------------------

async def check_database_connection() -> tuple[bool, str]:
    """Check that PostgreSQL is reachable and accepting queries."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        logger.info("PostgreSQL connection check: OK")
        return True, "postgresql_ok"
    except Exception as exc:  # pragma: no cover - runtime dependency check
        logger.exception("PostgreSQL connection check failed")
        return False, f"postgresql_error: {exc}"


async def check_ollama_connection() -> tuple[bool, str]:
    """Check that the local Ollama service is reachable."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
        logger.info("Ollama connection check: OK")
        return True, "ollama_ok"
    except Exception as exc:  # pragma: no cover - runtime dependency check
        logger.exception("Ollama connection check failed")
        return False, f"ollama_error: {exc}"


@app.on_event("startup")
async def on_startup() -> None:
    """Initialize the PostgreSQL tables and verify external dependencies."""
    logger.info("PFOR API starting up...")
    try:
        init_db()
        logger.info("PostgreSQL: %s", settings.database_url)
    except Exception as exc:  # pragma: no cover - runtime dependency check
        logger.warning("Database initialization failed at startup: %s", exc)
        app.state.db_status = f"postgresql_error: {exc}"
    else:
        app.state.db_status = "postgresql_ok"

    logger.info("Ollama API: %s", settings.OLLAMA_BASE_URL)
    logger.info("Ollama model: %s", settings.OLLAMA_MODEL)

    db_ok, db_message = await check_database_connection()
    ollama_ok, ollama_message = await check_ollama_connection()
    app.state.db_status = db_message
    app.state.ollama_status = ollama_message

    if not db_ok:
        logger.warning("Startup dependency check failed: %s", db_message)
    if not ollama_ok:
        logger.warning("Startup dependency check failed: %s", ollama_message)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------
@app.get("/health", tags=["System"], summary="Health check")
async def health_check():
    """Return service health status and configuration summary."""
    db_ok = getattr(app.state, "db_status", "unknown")
    ollama_ok = getattr(app.state, "ollama_status", "unknown")
    return JSONResponse(
        {
            "status": "ok" if "ok" in str(db_ok) or "ok" in str(ollama_ok) else "degraded",
            "database": db_ok,
            "ollama": ollama_ok,
            "ollama_model": settings.OLLAMA_MODEL,
            "version": "1.0.0",
        }
    )


frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")

@app.get("/", tags=["System"], summary="Root endpoint")
def root():
    """Serve the frontend index.html on the root path."""
    return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("pfor.main:app", host="0.0.0.0", port=8000, reload=True)

