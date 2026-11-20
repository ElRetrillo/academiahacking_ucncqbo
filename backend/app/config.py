from pathlib import Path
from typing import List, Optional, Union

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = f"sqlite+aiosqlite:///{(BACKEND_DIR / 'ctf.db').as_posix()}"

_DEV_JWT_MARKERS = ("change-this-in-production", "example_", "CHANGE_ME")
_DEV_HMAC_MARKERS = ("dev-only", "example_", "CHANGE_ME")
_ALLOWED_SAMESITE_VALUES = {"lax", "strict", "none"}


class Settings(BaseSettings):
    PROJECT_NAME: str = "EclipSec CTF API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"

    DATABASE_URL: str = DEFAULT_DATABASE_URL
    DB_ECHO: bool = False
    AUTO_SEED_ENABLED: bool = True

    JWT_SECRET: str = "change-this-in-production-super-secret-ctf-key-2026"
    FLAG_HMAC_SECRET: str = "dev-only-flag-hmac-secret-replace-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    CLI_TOKEN_EXPIRE_MINUTES: int = 60 * 12

    CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://eclipsec.cl",
        "https://www.eclipsec.cl",
    ]
    CORS_ORIGIN_REGEX: str = ""

    COOKIE_NAME: str = "eclipsec_session"
    CSRF_COOKIE_NAME: str = "eclipsec_csrf"
    COOKIE_SECURE: Optional[bool] = None
    COOKIE_SAMESITE: str = "lax"
    COOKIE_DOMAIN: Optional[str] = None

    ALLOW_FIRST_USER_ADMIN: bool = False
    TRUSTED_PROXY_COUNT: int = 0

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_AUTH_MAX: int = 10
    RATE_LIMIT_AUTH_WINDOW_SECONDS: int = 60
    RATE_LIMIT_FLAG_MAX: int = 15
    RATE_LIMIT_FLAG_WINDOW_SECONDS: int = 60

    CHALLENGES_BASE_URL: str = ""
    CHALLENGES_REPOSITORY: str = "ElRetrillo/retos_ctf"
    CHALLENGES_FLAGS_FILE: str = ""

    ADMIN_USERNAME: str = "admin"
    ADMIN_EMAIL: str = "admin@eclipsec.cl"
    ADMIN_PASSWORD: str = "admin123456"

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cookie_secure_effective(self) -> bool:
        if self.COOKIE_SECURE is not None:
            return self.COOKIE_SECURE
        return self.ENVIRONMENT.lower() == "production"

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
        if isinstance(v, (list, str)):
            return v
        return []

    @field_validator("COOKIE_SAMESITE", mode="before")
    @classmethod
    def validate_cookie_samesite(cls, v: str) -> str:
        normalized = str(v).strip().lower()
        if normalized not in _ALLOWED_SAMESITE_VALUES:
            raise ValueError("COOKIE_SAMESITE must be one of: lax, strict, none.")
        return normalized

    @field_validator("TRUSTED_PROXY_COUNT")
    @classmethod
    def validate_trusted_proxy_count(cls, v: int) -> int:
        if v < 0:
            raise ValueError("TRUSTED_PROXY_COUNT must be non-negative.")
        return v

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.ENVIRONMENT.lower() != "production":
            return self

        if len(self.JWT_SECRET) < 32 or any(m in self.JWT_SECRET for m in _DEV_JWT_MARKERS):
            raise ValueError("JWT_SECRET must be at least 32 characters and not a default placeholder in production.")

        if len(self.FLAG_HMAC_SECRET) < 32 or any(m in self.FLAG_HMAC_SECRET for m in _DEV_HMAC_MARKERS):
            raise ValueError("FLAG_HMAC_SECRET must be at least 32 characters and not a default placeholder in production.")

        if "*" in self.CORS_ORIGINS:
            raise ValueError("CORS_ORIGINS cannot contain wildcard '*' when allow_credentials is enabled.")

        if self.CORS_ORIGIN_REGEX and r".*\.vercel\.app" in self.CORS_ORIGIN_REGEX:
            raise ValueError("CORS_ORIGIN_REGEX cannot allow arbitrary vercel.app subdomains in production.")

        if self.COOKIE_SAMESITE == "none" and not self.cookie_secure_effective:
            raise ValueError("COOKIE_SAMESITE='none' requires Secure cookies in production.")

        return self


settings = Settings()
