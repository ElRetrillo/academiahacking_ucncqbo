from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.revoked_token import RevokedToken


class SqlAlchemyTokenRevocationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def is_revoked(self, jti: str) -> bool:
        if not jti:
            return False
        res = await self._db.execute(select(RevokedToken.jti).where(RevokedToken.jti == jti))
        return res.scalar_one_or_none() is not None

    async def revoke(self, jti: str, expires_at: datetime) -> None:
        if not jti:
            return

        now = datetime.now(timezone.utc)
        await self._db.execute(delete(RevokedToken).where(RevokedToken.expires_at < now))

        if await self.is_revoked(jti):
            await self._db.commit()
            return

        self._db.add(RevokedToken(jti=jti, expires_at=expires_at))
        try:
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()
