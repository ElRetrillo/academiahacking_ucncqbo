from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.challenge import Challenge
from app.models.instance import ChallengeInstance, STATUS_RUNNING, STATUS_STOPPED
from app.models.solve import Solve, Submission
from app.models.user import User
from app.schemas.challenge import (
    ChallengeAdmin,
    ChallengeCreate,
    ChallengeInstanceResponse,
    ChallengePublic,
    ChallengeUpdate,
    FlagSubmissionResponse,
    InstanceChallengeInfo,
)
from app.services.security import REDACTED_FLAG_MARKER, hash_flag, verify_flag


def resolve_target_url(target_url: Optional[str]) -> Optional[str]:
    """Make a relative challenge path absolute using CHALLENGES_BASE_URL."""
    base = settings.CHALLENGES_BASE_URL.strip().rstrip("/")
    if target_url and base and target_url.startswith("/") and not target_url.startswith("//"):
        return f"{base}{target_url}"
    return target_url


def to_public(ch: Challenge, is_solved: bool = False) -> ChallengePublic:
    return ChallengePublic(
        id=ch.id,
        slug=ch.slug,
        title=ch.title,
        description=ch.description,
        category=ch.category,
        difficulty=ch.difficulty,
        points=ch.points,
        target_url=resolve_target_url(ch.target_url),
        hints=ch.hints,
        version=ch.version,
        repository=ch.repository,
        path=ch.path,
        solves_count=ch.solves_count,
        is_solved=is_solved,
    )


def to_admin(ch: Challenge) -> ChallengeAdmin:
    return ChallengeAdmin(
        id=ch.id,
        slug=ch.slug,
        title=ch.title,
        description=ch.description,
        category=ch.category,
        difficulty=ch.difficulty,
        points=ch.points,
        target_url=ch.target_url,
        hints=ch.hints,
        version=ch.version,
        repository=ch.repository,
        path=ch.path,
        flag=REDACTED_FLAG_MARKER,
        flag_configured=bool(ch.flag_hash or (ch.flag and ch.flag != REDACTED_FLAG_MARKER)),
        is_active=ch.is_active,
        solves_count=ch.solves_count,
        created_at=ch.created_at,
    )


