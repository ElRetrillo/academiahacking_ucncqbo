import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


# Instance status values
STATUS_RUNNING = "running"
STATUS_STOPPED = "stopped"
STATUS_EXPIRED = "expired"


class ChallengeInstance(Base):
    """Represents "this user is working on this challenge".

    The container itself runs locally on the participant's machine (via the
    EclipSec CLI + Docker); this row is only the backend's record of the
    session, used for metadata hand-off and bookkeeping. The backend never
    runs Docker.
    """

    __tablename__ = "challenge_instances"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)

    status = Column(String(20), default=STATUS_RUNNING, nullable=False)  # running | stopped | expired

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at = Column(DateTime(timezone=True), default=utc_now, nullable=True)
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    expiration_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
    challenge = relationship("Challenge", back_populates="instances")


# Fast lookup for "the active instance of this user for this challenge"
Index("ix_instance_user_challenge_status", ChallengeInstance.user_id, ChallengeInstance.challenge_id, ChallengeInstance.status)
