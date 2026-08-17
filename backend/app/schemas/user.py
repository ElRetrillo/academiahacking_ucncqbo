from datetime import datetime
from typing import Optional, Union
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserBase(BaseModel):
    username: str
    email: EmailStr
    nationality: str
    role: str
    score: int
    created_at: datetime  # Registration / start date
    last_connected_at: datetime  # Last active telemetry
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
    current_password: Optional[str] = None
    new_password: Optional[str] = Field(None, min_length=6, max_length=100)


class UserAdminUpdate(BaseModel):
    role: Optional[str] = None  # "user" | "admin"
    is_active: Optional[bool] = None
    nationality: Optional[str] = None
    score: Optional[int] = None


class UserProfileSolvesBreakdown(BaseModel):
    category: str
    count: int

    model_config = ConfigDict(from_attributes=True)


class RecentSolveDetail(BaseModel):
    challenge_title: str
    challengeTitle: Optional[str] = None
    category: str
    difficulty: str
    points_awarded: int
    pointsAwarded: Optional[int] = None
    solved_at: datetime
    solvedAt: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class UserProfileDetail(BaseModel):
    id: str
    username: str
    email: EmailStr
    nationality: str
    role: str
    score: int
    global_rank: Optional[Union[int, str]] = None
    globalRank: Optional[Union[int, str]] = None
    rank_name: str
    rankName: Optional[str] = None
    created_at: datetime
    createdAt: Optional[datetime] = None
    last_connected_at: datetime
    lastConnectedAt: Optional[datetime] = None
    is_active: bool
    isActive: Optional[bool] = None
    solves_count: int
    solvesCount: Optional[int] = None
    solves_by_category: list[UserProfileSolvesBreakdown] = Field(default_factory=list)
    solvesByCategory: list[UserProfileSolvesBreakdown] = Field(default_factory=list)
    recent_solves: list[RecentSolveDetail] = Field(default_factory=list)
    recentSolves: list[RecentSolveDetail] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
