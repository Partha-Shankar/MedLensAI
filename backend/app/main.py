"""
MedLens AI — main.py
FastAPI application entry point.

Startup sequence:
  1. Validate configuration (GROQ_API_KEY check)
  2. Eagerly load TrOCR model (so first request is fast)
  3. Eagerly load PaddleOCR
  4. Mount API router
  5. Add CORS middleware (open during development)

Run with:
  uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
"""
from __future__ import annotations

import datetime
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.routes import router
from app.utils.helpers import get_logger

logger = get_logger("MAIN")


def _ts() -> str:
    return datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]


# ── Lifespan (startup / shutdown) ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Eagerly warm up all ML models at startup so the first request is fast."""
    t0 = time.perf_counter()
    logger.info(f"[{_ts()}] [MAIN] ===== MedLens AI starting up =====")

    # ── Drug index ─────────────────────────────────────────────────────────────
    try:
        from app.services.drug_corrector import _load_drug_index
        idx = _load_drug_index()
        logger.info(f"[{_ts()}] [MAIN] Drug index loaded ({len(idx)} entries)")
    except Exception as exc:
        logger.error(f"[{_ts()}] [MAIN] Drug index load failed: {exc}")

    # ── Config check ──────────────────────────────────────────────────────────
    if not settings.GROQ_API_KEY:
        logger.warning(
            f"[{_ts()}] [MAIN] GROQ_API_KEY is not set — "
            "Groq fallback and /validate-dosage will be unavailable"
        )
    else:
        logger.info(f"[{_ts()}] [MAIN] Groq API key detected")

    elapsed = round((time.perf_counter() - t0) * 1000)
    logger.info(f"[{_ts()}] [MAIN] Startup complete in {elapsed} ms")
    logger.info(f"[{_ts()}] [MAIN] ===== MedLens AI ready =====")

    yield  # ← application is running

    logger.info(f"[{_ts()}] [MAIN] ===== MedLens AI shutting down =====")


# ── App factory ───────────────────────────────────────────────────────────────

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "MedLens AI — Prescription OCR and Safety Analysis Backend. "
            "Extracts structured medication data from handwritten Indian prescriptions."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],          # Restrict in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(router)

    # ── Health check ──────────────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health():
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        }

    return app


app = create_app()


# ── Dev runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
