from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete
from fastapi import HTTPException, status

from app.models.challenge import Challenge
from app.models.solve import Solve, Submission
from app.models.user import User
from app.schemas.challenge import (
    ChallengeCreate,
    ChallengeUpdate,
    ChallengePublic,
    ChallengeAdmin,
    FlagSubmissionResponse,
)
from app.services.security import verify_flag, hash_flag


class ChallengeService:
    @staticmethod
    async def get_public_challenges(db: AsyncSession, user: Optional[User] = None) -> List[ChallengePublic]:
        query = select(Challenge).where(Challenge.is_active == True).order_by(Challenge.points.asc(), Challenge.slug.asc())
        result = await db.execute(query)
        challenges = result.scalars().all()

        solved_challenge_ids = set()
        if user:
            solves_query = select(Solve.challenge_id).where(Solve.user_id == user.id)
            solves_result = await db.execute(solves_query)
            solved_challenge_ids = set(solves_result.scalars().all())

        public_list = []
        for ch in challenges:
            public_list.append(
                ChallengePublic(
                    id=ch.id,
                    slug=ch.slug,
                    title=ch.title,
                    description=ch.description,
                    category=ch.category,
                    difficulty=ch.difficulty,
                    points=ch.points,
                    target_url=ch.target_url,
                    hints=ch.hints,
                    solves_count=ch.solves_count,
                    is_solved=(ch.id in solved_challenge_ids),
                )
            )
        return public_list

    @staticmethod
    async def get_challenge_by_id_or_slug(db: AsyncSession, challenge_id_or_slug: str, user: Optional[User] = None) -> ChallengePublic:
        query = select(Challenge).where(
            (Challenge.id == challenge_id_or_slug) | (Challenge.slug == challenge_id_or_slug),
            Challenge.is_active == True,
        )
        result = await db.execute(query)
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

        is_solved = False
        if user:
            solve_query = select(Solve).where(Solve.user_id == user.id, Solve.challenge_id == ch.id)
            solve_res = await db.execute(solve_query)
            is_solved = solve_res.scalar_one_or_none() is not None

        return ChallengePublic(
            id=ch.id,
            slug=ch.slug,
            title=ch.title,
            description=ch.description,
            category=ch.category,
            difficulty=ch.difficulty,
            points=ch.points,
            target_url=ch.target_url,
            hints=ch.hints,
            solves_count=ch.solves_count,
            is_solved=is_solved,
        )

    @staticmethod
    async def submit_flag(db: AsyncSession, challenge_id_or_slug: str, submitted_flag: str, user: User) -> FlagSubmissionResponse:
        # 1. Fetch challenge
        query = select(Challenge).where(
            (Challenge.id == challenge_id_or_slug) | (Challenge.slug == challenge_id_or_slug),
            Challenge.is_active == True,
        )
        result = await db.execute(query)
        challenge = result.scalar_one_or_none()
        if not challenge:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found or inactive.")

        # 2. Check if user already solved it
        solve_query = select(Solve).where(Solve.user_id == user.id, Solve.challenge_id == challenge.id)
        solve_res = await db.execute(solve_query)
        existing_solve = solve_res.scalar_one_or_none()
        if existing_solve:
            return FlagSubmissionResponse(
                is_correct=True,
                message="You have already solved this challenge!",
                points_awarded=0,
                new_total_score=user.score,
            )

        # 3. Verify flag using constant-time check
        is_correct = verify_flag(submitted_flag, challenge.flag, challenge.flag_hash)

        # 4. Record submission
        submission = Submission(
            user_id=user.id,
            challenge_id=challenge.id,
            submitted_flag=submitted_flag.strip(),
            is_correct=is_correct,
            submitted_at=datetime.now(timezone.utc),
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

        # 5. Correct flag -> Record Solve & award points
        solve = Solve(
            user_id=user.id,
            challenge_id=challenge.id,
            points_awarded=challenge.points,
            solved_at=datetime.now(timezone.utc),
        )
        db.add(solve)

        challenge.solves_count += 1
        user.score += challenge.points
        user.last_connected_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)

        return FlagSubmissionResponse(
            is_correct=True,
            message=f"Congratulations! Flag accepted (+{challenge.points} pts)",
            points_awarded=challenge.points,
            new_total_score=user.score,
        )

    # ──────────────────────────────────────────────────────────────
    # Admin methods
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    async def admin_get_all_challenges(db: AsyncSession) -> List[ChallengeAdmin]:
        query = select(Challenge).order_by(Challenge.created_at.desc())
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def admin_create_challenge(db: AsyncSession, req: ChallengeCreate) -> ChallengeAdmin:
        # Check slug uniqueness
        query = select(Challenge).where(Challenge.slug == req.slug)
        result = await db.execute(query)
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Slug '{req.slug}' is already in use.")

        ch = Challenge(
            slug=req.slug,
            title=req.title,
            description=req.description,
            category=req.category,
            difficulty=req.difficulty.upper(),
            points=req.points,
            flag=req.flag.strip(),
            flag_hash=hash_flag(req.flag.strip()),
            target_url=req.target_url,
            hints=req.hints,
            is_active=True,
            solves_count=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ch)
        await db.commit()
        await db.refresh(ch)
        return ch

    @staticmethod
    async def admin_update_challenge(db: AsyncSession, challenge_id: str, req: ChallengeUpdate) -> ChallengeAdmin:
        query = select(Challenge).where(Challenge.id == challenge_id)
        result = await db.execute(query)
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
        if req.flag is not None:
            ch.flag = req.flag.strip()
            ch.flag_hash = hash_flag(req.flag.strip())
        if req.is_active is not None:
            ch.is_active = req.is_active

        await db.commit()
        await db.refresh(ch)
        return ch

    @staticmethod
    async def admin_delete_challenge(db: AsyncSession, challenge_id: str) -> None:
        query = select(Challenge).where(Challenge.id == challenge_id)
        result = await db.execute(query)
        ch = result.scalar_one_or_none()
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

        await db.delete(ch)
        await db.commit()
