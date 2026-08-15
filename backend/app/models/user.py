import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), default="user", nullable=False)  # "user" | "admin"
    nationality = Column(String(10), default="CL", nullable=False)  # Country code (CL, AR, US, etc.)
    score = Column(Integer, default=0, nullable=False)
    
    # Telemetry
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)  # Start date / registration
    last_connected_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)  # Last connected
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    solves = relationship("Solve", back_populates="user", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="user", cascade="all, delete-orphan")
