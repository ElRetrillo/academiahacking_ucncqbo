import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.services.security import REDACTED_FLAG_MARKER

ALLOWED_DIFFICULTIES = {"EASY", "MEDIUM", "HARD", "INSANE"}
_CATEGORY_PATTERN = re.compile(r"^[a-z0-9_-]+$")


def _normalize_category(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    normalized = v.strip().lower()
    if not normalized or not _CATEGORY_PATTERN.match(normalized):
        raise ValueError("category must contain only lowercase letters, numbers, '-' or '_'.")
    return normalized


def _normalize_difficulty(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    normalized = v.strip().upper()
    if normalized not in ALLOWED_DIFFICULTIES:
        raise ValueError(f"difficulty must be one of: {', '.join(sorted(ALLOWED_DIFFICULTIES))}.")
    return normalized


def _validate_target_url(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    stripped = v.strip()
    if not stripped:
        return None
    if stripped.startswith(("http://", "https://")):
        return stripped
    if stripped.startswith("/") and not stripped.startswith("//"):
        return stripped
    raise ValueError("target_url must be a relative path starting with '/' or an http(s) URL.")


def _validate_repo_path(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    stripped = v.strip()
    if not stripped:
        return None
    if stripped.startswith("/") or "\\" in stripped or ".." in stripped.split("/"):
        raise ValueError("path must be a relative repository path without '..' segments.")
    return stripped


def _validate_flag_value(v: Optional[str]) -> Optional[str]:
    if v is None:
        return None
    stripped = v.strip()
    if not stripped or stripped == REDACTED_FLAG_MARKER:
        raise ValueError("flag must be a non-empty secret value.")
    return stripped


class ChallengeBase(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    description: str
    category: str = Field(default="web", max_length=50)
    difficulty: str = Field(default="EASY")
    points: int = Field(default=100, ge=1)
    target_url: Optional[str] = None
    hints: Optional[str] = None
    version: str = Field(default="1.0", max_length=20)
    repository: Optional[str] = None
    path: Optional[str] = None

    @field_validator("category")
    @classmethod
    def check_category(cls, v: str) -> str:
        res = _normalize_category(v)
        assert res is not None
        return res

    @field_validator("difficulty")
    @classmethod
    def check_difficulty(cls, v: str) -> str:
        res = _normalize_difficulty(v)
        assert res is not None
        return res

    @field_validator("target_url")
    @classmethod
    def check_target_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_target_url(v)

    @field_validator("path")
    @classmethod
    def check_path(cls, v: Optional[str]) -> Optional[str]:
        return _validate_repo_path(v)


class ChallengeCreate(ChallengeBase):
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    flag: str = Field(..., min_length=1, max_length=255)

    @field_validator("flag")
    @classmethod
    def check_flag(cls, v: str) -> str:
        res = _validate_flag_value(v)
        assert res is not None
        return res


class ChallengeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    difficulty: Optional[str] = None
    points: Optional[int] = Field(None, ge=1)
    target_url: Optional[str] = None
    hints: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    repository: Optional[str] = None
    path: Optional[str] = None
    flag: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None

    @field_validator("category")
    @classmethod
    def check_category(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_category(v)

    @field_validator("difficulty")
    @classmethod
    def check_difficulty(cls, v: Optional[str]) -> Optional[str]:
        return _normalize_difficulty(v)

    @field_validator("target_url")
    @classmethod
    def check_target_url(cls, v: Optional[str]) -> Optional[str]:
        return _validate_target_url(v)

    @field_validator("path")
    @classmethod
    def check_path(cls, v: Optional[str]) -> Optional[str]:
        return _validate_repo_path(v)

    @field_validator("flag")
    @classmethod
    def check_flag(cls, v: Optional[str]) -> Optional[str]:
        return _validate_flag_value(v)


class ChallengePublic(ChallengeBase):
    id: str
    slug: str
    solves_count: int
    is_solved: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChallengeAdmin(ChallengeBase):
    id: str
    slug: str
    flag: str = REDACTED_FLAG_MARKER
    flag_configured: bool = True
    is_active: bool
    solves_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class FlagSubmissionRequest(BaseModel):
    flag: str = Field(..., min_length=1, max_length=255)


class FlagSubmissionResponse(BaseModel):
    is_correct: bool
    message: str
    points_awarded: int = 0
    new_total_score: int = 0


class InstanceChallengeInfo(BaseModel):
    id: str
    slug: str
    title: str
    category: str
    difficulty: str
    points: int
    version: str
    repository: Optional[str] = None
    path: Optional[str] = None
    target_url: Optional[str] = None


class ChallengeInstanceResponse(BaseModel):
    id: str
    status: str
    created_at: datetime
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    expiration_at: Optional[datetime] = None
    challenge: InstanceChallengeInfo

    model_config = ConfigDict(from_attributes=True)
