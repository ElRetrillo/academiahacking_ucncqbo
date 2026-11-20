from sqlalchemy import Boolean, Column, DateTime, Index, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base
from app.models.base_utils import generate_uuid, utc_now


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_active_role_score", "is_active", "role", "score"),
    )

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)
    nationality = Column(String(10), default="CL", nullable=False)
    score = Column(Integer, default=0, nullable=False)

    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    last_connected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
    instances = relationship("ChallengeInstance", back_populates="user", cascade="all, delete-orphan")
