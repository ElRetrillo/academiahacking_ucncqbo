from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1 import api_v1_router, ctf_academy_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
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
