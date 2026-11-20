from pathlib import Path
from typing import List, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{(BACKEND_DIR / 'ctf.db').as_posix()}"


class Settings(BaseSettings):
    PROJECT_NAME: str = "EclipSec CTF API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = DEFAULT_DATABASE_URL

    JWT_SECRET: str = "change-this-in-production-super-secret-ctf-key-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://eclipsec.cl",
        "https://www.eclipsec.cl",
    ]

    CORS_ORIGIN_REGEX: str = r"^https:\/\/.*\.vercel\.app$"

    CHALLENGES_BASE_URL: str = ""
    CHALLENGES_REPOSITORY: str = "ElRetrillo/retos_ctf"

    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@eclipsec.cl"
    ADMIN_PASSWORD: str = "admin123456"

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: str) -> str:
        if not v:
            return DEFAULT_DATABASE_URL
        if v.startswith("sqlite+aiosqlite:///./"):
            relative_path = v.removeprefix("sqlite+aiosqlite:///./")
            return f"sqlite+aiosqlite:///{(BACKEND_DIR / relative_path).as_posix()}"
        if v.startswith("postgres://"):
            return v.replace("postgres://", "postgresql+asyncpg://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, str)):
            return v
        return []


settings = Settings()
