"""
main.py — FastAPI application entry point.

Responsibilities:
  - Create and configure the FastAPI app instance.
  - Register middleware (CORS, rate limiting).
  - Mount all routers.
  - Define the /health endpoint.
  - Pre-load the knowledge base at startup so the first request is fast.
  - Configure structured logging.
"""

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.config import settings
from app.routes.chat import router as chat_router
from app.schemas.chat_response import HealthResponse
from app.services.knowledge_service import load_knowledge


# ---------------------------------------------------------------------------
# Logging — structured, human-readable format
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rate limiter — shared instance used by all routes
# ---------------------------------------------------------------------------

limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Lifespan — startup / shutdown logic
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Async context manager for startup and shutdown events.

    Startup:
      1. Validate required settings (GROQ_API_KEY).
      2. Pre-load the knowledge base into memory so the first request
         doesn't incur a disk read.

    Shutdown:
      Logs a clean shutdown message (extend here for DB connection teardown etc.)
    """
    # --- Startup ---
    logger.info("=" * 60)
    logger.info("Starting %s v%s", settings.app_title, settings.app_version)

    try:
        settings.validate()
        logger.info("Configuration validated ✓")
    except ValueError as exc:
        logger.critical("Configuration error: %s", exc)
        sys.exit(1)

    try:
        load_knowledge(settings.knowledge_dir)
        logger.info("Knowledge base pre-loaded ✓")
    except FileNotFoundError as exc:
        # Non-fatal: warn and continue — knowledge dir may be added later
        logger.warning("Knowledge directory not found: %s", exc)

    logger.info("Server ready. Listening for requests.")
    logger.info("=" * 60)

    yield  # Application runs here

    # --- Shutdown ---
    logger.info("Shutting down %s.", settings.app_title)


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description=settings.app_description,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Attach the rate limiter to the app state so slowapi can find it
app.state.limiter = limiter

# Register the rate-limit exceeded handler (returns 429 JSON automatically)
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global exception handler — catch-all for unhandled errors
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a clean 500 response instead of a raw Python traceback."""
    logger.error(
        "Unhandled exception on %s %s: %s",
        request.method,
        request.url.path,
        exc,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(chat_router, prefix="/api", tags=["Chat"])


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Health check",
    description="Returns 200 OK when the server is running. Use this for uptime monitors and deployment health checks.",
)
async def health_check() -> HealthResponse:
    logger.debug("GET /health")
    return HealthResponse(status="ok")


# ---------------------------------------------------------------------------
# Root redirect to docs
# ---------------------------------------------------------------------------

@app.get("/", include_in_schema=False)
async def root():
    """Redirect visitors at / to the interactive API docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")
