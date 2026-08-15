import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text
from sqlalchemy.orm import relationship
from app.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Challenge(Base):
    __tablename__ = "challenges"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    slug = Column(String(50), unique=True, index=True, nullable=False)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), default="web", nullable=False)  # web, pwn, crypto, forensic, rev, osint, misc
    difficulty = Column(String(20), default="EASY", nullable=False)  # EASY, MEDIUM, HARD, INSANE
    points = Column(Integer, default=100, nullable=False)
    
    # Flag validation
    flag = Column(String(255), nullable=False)  # Plain/Standard format e.g. EclipSec{...}
    flag_hash = Column(String(64), nullable=True)  # SHA-256 hash for fast constant-time verification
    
    # Instance URL / endpoint
    target_url = Column(String(255), nullable=True)  # e.g., /web-001/ or http://host:8001
    hints = Column(Text, nullable=True)  # Optional JSON or plaintext hints
    
    is_active = Column(Boolean, default=True, nullable=False)
    solves_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)

    # Relationships
    solves = relationship("Solve", back_populates="challenge", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="challenge", cascade="all, delete-orphan")
