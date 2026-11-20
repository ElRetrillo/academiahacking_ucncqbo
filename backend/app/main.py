from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.api.v1 import api_v1_router, ctf_academy_router
from app.database import AsyncSessionLocal, init_db
from app.models.challenge import Challenge

_SENSITIVE_NO_STORE_PREFIXES = (
    "/api/v1/auth/",
    "/api/v1/admin/",
    "/api/ctf-academy",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()

    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Challenge).limit(1))
            has_challenges = result.first() is not None

        if not has_challenges:
            try:
                from seed import seed
            except ImportError:
                from backend.seed import seed
            print("No challenges found in the database. Running automatic seeding...")
            await seed()
            print("Automatic seeding completed successfully.")
    except Exception as e:
        print(f"Warning: Auto-seeding check failed or was skipped: {e}")

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
@app.get("/health")
async def health():
    return {"status": "ok"}
