from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now

if TYPE_CHECKING:
    from app.models.challenge import Challenge
    from app.models.user import User

STATUS_RUNNING = "running"
STATUS_STOPPED = "stopped"
STATUS_EXPIRED = "expired"


class ChallengeInstance(Base):
    """Represents that a participant has an active or historical local challenge session."""

    __tablename__ = "challenge_instances"
    __table_args__ = (
        Index(
            "ix_instance_user_challenge_status",
            "user_id",
            "challenge_id",
            "status",
        ),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    challenge_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status: Mapped[str] = mapped_column(String(20), default=STATUS_RUNNING, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=True
    )
    stopped_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    expiration_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="instances")
    challenge: Mapped["Challenge"] = relationship("Challenge", back_populates="instances")