class ChallengeService:
    @staticmethod
    async def get_public_challenges(
        db: AsyncSession,
        user: Optional[User] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> List[ChallengePublic]:
        query = select(Challenge).where(Challenge.is_active == True)
        if category:
            query = query.where(Challenge.category == category.lower())
        if difficulty:
            query = query.where(Challenge.difficulty == difficulty.upper())

        query = query.order_by(Challenge.points.asc(), Challenge.slug.asc())
        result = await db.execute(query)
        challenges = result.scalars().all()

        solved_challenge_ids = set()
        if user:
            solves_res = await db.execute(select(Solve.challenge_id).where(Solve.user_id == user.id))
            solved_challenge_ids = set(solves_res.scalars().all())

        return [to_public(ch, is_solved=(ch.id in solved_challenge_ids)) for ch in challenges]

    @staticmethod
    async def get_recent_challenges(
        db: AsyncSession,
        user: Optional[User] = None,
        limit: int = 5,
    ) -> List[ChallengePublic]:
        query = select(Challenge).where(Challenge.is_active == True).order_by(Challenge.created_at.desc()).limit(limit)
        result = await db.execute(query)
        challenges = result.scalars().all()

        solved_challenge_ids = set()
        if user:
            solves_res = await db.execute(select(Solve.challenge_id).where(Solve.user_id == user.id))
            solved_challenge_ids = set(solves_res.scalars().all())

        return [to_public(ch, is_solved=(ch.id in solved_challenge_ids)) for ch in challenges]

    @staticmethod
    async def get_category_summary(db: AsyncSession) -> List[dict]:
        query = (
            select(Challenge.category, func.count(Challenge.id).label("count"))
            .where(Challenge.is_active == True)
            .group_by(Challenge.category)
            .order_by(Challenge.category.asc())
        )
        result = await db.execute(query)
        return [{"category": row.category, "count": row.count} for row in result.all()]

    @staticmethod
    async def get_challenge_by_id_or_slug(
        db: AsyncSession,
        challenge_id_or_slug: str,
        user: Optional[User] = None,
    ) -> ChallengePublic:
        ch = await ChallengeService._get_active_challenge(db, challenge_id_or_slug)

        is_solved = False
        if user:
            solve_res = await db.execute(
                select(Solve).where(Solve.user_id == user.id, Solve.challenge_id == ch.id)
            )
            is_solved = solve_res.scalar_one_or_none() is not None

        return to_public(ch, is_solved=is_solved)

    @staticmethod
    async def submit_flag(
        db: AsyncSession,
        challenge_id_or_slug: str,
        submitted_flag: str,
        user: User,
    ) -> FlagSubmissionResponse:
        challenge = await ChallengeService._get_active_challenge(db, challenge_id_or_slug)

        solve_res = await db.execute(
            select(Solve).where(Solve.user_id == user.id, Solve.challenge_id == challenge.id)
        )
        if solve_res.scalar_one_or_none():
            return FlagSubmissionResponse(
                is_correct=True,
                message="You have already solved this challenge!",
                points_awarded=0,
                new_total_score=user.score,
            )

        is_correct = verify_flag(submitted_flag, challenge.flag, challenge.flag_hash)
        now = datetime.now(timezone.utc)

        submission = Submission(
            user_id=user.id,
            challenge_id=challenge.id,
            submitted_flag=hash_flag(submitted_flag),
            is_correct=is_correct,
            submitted_at=now,
        )
        db.add(submission)

        if not is_correct:
            await db.commit()
            return FlagSubmissionResponse(
                is_correct=False,
                message="Incorrect flag. Keep analyzing!",
                points_awarded=0,
                new_total_score=user.score,
            )

        solve = Solve(
            user_id=user.id,
            challenge_id=challenge.id,
            points_awarded=challenge.points,
            solved_at=now,
        )
        db.add(solve)

        challenge.solves_count += 1
        user.score += challenge.points
        user.last_connected_at = now

        await db.commit()
        await db.refresh(user)

        return FlagSubmissionResponse(
            is_correct=True,
            message=f"Congratulations! Flag accepted (+{challenge.points} pts)",
            points_awarded=challenge.points,
            new_total_score=user.score,
        )

    @staticmethod
    async def _get_active_challenge(db: AsyncSession, challenge_id_or_slug: str) -> Challenge:
        query = select(Challenge).where(
            (Challenge.id == challenge_id_or_slug) | (Challenge.slug == challenge_id_or_slug),
            Challenge.is_active == True,
        )
        result = await db.execute(query)
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Challenge not found or inactive.",
            )
        return ch

    @staticmethod
    def _instance_response(instance: ChallengeInstance, ch: Challenge) -> ChallengeInstanceResponse:
        return ChallengeInstanceResponse(
            id=instance.id,
            status=instance.status,
            created_at=instance.created_at,
            started_at=instance.started_at,
            stopped_at=instance.stopped_at,
            expiration_at=instance.expiration_at,
            challenge=InstanceChallengeInfo(
                id=ch.id,
                slug=ch.slug,
                title=ch.title,
                category=ch.category,
                difficulty=ch.difficulty,
                points=ch.points,
                version=ch.version,
                repository=ch.repository,
                path=ch.path,
                target_url=resolve_target_url(ch.target_url),
            ),
        )

    @staticmethod
    async def start_instance(db: AsyncSession, challenge_id_or_slug: str, user: User) -> ChallengeInstanceResponse:
        ch = await ChallengeService._get_active_challenge(db, challenge_id_or_slug)

        existing_q = select(ChallengeInstance).where(
            ChallengeInstance.user_id == user.id,
            ChallengeInstance.challenge_id == ch.id,
            ChallengeInstance.status == STATUS_RUNNING,
        )
        existing = (await db.execute(existing_q)).scalar_one_or_none()
        if existing:
            return ChallengeService._instance_response(existing, ch)

        now = datetime.now(timezone.utc)
        instance = ChallengeInstance(
            user_id=user.id,
            challenge_id=ch.id,
            status=STATUS_RUNNING,
            created_at=now,
            started_at=now,
        )
        db.add(instance)
        await db.commit()
        await db.refresh(instance)
        return ChallengeService._instance_response(instance, ch)

    @staticmethod
    async def stop_instance(db: AsyncSession, challenge_id_or_slug: str, user: User) -> ChallengeInstanceResponse:
        ch = await ChallengeService._get_active_challenge(db, challenge_id_or_slug)

        instance_q = select(ChallengeInstance).where(
            ChallengeInstance.user_id == user.id,
            ChallengeInstance.challenge_id == ch.id,
            ChallengeInstance.status == STATUS_RUNNING,
        )
        instance = (await db.execute(instance_q)).scalar_one_or_none()
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No running instance for this challenge.",
            )

        instance.status = STATUS_STOPPED
        instance.stopped_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(instance)
        return ChallengeService._instance_response(instance, ch)

    @staticmethod
    async def admin_get_all_challenges(db: AsyncSession) -> List[ChallengeAdmin]:
        result = await db.execute(select(Challenge).order_by(Challenge.created_at.desc()))
        return [to_admin(ch) for ch in result.scalars().all()]

    @staticmethod
    async def admin_create_challenge(db: AsyncSession, req: ChallengeCreate) -> ChallengeAdmin:
        result = await db.execute(select(Challenge).where(Challenge.slug == req.slug))
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug '{req.slug}' is already in use.",
            )

        clean_flag = req.flag.strip()
        ch = Challenge(
            slug=req.slug,
            title=req.title,
            description=req.description,
            category=req.category,
            difficulty=req.difficulty.upper(),
            points=req.points,
            flag=REDACTED_FLAG_MARKER,
            flag_hash=hash_flag(clean_flag),
            target_url=req.target_url,
            hints=req.hints,
            version=req.version,
            repository=req.repository,
            path=req.path,
            is_active=True,
            solves_count=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ch)
        await db.commit()
        await db.refresh(ch)
        return to_admin(ch)

    @staticmethod
    async def admin_update_challenge(
        db: AsyncSession,
        challenge_id: str,
        req: ChallengeUpdate,
    ) -> ChallengeAdmin:
        result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

        if req.title is not None:
            ch.title = req.title
        if req.description is not None:
            ch.description = req.description
        if req.category is not None:
            ch.category = req.category
        if req.difficulty is not None:
            ch.difficulty = req.difficulty.upper()
        if req.points is not None:
            ch.points = req.points
        if req.target_url is not None:
            ch.target_url = req.target_url
        if req.hints is not None:
            ch.hints = req.hints
        if req.version is not None:
            ch.version = req.version
        if req.repository is not None:
            ch.repository = req.repository
        if req.path is not None:
            ch.path = req.path
        if req.flag is not None:
            ch.flag = REDACTED_FLAG_MARKER
            ch.flag_hash = hash_flag(req.flag.strip())
        if req.is_active is not None:
            ch.is_active = req.is_active

        await db.commit()
        await db.refresh(ch)
        return to_admin(ch)

    @staticmethod
    async def admin_delete_challenge(db: AsyncSession, challenge_id: str) -> None:
        result = await db.execute(select(Challenge).where(Challenge.id == challenge_id))
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

        await db.delete(ch)
        await db.commit()
