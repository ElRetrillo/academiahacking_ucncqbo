from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now


class Solve(Base):
    __tablename__ = "solves"
    __table_args__ = (
        UniqueConstraint("user_id", "challenge_id", name="uq_user_challenge_solve"),
        Index("ix_solves_user_solved_at", "user_id", "solved_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    points_awarded = Column(Integer, default=0, nullable=False)
    solved_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="solves")
    challenge = relationship("Challenge", back_populates="solves")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_user_challenge_submitted", "user_id", "challenge_id", "submitted_at"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    challenge_id = Column(String(36), ForeignKey("challenges.id", ondelete="CASCADE"), nullable=False, index=True)
    submitted_flag = Column(String(255), nullable=False)
    is_correct = Column(Boolean, default=False, nullable=False)
    submitted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    user = relationship("User", back_populates="submissions")
    challenge = relationship("Challenge", back_populates="submissions")
