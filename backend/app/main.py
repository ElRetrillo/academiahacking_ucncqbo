from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_v1_router, ctf_academy_router
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Automatically create tables if they do not exist
    await init_db()
    
    # If the database is empty (no challenges seeded), run the seeding script automatically
    from app.database import AsyncSessionLocal
    from app.models.challenge import Challenge
    from sqlalchemy import select
    
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Challenge).limit(1))
            has_challenges = result.first() is not None
        
        if not has_challenges:
            from seed import seed
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

# CORS configuration matching settings and vercel previews
origins = []
if isinstance(settings.CORS_ORIGINS, list):
    origins = settings.CORS_ORIGINS
else:
    origins = [settings.CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register database-backed routers
app.include_router(api_v1_router)
app.include_router(ctf_academy_router)


@app.get("/")
@app.get("/health")
async def health():
    return {"status": "ok"}
