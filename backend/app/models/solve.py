from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.challenge import Challenge
    from app.models.user import User


class Solve(Base):
    __tablename__ = "solves"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge_solve"),
        Index("ix_solves_user_solved_at", "user_id", "solved_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    points_awarded: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    solved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="solves")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="solves")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_user_challenge_submitted", "user_id", "challenge_id", "submitted_at"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )
    submitted_flag: Mapped[str] = mapped_column(String(255), nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="submissions")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="submissions")
