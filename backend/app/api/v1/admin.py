from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.database import get_db
from app.models.user import User
from app.models.challenge import Challenge
from app.models.solve import Solve
from app.schemas.challenge import ChallengeAdmin, ChallengeCreate, ChallengeUpdate
from app.schemas.user import UserProfile, UserAdminUpdate
from app.services.challenge_service import ChallengeService
from app.api.deps import get_current_admin

router = APIRouter(prefix="/admin", tags=["Admin Panel"])


# ──────────────────────────────────────────────────────────────
# Challenge Management
# ──────────────────────────────────────────────────────────────

@router.get("/challenges", response_model=List[ChallengeAdmin])
async def admin_list_challenges(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all challenges with flags, solutions, and internal metadata."""
    return await ChallengeService.admin_get_all_challenges(db)


@router.post("/challenges", response_model=ChallengeAdmin, status_code=status.HTTP_201_CREATED)
async def admin_create_challenge(
    req: ChallengeCreate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new CTF challenge with difficulty, points, and flag."""
    return await ChallengeService.admin_create_challenge(db, req)


@router.put("/challenges/{challenge_id}", response_model=ChallengeAdmin)
async def admin_update_challenge(
    challenge_id: str,
    req: ChallengeUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update challenge details, points, difficulty, or flag."""
    return await ChallengeService.admin_update_challenge(db, challenge_id, req)


@router.delete("/challenges/{challenge_id}", status_code=status.HTTP_204_NO_CONTENT)
async def admin_delete_challenge(
    challenge_id: str,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a challenge."""
    await ChallengeService.admin_delete_challenge(db, challenge_id)


# ──────────────────────────────────────────────────────────────
# User Management
# ──────────────────────────────────────────────────────────────

@router.get("/users", response_model=List[UserProfile])
async def admin_list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all registered users, roles, points, nationality, start dates, and last connected times."""
    query = select(User).order_by(desc(User.created_at))
    result = await db.execute(query)
    users = result.scalars().all()

    solves_query = (
        select(Solve.user_id, func.count(Solve.id).label("cnt"))
        .group_by(Solve.user_id)
    )
    solves_res = await db.execute(solves_query)
    solves_map = {row.user_id: row.cnt for row in solves_res.all()}

    return [
        UserProfile(
            id=u.id,
            username=u.username,
            email=u.email,
            nationality=u.nationality,
            role=u.role,
            score=u.score,
            created_at=u.created_at,
            last_connected_at=u.last_connected_at,
            is_active=u.is_active,
            solves_count=solves_map.get(u.id, 0),
        )
        for u in users
    ]


@router.put("/users/{user_id}", response_model=UserProfile)
async def admin_update_user(
    user_id: str,
    req: UserAdminUpdate,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update user role, activation status, nationality, or score."""
    query = select(User).where(User.id == user_id)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    if req.role is not None:
        user.role = req.role
    if req.is_active is not None:
        user.is_active = req.is_active
    if req.nationality is not None:
        user.nationality = req.nationality.upper()
    if req.score is not None:
        user.score = req.score

    await db.commit()
    await db.refresh(user)

    solves_query = select(func.count()).select_from(Solve).where(Solve.user_id == user.id)
    solves_res = await db.execute(solves_query)
    solves_count = solves_res.scalar() or 0

    return UserProfile(
        id=user.id,
        username=user.username,
        email=user.email,
        nationality=user.nationality,
        role=user.role,
        score=user.score,
        created_at=user.created_at,
        last_connected_at=user.last_connected_at,
        is_active=user.is_active,
        solves_count=solves_count,
    )
