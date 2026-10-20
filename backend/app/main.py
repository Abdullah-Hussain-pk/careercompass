"""
CareerCompass – FastAPI application entry point.

All routers are versioned under /api/v1.
Includes:
  - CORS configuration (allow-list from settings)
  - Rate limiting (slowapi)
  - OpenAPI documentation at /docs and /redoc
  - Health-check endpoint (NFR-6)
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import get_settings
from app.routers import auth, assessment, recommendations, skillgap, booking, admin, expert

settings = get_settings()

# Global rate limiter (auth routes add their own limits)
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run seed on startup in development mode."""
    if settings.ENVIRONMENT == "development":
        try:
            from app.data.seed import seed
            await seed()
        except Exception as e:
            print(f"⚠️  Seed skipped or failed: {e}")
    yield


app = FastAPI(
    title="CareerCompass API",
    version="1.0.0",
    description=(
        "Explainable career consultation platform for Pakistani students. "
        "Hybrid recommender engine with RIASEC interest test, skill-gap analysis, "
        "counsellor booking, and admin dashboard."
    ),
    openapi_url="/api/v1/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Middleware ─────────────────────────────────────────────────────────────

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS – restrict to allow-list (security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────

PREFIX = "/api/v1"

app.include_router(auth.router, prefix=PREFIX)
app.include_router(assessment.router, prefix=PREFIX)
app.include_router(recommendations.router, prefix=PREFIX)
app.include_router(skillgap.router, prefix=PREFIX)
app.include_router(booking.router, prefix=PREFIX)
app.include_router(admin.router, prefix=PREFIX)
app.include_router(expert.router, prefix=PREFIX)


# ── Health check (NFR-6) ──────────────────────────────────────────────────

@app.get("/health", tags=["Health"])
async def health_check() -> dict:
    """
    Health-check endpoint for Docker restart policy and load balancer probes.
    Returns 200 OK when the application is ready.
    """
    return {"status": "ok", "version": settings.APP_VERSION, "env": settings.ENVIRONMENT}


# ── Root ──────────────────────────────────────────────────────────────────

@app.get("/", tags=["Root"])
async def root() -> dict:
    """API root – redirects clients to the docs."""
    return {
        "message": "CareerCompass API",
        "docs": "/docs",
        "version": "1.0.0",
    }


# ── Global error handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler – returns a consistent error format.
    Does NOT log sensitive data (NFR security).
    """
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred", "code": "INTERNAL_ERROR"},
    )
