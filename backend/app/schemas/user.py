from datetime import datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, EmailStr, Field, computed_field, field_validator

from app.services.security import MAX_BCRYPT_PASSWORD_BYTES


class UserBase(BaseModel):
    username: str
    email: EmailStr
    nationality: str
    role: str
    score: int
    created_at: datetime
    last_connected_at: datetime
    is_active: bool


class UserProfile(BaseModel):
    id: str
    username: str
    email: EmailStr
    nationality: str
    role: str
    score: int
    created_at: datetime
    last_connected_at: datetime
    is_active: bool
    solves_count: Optional[int] = 0

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    nationality: Optional[str] = Field(None, min_length=2, max_length=10)
    current_password: Optional[str] = Field(None, max_length=256)
    new_password: Optional[str] = Field(None, min_length=6, max_length=100)

    @field_validator("nationality", mode="before")
    @classmethod
    def normalize_nationality(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v

    @field_validator("new_password")
    @classmethod
    def validate_new_password_bytes(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and len(v.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
            raise ValueError(f"Password cannot exceed {MAX_BCRYPT_PASSWORD_BYTES} UTF-8 bytes.")
        return v


class UserAdminUpdate(BaseModel):
    role: Optional[Literal["user", "admin"]] = None
    is_active: Optional[bool] = None
    nationality: Optional[str] = Field(None, min_length=2, max_length=10)
    score: Optional[int] = Field(None, ge=0)

    @field_validator("nationality", mode="before")
    @classmethod
    def normalize_nationality(cls, v: object) -> object:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class UserProfileSolvesBreakdown(BaseModel):
    category: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class RecentSolveDetail(BaseModel):
    challenge_title: str
    category: str
    difficulty: str
    points_awarded: int
    solved_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def challengeTitle(self) -> str:
        return self.challenge_title

    @computed_field
    @property
    def pointsAwarded(self) -> int:
        return self.points_awarded

    @computed_field
    @property
    def solvedAt(self) -> datetime:
        return self.solved_at


class UserPublicProfileDetail(BaseModel):
    id: str
    username: str
    nationality: str
    score: int
    global_rank: Optional[Union[int, str]] = None
    rank_name: str
    created_at: datetime
    solves_count: int
    solves_by_category: list[UserProfileSolvesBreakdown] = Field(default_factory=list)
    recent_solves: list[RecentSolveDetail] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def globalRank(self) -> Optional[Union[int, str]]:
        return self.global_rank

    @computed_field
    @property
    def rankName(self) -> str:
        return self.rank_name

    @computed_field
    @property
    def createdAt(self) -> datetime:
        return self.created_at

    @computed_field
    @property
    def solvesCount(self) -> int:
        return self.solves_count

    @computed_field
    @property
    def solvesByCategory(self) -> list[UserProfileSolvesBreakdown]:
        return self.solves_by_category

    @computed_field
    @property
    def recentSolves(self) -> list[RecentSolveDetail]:
        return self.recent_solves


class UserProfileDetail(UserPublicProfileDetail):
    email: EmailStr
    role: str
    last_connected_at: datetime
    is_active: bool

    @computed_field
    @property
    def lastConnectedAt(self) -> datetime:
        return self.last_connected_at

    @computed_field
    @property
    def isActive(self) -> bool:
        return self.is_active
