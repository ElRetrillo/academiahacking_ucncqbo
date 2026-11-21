from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.instance import ChallengeInstance
    from app.models.solve import Solve, Submission


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (
        Index("ix_challenges_active_category_difficulty", "is_active", "category", "difficulty"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(50), default="web", nullable=False)
    difficulty: Mapped[str] = mapped_column(String(20), default="EASY", nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=100, nullable=False)

    flag: Mapped[str] = mapped_column(String(255), nullable=False)
    flag_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    target_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    hints: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    version: Mapped[str] = mapped_column(String(20), default="1.0", nullable=False)
    repository: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    solves_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False
    )

    solves: Mapped[list["Solve"]] = relationship("Solve", back_populates="challenge", cascade="all, delete-orphan")
    submissions: Mapped[list["Submission"]] = relationship(
        "Submission", back_populates="challenge", cascade="all, delete-orphan"
    )
    instances: Mapped[list["ChallengeInstance"]] = relationship(
        "ChallengeInstance", back_populates="challenge", cascade="all, delete-orphan"
    )
