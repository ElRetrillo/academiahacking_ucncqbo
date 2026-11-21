from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.instance import ChallengeInstance
    from app.models.solve import Solve, Submission


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_active_role_score", "is_active", "role", "score"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="user", nullable=False)
    nationality: Mapped[str] = mapped_column(String(10), default="CL", nullable=False)
    score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_connected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    solves: Mapped[list["Solve"]] = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission", back_populates="user", cascade="all, delete-orphan"
    )
    instances: Mapped[list["ChallengeInstance"]] = relationship(
        "ChallengeInstance", back_populates="user", cascade="all, delete-orphan"
    )
