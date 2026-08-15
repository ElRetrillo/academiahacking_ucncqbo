from datetime import datetime
from typing import Optional
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
