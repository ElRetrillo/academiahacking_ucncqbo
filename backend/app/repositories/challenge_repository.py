from datetime import datetime
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.instance import ChallengeInstance, STATUS_RUNNING, STATUS_STOPPED
from app.models.solve import Solve, Submission
from app.models.user import User


class SqlAlchemyChallengeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_active(
        self,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> list[Challenge]:
        query = select(Challenge).where(Challenge.is_active.is_(True))
        if category:
            query = query.where(Challenge.category == category.strip().lower())
        if difficulty:
            query = query.where(Challenge.difficulty == difficulty.strip().upper())
        query = query.order_by(Challenge.points.asc(), Challenge.slug.asc())
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def list_recent_active(self, limit: int = 5) -> list[Challenge]:
        query = (
            select(Challenge)
            .where(Challenge.is_active.is_(True))
            .order_by(Challenge.created_at.desc())
            .limit(limit)
        )
        result = await self._db.execute(query)
        return list(result.scalars().all())

    async def get_category_summary(self) -> list[tuple[str, int]]:
        query = (
            select(Challenge.category, func.count(Challenge.id).label("total"))
            .where(Challenge.is_active.is_(True))
            .group_by(Challenge.category)
            .order_by(Challenge.category.asc())
        )
        result = await self._db.execute(query)
        return [(category, total) for category, total in result.all()]

    async def get_active_by_id_or_slug(self, challenge_id_or_slug: str) -> Optional[Challenge]:
        query = select(Challenge).where(
            (Challenge.id == challenge_id_or_slug) | (Challenge.slug == challenge_id_or_slug),
            Challenge.is_active.is_(True),
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id(self, challenge_id: str) -> Optional[Challenge]:
        result = await self._db.execute(select(Challenge).where(Challenge.id == challenge_id))
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Optional[Challenge]:
        result = await self._db.execute(select(Challenge).where(Challenge.slug == slug))
        return result.scalar_one_or_none()

    async def list_all(self) -> list[Challenge]:
        result = await self._db.execute(select(Challenge).order_by(Challenge.created_at.desc()))
        return list(result.scalars().all())

    async def count_active(self) -> int:
        result = await self._db.execute(
            select(func.count()).select_from(Challenge).where(Challenge.is_active.is_(True))
        )
        return result.scalar() or 0

    async def get_solved_challenge_ids(self, user_id: str) -> set[str]:
        result = await self._db.execute(select(Solve.challenge_id).where(Solve.user_id == user_id))
        return set(result.scalars().all())

    async def has_user_solved(self, user_id: str, challenge_id: str) -> bool:
        result = await self._db.execute(
            select(Solve.id).where(Solve.user_id == user_id, Solve.challenge_id == challenge_id)
        )
        return result.scalar_one_or_none() is not None

    async def record_incorrect_submission(
        self,
        user_id: str,
        challenge_id: str,
        flag_hash: str,
        now: datetime,
    ) -> None:
        submission = Submission(
            user_id=user_id,
            challenge_id=challenge_id,
            submitted_flag=flag_hash,
            is_correct=False,
            submitted_at=now,
        )
        self._db.add(submission)
        await self._db.commit()

    async def record_correct_solve(
        self,
        user: User,
        challenge: Challenge,
        flag_hash: str,
        now: datetime,
    ) -> tuple[bool, int]:
        submission = Submission(
            user_id=user.id,
            challenge_id=challenge.id,
            submitted_flag=flag_hash,
            is_correct=True,
            submitted_at=now,
        )
        solve = Solve(
            user_id=user.id,
            challenge_id=challenge.id,
            points_awarded=challenge.points,
            solved_at=now,
        )
        self._db.add(submission)
        self._db.add(solve)

        try:
            await self._db.flush()
            await self._db.execute(
                update(Challenge)
                .where(Challenge.id == challenge.id)
                .values(solves_count=Challenge.solves_count + 1)
            )
            await self._db.execute(
                update(User)
                .where(User.id == user.id)
                .values(score=User.score + challenge.points, last_connected_at=now)
            )
            await self._db.commit()
        except IntegrityError:
            await self._db.rollback()
            await self._db.refresh(user)
            return False, user.score

        await self._db.refresh(user)
        await self._db.refresh(challenge)
        return True, user.score

    async def get_running_instance(
        self,
        user_id: str,
        challenge_id: str,
    ) -> Optional[ChallengeInstance]:
        query = select(ChallengeInstance).where(
            ChallengeInstance.user_id == user_id,
            ChallengeInstance.challenge_id == challenge_id,
            ChallengeInstance.status == STATUS_RUNNING,
        )
        result = await self._db.execute(query)
        return result.scalar_one_or_none()

    async def create_instance(
        self,
        user_id: str,
        challenge_id: str,
        now: datetime,
    ) -> ChallengeInstance:
        instance = ChallengeInstance(
            user_id=user_id,
            challenge_id=challenge_id,
            status=STATUS_RUNNING,
            created_at=now,
            started_at=now,
        )
        self._db.add(instance)
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def stop_instance(
        self,
        instance: ChallengeInstance,
        now: datetime,
    ) -> ChallengeInstance:
        instance.status = STATUS_STOPPED
        instance.stopped_at = now
        await self._db.commit()
        await self._db.refresh(instance)
        return instance

    async def create(self, challenge: Challenge) -> Challenge:
        self._db.add(challenge)
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        await self._db.refresh(challenge)
        return challenge

    async def save(self, challenge: Challenge) -> Challenge:
        try:
            await self._db.commit()
        except Exception:
            await self._db.rollback()
            raise
        await self._db.refresh(challenge)
        return challenge

    async def delete(self, challenge: Challenge) -> None:
        await self._db.delete(challenge)
        await self._db.commit()
