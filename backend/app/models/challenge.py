from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now


class Challenge(Base):
    __tablename__ = "challenges"
    __table_args__ = (
        Index("ix_challenges_active_category_difficulty", "is_active", "category", "difficulty"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="web", nullable=False)
    difficulty = Column(String(20), default="EASY", nullable=False)
    points = Column(Integer, default=100, nullable=False)

    flag = Column(String(255), nullable=False)
    flag_hash = Column(String(64), nullable=True)

    target_url = Column(String(255), nullable=True)
    hints = Column(Text, nullable=True)

    version = Column(String(20), default="1.0", nullable=False)
    repository = Column(String(255), nullable=True)
    path = Column(String(255), nullable=True)

    is_active = Column(Boolean, default=True, nullable=False)
    solves_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)

    solves = relationship("Solve", back_populates="challenge", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="challenge", cascade="all, delete-orphan")
    instances = relationship("ChallengeInstance", back_populates="challenge", cascade="all, delete-orphan")
