from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


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


class ChallengeCreate(ChallengeBase):
    slug: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-zA-Z0-9_-]+$")
    flag: str = Field(..., min_length=1, max_length=255)


class ChallengeUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    points: Optional[int] = Field(None, ge=1)
    target_url: Optional[str] = None
    hints: Optional[str] = None
    version: Optional[str] = Field(None, max_length=20)
    repository: Optional[str] = None
    path: Optional[str] = None
    flag: Optional[str] = None
    is_active: Optional[bool] = None


class ChallengePublic(ChallengeBase):
    id: str
    slug: str
    solves_count: int
    is_solved: bool = False

    model_config = ConfigDict(from_attributes=True)


class ChallengeAdmin(ChallengeBase):
    id: str
    slug: str
    flag: str = "[REDACTED]"
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
