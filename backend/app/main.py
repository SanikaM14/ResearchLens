"""
ResearchLens — Evidence-Grounded AI Research Paper Intelligence Platform.

Main FastAPI application entry point.
"""
import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.config import get_settings
from app.core.database import init_db
from app.api.routes import documents, research, health, auth

# ─────────────────────────────────────────────
# Logging Configuration
# ─────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("researchlens")

# ─────────────────────────────────────────────
# Application Setup
# ─────────────────────────────────────────────

settings = get_settings()

from app.core.limiter import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    # Startup
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(settings.CHROMA_PERSIST_DIR, exist_ok=True)
    await init_db()
    logger.info("═" * 60)
    logger.info("  ResearchLens API v1.0.0 — Starting up")
    logger.info(f"  LLM Model: {settings.LLM_MODEL}")
    logger.info(f"  Embedding Model: {settings.EMBEDDING_MODEL}")
    logger.info(f"  Rate Limit: {settings.RATE_LIMIT_PER_MINUTE} req/min/IP")
    logger.info(f"  Max Upload: {settings.MAX_UPLOAD_SIZE_MB}MB")
    logger.info(f"  CORS Origins: {settings.cors_origins_list}")
    logger.info("═" * 60)
    yield
    # Shutdown
    logger.info("ResearchLens API shutting down.")


app = FastAPI(
    title="ResearchLens API",
    description="Evidence-Grounded AI Research Paper Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

from fastapi.staticfiles import StaticFiles
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# ─────────────────────────────────────────────
# Middleware
# ─────────────────────────────────────────────

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────
# Routes
# ─────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(research.router)

# ─────────────────────────────────────────────
# Exception Handlers (never expose internals)
# ─────────────────────────────────────────────


@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "The requested resource was not found."},
    )


@app.exception_handler(413)
async def payload_too_large_handler(request: Request, exc):
    return JSONResponse(
        status_code=413,
        content={"detail": f"File too large. Maximum size is {settings.MAX_UPLOAD_SIZE_MB}MB."},
    )


@app.exception_handler(415)
async def unsupported_media_handler(request: Request, exc):
    return JSONResponse(
        status_code=415,
        content={"detail": "Unsupported file type. Only PDF files are accepted."},
    )


@app.exception_handler(422)
async def validation_error_handler(request: Request, exc):
    return JSONResponse(
        status_code=422,
        content={"detail": "Invalid request. Please check your input and try again."},
    )


@app.exception_handler(500)
async def internal_server_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."},
    )
