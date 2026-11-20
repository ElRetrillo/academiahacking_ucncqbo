from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, String
from app.database import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(36), primary_key=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    revoked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
