from sqlalchemy import Column, DateTime, String

from app.database import Base
from app.models.base_utils import utc_now


class RevokedToken(Base):
    __tablename__ = "revoked_tokens"

    jti = Column(String(36), primary_key=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
