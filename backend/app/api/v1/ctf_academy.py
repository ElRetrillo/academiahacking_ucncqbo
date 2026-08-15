"""
Adapter endpoint: POST /api/ctf-academy

Implements the action-based contract consumed by the EclipSec frontend.

Request:  { action: str, username?, password?, challengeId?, flag? }
Response: { ok: bool, message: str, token?: str, data?: CtfAcademyData }
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.challenge import Challenge
from app.models.solve import Solve
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.services.challenge_service import ChallengeService
from app.services.security import decode_token, create_access_token

router = APIRouter(tags=["CTF Academy"])


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic request model
# ─────────────────────────────────────────────────────────────────────────────

class CtfAcademyRequest(BaseModel):
    action: str = Field(..., description="Action: login | register | logout | state | complete")
    username: Optional[str] = None
    password: Optional[str] = None
    challengeId: Optional[str] = None
    flag: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Response helpers
# ─────────────────────────────────────────────────────────────────────────────

def ok_resp(message: str, token: Optional[str] = None, data: Optional[Any] = None) -> dict:
    payload: dict = {"ok": True, "message": message}
    if token is not None:
        payload["token"] = token
    if data is not None:
        payload["data"] = data
    return payload


def err_resp(message: str) -> dict:
    return {"ok": False, "message": message}


def r(status_code: int, body: dict) -> JSONResponse:
    """Shorthand to avoid arg-order mistakes with JSONResponse."""
    return JSONResponse(status_code=status_code, content=body)


# ─────────────────────────────────────────────────────────────────────────────
# Academy state builder
# ─────────────────────────────────────────────────────────────────────────────

async def build_academy_state(db: AsyncSession, user: Optional[User]) -> dict:
    """Build the CtfAcademyData envelope the EclipSec frontend expects."""

    # Leaderboard: top 50 active players, score desc then join date asc
    lb_result = await db.execute(
        select(User.username, User.score, User.created_at)
        .where(User.is_active.is_(True), User.role == "user")
        .order_by(User.score.desc(), User.created_at.asc())
        .limit(50)
    )
    leaderboard = [
        {
            "username": row.username,
            "score": row.score,
            "durationMs": 0,
            "completedAt": int(row.created_at.timestamp() * 1000),
        }
        for row in lb_result.all()
    ]

    # Participant count
    count_res = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.is_active.is_(True), User.role == "user")
    )
    participants: int = count_res.scalar() or 0

    current_user_data = None
    session_data = None

    if user:
        solves_res = await db.execute(
            select(Solve.challenge_id, Solve.solved_at)
            .where(Solve.user_id == user.id)
            .order_by(Solve.solved_at.asc())
        )
        solves = solves_res.all()
        completed_ids = [str(s.challenge_id) for s in solves]
        completion_times = {str(s.challenge_id): int(s.solved_at.timestamp() * 1000) for s in solves}

        total_res = await db.execute(
            select(func.count()).select_from(Challenge).where(Challenge.is_active.is_(True))
        )
        total_challenges: int = total_res.scalar() or 0
        completed_at_ts = None
        if total_challenges > 0 and len(completed_ids) >= total_challenges and solves:
            completed_at_ts = int(solves[-1].solved_at.timestamp() * 1000)

        current_user_data = {
            "username": user.username,
            "createdAt": int(user.created_at.timestamp() * 1000),
            "startedAt": int(user.created_at.timestamp() * 1000),
            "completedChallengeIds": completed_ids,
            "completionTimes": completion_times,
            **({"completedAt": completed_at_ts} if completed_at_ts else {}),
        }
        session_data = {
            "username": user.username,
            "role": "admin" if user.role == "admin" else "player",
        }

    return {
        "session": session_data,
        "currentUser": current_user_data,
        "leaderboard": leaderboard,
        "participants": participants,
    }


def extract_bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    return auth[7:] if auth.startswith("Bearer ") else None


async def get_user_from_token(token: str, db: AsyncSession) -> Optional[User]:
    user_id = decode_token(token)
    if not user_id:
        return None
    result = await db.execute(
        select(User).where(User.id == user_id, User.is_active.is_(True))
    )
    user = result.scalar_one_or_none()
    if user:
        user.last_connected_at = datetime.now(timezone.utc)
        await db.commit()
    return user


# ─────────────────────────────────────────────────────────────────────────────
# Main handler
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/api/ctf-academy")
async def ctf_academy_handler(
    body: CtfAcademyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    action = body.action.strip().lower()
    token = extract_bearer_token(request)

    # ── register ──────────────────────────────────────────────────────────────
    if action == "register":
        username = (body.username or "").strip()
        password = body.password or ""

        if len(username) < 3:
            return r(400, err_resp("El usuario debe tener al menos 3 caracteres."))
        if len(password) < 4:
            return r(400, err_resp("La contraseña debe tener al menos 4 caracteres."))

        req = RegisterRequest(
            username=username,
            email=f"{username}@ctf.eclipsec.cl",
            password=password,
            nationality="CL",
        )
        try:
            user = await AuthService.register_user(db, req)
        except Exception as exc:
            msg = str(exc).lower()
            if any(k in msg for k in ("already", "exist", "registered")):
                return r(409, err_resp("Ese usuario ya existe."))
            return r(500, err_resp("Error interno al registrar."))

        new_token = create_access_token(subject=user.id)
        data = await build_academy_state(db, user)
        return r(200, ok_resp("Usuario creado. ¡Bienvenido a la Academia!", token=new_token, data=data))

    # ── login ─────────────────────────────────────────────────────────────────
    if action == "login":
        username = (body.username or "").strip()
        password = body.password or ""

        if not username or not password:
            return r(400, err_resp("Usuario y contraseña son requeridos."))

        try:
            token_resp = await AuthService.authenticate_user(
                db, LoginRequest(username_or_email=username, password=password)
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "deactivated" in msg or "403" in msg:
                return r(403, err_resp("Tu cuenta está suspendida."))
            return r(401, err_resp("Usuario o contraseña incorrectos."))

        user_id = decode_token(token_resp.access_token)
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        data = await build_academy_state(db, user)
        return r(200, ok_resp("Sesión iniciada.", token=token_resp.access_token, data=data))

    # ── logout ────────────────────────────────────────────────────────────────
    if action == "logout":
        return r(200, ok_resp("Sesión cerrada."))

    # ── state ─────────────────────────────────────────────────────────────────
    if action == "state":
        user = await get_user_from_token(token, db) if token else None
        data = await build_academy_state(db, user)
        return r(200, ok_resp("Estado cargado.", data=data))

    # ── complete (flag submission) ────────────────────────────────────────────
    if action == "complete":
        if not token:
            return r(403, err_resp("Debes iniciar sesión."))

        user = await get_user_from_token(token, db)
        if not user:
            return r(403, err_resp("Sesión inválida."))

        challenge_id = (body.challengeId or "").strip()
        submitted_flag = (body.flag or "").strip()

        if not challenge_id or not submitted_flag:
            return r(400, err_resp("challengeId y flag son requeridos."))

        try:
            result = await ChallengeService.submit_flag(
                db=db,
                challenge_id_or_slug=challenge_id,
                submitted_flag=submitted_flag,
                user=user,
            )
        except Exception as exc:
            msg = str(exc).lower()
            if "404" in msg or "not found" in msg:
                return r(404, err_resp("Reto no encontrado."))
            return r(400, err_resp(str(exc)))

        if not result.is_correct:
            return r(401, err_resp("Flag incorrecta."))

        data = await build_academy_state(db, user)
        return r(200, ok_resp(result.message, data=data))

    # ── unknown action ────────────────────────────────────────────────────────
    return r(400, err_resp(f"Acción desconocida: '{action}'."))
