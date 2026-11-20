from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import UserProfile
from app.services.security import MAX_BCRYPT_PASSWORD_BYTES


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    nationality: str = Field(default="CL", min_length=2, max_length=10)

    @field_validator("email", mode="before")
    @classmethod
    def normalize_email(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().lower()
        return v

    @field_validator("password")
    @classmethod
    def validate_password_byte_length(cls, v: str) -> str:
        if len(v.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError(f"Password cannot exceed {MAX_BCRYPT_PASSWORD_BYTES} UTF-8 bytes.")
        return v

    @field_validator("nationality", mode="before")
    @classmethod
    def normalize_nationality(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class LoginRequest(BaseModel):
    username_or_email: str = Field(..., min_length=3, max_length=256)
    password: str = Field(..., min_length=1, max_length=256)

    @field_validator("username_or_email", mode="before")
    @classmethod
    def strip_identifier(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip()
        return v


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class SessionResponse(BaseModel):
    authenticated: bool = True
    user: UserProfile


class LogoutResponse(BaseModel):
    authenticated: bool = False
    message: str
