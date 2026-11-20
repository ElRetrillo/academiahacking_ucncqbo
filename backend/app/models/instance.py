from sqlalchemy import Column, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now

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

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(20), default=STATUS_RUNNING, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    expiration_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="instances")
    challenge = relationship("Challenge", back_populates="instances")
