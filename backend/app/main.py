import importlib
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1 import api_v1_router, ctf_academy_router
from app.config import settings
from app.database import AsyncSessionLocal, get_db, init_db

logger = logging.getLogger(__name__)

_SENSITIVE_NO_STORE_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/admin/",
    "/api/ctf-academy",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    if settings.AUTO_SEED_ENABLED:
        try:
            try:
                from seed import sync_seed_data
            except ImportError:
                sync_seed_data = importlib.import_module("backend.seed").sync_seed_data

            async with AsyncSessionLocal() as db:
                summary = await sync_seed_data(db)
            if summary["admin_created"] or summary["challenges_added"]:
                logger.info(
                    "Seed sync applied: admin_created=%s, challenges_added=%s",
                    summary["admin_created"],
                    summary["challenges_added"],
                )
        except Exception as exc:
            logger.warning("Automatic seeding check failed or was skipped: %s", exc)

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-CSRF-Token"],
)


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.ENVIRONMENT.lower() == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    if request.url.path.startswith(_SENSITIVE_NO_STORE_PREFIXES):
        response.headers["Cache-Control"] = "no-store"
    return response


app.include_router(api_v1_router)
app.include_router(ctf_academy_router)


@app.get("/")
async def root():
    return {"status": "ok"}


@app.get("/health")
async def health(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception as exc:
        logger.warning("Database health check failed: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": "error"},
        )
