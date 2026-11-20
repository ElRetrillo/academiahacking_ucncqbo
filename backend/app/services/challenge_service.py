from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.models.challenge import Challenge
from app.models.instance import ChallengeInstance
from app.models.user import User
from app.repositories.protocols import ChallengeRepositoryProtocol
from app.schemas.challenge import (
    ChallengeAdmin,
    ChallengeCreate,
    ChallengeInstanceResponse,
    ChallengePublic,
    ChallengeUpdate,
    FlagSubmissionResponse,
    InstanceChallengeInfo,
)
from app.services.security import REDACTED_FLAG_MARKER, FlagVerifier, hash_flag


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
    def __init__(
        self,
        challenge_repo: ChallengeRepositoryProtocol,
        flag_verifier: FlagVerifier,
    ) -> None:
        self._challenge_repo = challenge_repo
        self._flag_verifier = flag_verifier

    async def get_public_challenges(
        self,
        user: Optional[User] = None,
        category: Optional[str] = None,
        difficulty: Optional[str] = None,
    ) -> list[ChallengePublic]:
        challenges = await self._challenge_repo.list_active(category=category, difficulty=difficulty)
        solved_ids = (
            await self._challenge_repo.get_solved_challenge_ids(user.id) if user else set()
        )
        return [to_public(ch, is_solved=(ch.id in solved_ids)) for ch in challenges]

    async def get_recent_challenges(
        self,
        user: Optional[User] = None,
        limit: int = 5,
    ) -> list[ChallengePublic]:
        challenges = await self._challenge_repo.list_recent_active(limit=limit)
        solved_ids = (
            await self._challenge_repo.get_solved_challenge_ids(user.id) if user else set()
        )
        return [to_public(ch, is_solved=(ch.id in solved_ids)) for ch in challenges]

    async def get_category_summary(self) -> list[dict]:
        rows = await self._challenge_repo.get_category_summary()
        return [{"category": category, "count": count} for category, count in rows]

    async def get_challenge_by_id_or_slug(
        self,
        challenge_id_or_slug: str,
        user: Optional[User] = None,
    ) -> ChallengePublic:
        ch = await self._get_active_challenge(challenge_id_or_slug)
        is_solved = (
            await self._challenge_repo.has_user_solved(user.id, ch.id) if user else False
        )
        return to_public(ch, is_solved=is_solved)

    async def submit_flag(
        self,
        challenge_id_or_slug: str,
        submitted_flag: str,
        user: User,
    ) -> FlagSubmissionResponse:
        challenge = await self._get_active_challenge(challenge_id_or_slug)

        if await self._challenge_repo.has_user_solved(user.id, challenge.id):
            return FlagSubmissionResponse(
                is_correct=True,
                message="You have already solved this challenge!",
                points_awarded=0,
                new_total_score=user.score,
            )

        is_correct = self._flag_verifier.verify(submitted_flag, challenge.flag, challenge.flag_hash)
        now = datetime.now(timezone.utc)
        flag_digest = hash_flag(submitted_flag)

        if not is_correct:
            await self._challenge_repo.record_incorrect_submission(
                user.id, challenge.id, flag_digest, now
            )
            return FlagSubmissionResponse(
                is_correct=False,
                message="Incorrect flag. Keep analyzing!",
                points_awarded=0,
                new_total_score=user.score,
            )

        awarded, new_total_score = await self._challenge_repo.record_correct_solve(
            user=user,
            challenge=challenge,
            flag_hash=flag_digest,
            now=now,
        )
        if not awarded:
            return FlagSubmissionResponse(
                is_correct=True,
                message="You have already solved this challenge!",
                points_awarded=0,
                new_total_score=new_total_score,
            )

        return FlagSubmissionResponse(
            is_correct=True,
            message=f"Congratulations! Flag accepted (+{challenge.points} pts)",
            points_awarded=challenge.points,
            new_total_score=new_total_score,
        )

    async def _get_active_challenge(self, challenge_id_or_slug: str) -> Challenge:
        ch = await self._challenge_repo.get_active_by_id_or_slug(challenge_id_or_slug)
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

    async def start_instance(
        self,
        challenge_id_or_slug: str,
        user: User,
    ) -> ChallengeInstanceResponse:
        ch = await self._get_active_challenge(challenge_id_or_slug)
        existing = await self._challenge_repo.get_running_instance(user.id, ch.id)
        if existing:
            return self._instance_response(existing, ch)

        instance = await self._challenge_repo.create_instance(
            user.id, ch.id, datetime.now(timezone.utc)
        )
        return self._instance_response(instance, ch)

    async def stop_instance(
        self,
        challenge_id_or_slug: str,
        user: User,
    ) -> ChallengeInstanceResponse:
        ch = await self._get_active_challenge(challenge_id_or_slug)
        instance = await self._challenge_repo.get_running_instance(user.id, ch.id)
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No running instance for this challenge.",
            )

        stopped = await self._challenge_repo.stop_instance(instance, datetime.now(timezone.utc))
        return self._instance_response(stopped, ch)

    async def admin_get_all_challenges(self) -> list[ChallengeAdmin]:
        challenges = await self._challenge_repo.list_all()
        return [to_admin(ch) for ch in challenges]

    async def admin_create_challenge(self, req: ChallengeCreate) -> ChallengeAdmin:
        if await self._challenge_repo.get_by_slug(req.slug):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug '{req.slug}' is already in use.",
            )

        ch = Challenge(
            slug=req.slug,
            title=req.title,
            description=req.description,
            category=req.category,
            difficulty=req.difficulty,
            points=req.points,
            flag=REDACTED_FLAG_MARKER,
            flag_hash=hash_flag(req.flag),
            target_url=req.target_url,
            hints=req.hints,
            version=req.version,
            repository=req.repository,
            path=req.path,
            is_active=True,
            solves_count=0,
            created_at=datetime.now(timezone.utc),
        )
        try:
            created = await self._challenge_repo.create(ch)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Slug '{req.slug}' is already in use.",
            ) from exc
        return to_admin(created)

    async def admin_update_challenge(
        self,
        challenge_id: str,
        req: ChallengeUpdate,
    ) -> ChallengeAdmin:
        ch = await self._challenge_repo.get_by_id(challenge_id)
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")

        if req.title is not None:
            ch.title = req.title
        if req.description is not None:
            ch.description = req.description
        if req.category is not None:
            ch.category = req.category
        if req.difficulty is not None:
            ch.difficulty = req.difficulty
        if req.points is not None:
            ch.points = req.points
        if "target_url" in req.model_fields_set:
            ch.target_url = req.target_url
        if "hints" in req.model_fields_set:
            ch.hints = req.hints
        if req.version is not None:
            ch.version = req.version
        if "repository" in req.model_fields_set:
            ch.repository = req.repository
        if "path" in req.model_fields_set:
            ch.path = req.path
        if req.flag is not None:
            ch.flag = REDACTED_FLAG_MARKER
            ch.flag_hash = hash_flag(req.flag)
        if req.is_active is not None:
            ch.is_active = req.is_active

        updated = await self._challenge_repo.save(ch)
        return to_admin(updated)

    async def admin_delete_challenge(self, challenge_id: str) -> None:
        ch = await self._challenge_repo.get_by_id(challenge_id)
        if not ch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Challenge not found.")
        await self._challenge_repo.delete(ch)
