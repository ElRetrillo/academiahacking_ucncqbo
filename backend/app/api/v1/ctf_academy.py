from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    clear_session_cookies,
    extract_token_from_request,
    is_token_revoked,
    revoke_token,
    set_session_cookies,
    touch_last_connected,
    verify_csrf_if_cookie,
)
from app.config import settings
from app.database import get_db
from app.models.challenge import Challenge
from app.models.solve import Solve
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services.auth_service import AuthService
from app.services.challenge_service import ChallengeService
from app.services.rate_limiter import enforce_rate_limit, get_client_ip
from app.services.security import create_access_token, decode_token_payload
from app.services.user_service import UserService

router = APIRouter(tags=["CTF Academy"])


class CtfAcademyRequest(BaseModel):
    action: str = Field(..., description="Action: login | register | logout | state | complete")
    username: Optional[str] = None
    password: Optional[str] = None
    challengeId: Optional[str] = None
    flag: Optional[str] = None


def ok_resp(message: str, data: Optional[Any] = None) -> dict:
    payload: dict = {"ok": True, "message": message}
    if data is not None:
        payload["data"] = data
    return payload


def err_resp(message: str) -> dict:
    return {"ok": False, "message": message}


def json_response(status_code: int, body: dict) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=body)


async def build_academy_state(db: AsyncSession, user: Optional[User]) -> dict:
    """Build the CtfAcademyData envelope expected by the frontend."""
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

        global_rank: Any = "Sin clasificar"
        if user.role == "user" and user.score > 0 and len(completed_ids) > 0:
            active_solvers_subquery = select(Solve.user_id).group_by(Solve.user_id).subquery()
            rank_query = (
                select(User.id)
                .join(active_solvers_subquery, User.id == active_solvers_subquery.c.user_id)
                .where(User.is_active.is_(True), User.role == "user", User.score > 0)
                .order_by(desc(User.score), User.created_at.asc())
            )
            rank_res = await db.execute(rank_query)
            ranked_user_ids = [row[0] for row in rank_res.all()]
            if user.id in ranked_user_ids:
                global_rank = ranked_user_ids.index(user.id) + 1

        rank_name = UserService.get_rank_name(user.score)
        created_ms = int(user.created_at.timestamp() * 1000)

        current_user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "nationality": user.nationality,
            "score": user.score,
            "rankName": rank_name,
            "rank_name": rank_name,
            "globalRank": global_rank,
            "global_rank": global_rank,
            "createdAt": created_ms,
            "created_at": created_ms,
            "startedAt": created_ms,
            "completedChallengeIds": completed_ids,
            "completionTimes": completion_times,
            "solvesCount": len(completed_ids),
            "solves_count": len(completed_ids),
            **({"completedAt": completed_at_ts} if completed_at_ts else {}),
        }
        session_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "nationality": user.nationality,
            "score": user.score,
            "isLoggedIn": True,
            "is_logged_in": True,
            "user": current_user_data,
        }

    return {
        "session": session_data,
        "currentUser": current_user_data,
        "leaderboard": leaderboard,
        "participants": participants,
    }


async def get_authenticated_academy_user(
    request: Request,
    db: AsyncSession,
    require_csrf: bool = False,
) -> tuple[Optional[User], Optional[str], Optional[JSONResponse]]:
    token, is_cookie_auth = extract_token_from_request(request)
    if not token:
        return None, None, None

    if require_csrf and is_cookie_auth:
        try:
            verify_csrf_if_cookie(request, True)
        except HTTPException:
            return None, token, json_response(status.HTTP_403_FORBIDDEN, err_resp("Validacion CSRF fallida."))

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(db, payload.get("jti")):
        return None, token, None

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id, User.is_active.is_(True)))
    user = result.scalar_one_or_none()
    if user:
        await touch_last_connected(db, user)
    return user, token, None


@router.post("/api/ctf-academy")
async def ctf_academy_handler(
    body: CtfAcademyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    action = body.action.strip().lower()
    client_ip = get_client_ip(request)

    if action == "register":
        enforce_rate_limit(
            "ctf_academy_auth",
            client_ip,
            settings.RATE_LIMIT_AUTH_MAX,
            settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
        )
        username = (body.username or "").strip()
        password = body.password or ""

        if len(username) < 3:
            return json_response(400, err_resp("El usuario debe tener al menos 3 caracteres."))
        if len(password) < 6:
            return json_response(400, err_resp("La contrasena debe tener al menos 6 caracteres."))

        try:
            req = RegisterRequest(
                username=username,
                email=f"{username}@ctf.eclipsec.cl",
                password=password,
                nationality="CL",
            )
            user = await AuthService.register_user(db, req)
        except ValidationError:
            return json_response(400, err_resp("Formato de usuario o contrasena invalido."))
        except HTTPException as exc:
            detail = str(exc.detail).lower()
            if any(k in detail for k in ("already", "exist", "registered")):
                return json_response(409, err_resp("Ese usuario ya existe."))
            return json_response(exc.status_code, err_resp("No se pudo registrar el usuario."))

        new_token = create_access_token(subject=user.id, token_type="web")
        data = await build_academy_state(db, user)
        resp = json_response(200, ok_resp("Usuario creado. Bienvenido a la Academia.", data=data))
        set_session_cookies(resp, new_token)
        return resp

    if action == "login":
        enforce_rate_limit(
            "ctf_academy_auth",
            client_ip,
            settings.RATE_LIMIT_AUTH_MAX,
            settings.RATE_LIMIT_AUTH_WINDOW_SECONDS,
        )
        username = (body.username or "").strip()
        password = body.password or ""

        if not username or not password:
            return json_response(400, err_resp("Usuario y contrasena son requeridos."))

        try:
            token_resp = await AuthService.authenticate_user(
                db,
                LoginRequest(username_or_email=username, password=password),
                token_type="web",
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_403_FORBIDDEN:
                return json_response(403, err_resp("Tu cuenta esta suspendida."))
            return json_response(401, err_resp("Usuario o contrasena incorrectos."))

        payload = decode_token_payload(token_resp.access_token)
        user_id = payload.get("sub") if payload else None
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        data = await build_academy_state(db, user)
        resp = json_response(200, ok_resp("Sesion iniciada.", data=data))
        set_session_cookies(resp, token_resp.access_token)
        return resp

    if action == "logout":
        token, is_cookie_auth = extract_token_from_request(request)
        if is_cookie_auth:
            try:
                verify_csrf_if_cookie(request, True)
            except HTTPException:
                return json_response(status.HTTP_403_FORBIDDEN, err_resp("Validacion CSRF fallida."))
        if token:
            await revoke_token(db, token)
        resp = json_response(200, ok_resp("Sesion cerrada."))
        clear_session_cookies(resp)
        return resp

    if action == "state":
        user, _, _ = await get_authenticated_academy_user(request, db, require_csrf=False)
        data = await build_academy_state(db, user)
        return json_response(200, ok_resp("Estado cargado.", data=data))

    if action == "complete":
        enforce_rate_limit(
            "ctf_academy_flag",
            client_ip,
            settings.RATE_LIMIT_FLAG_MAX,
            settings.RATE_LIMIT_FLAG_WINDOW_SECONDS,
        )
        user, token, err_response = await get_authenticated_academy_user(request, db, require_csrf=True)
        if err_response is not None:
            return err_response
        if not token:
            return json_response(403, err_resp("Debes iniciar sesion."))
        if not user:
            return json_response(403, err_resp("Sesion invalida."))

        challenge_id = (body.challengeId or "").strip()
        submitted_flag = (body.flag or "").strip()

        if not challenge_id or not submitted_flag:
            return json_response(400, err_resp("challengeId y flag son requeridos."))

        try:
            result = await ChallengeService.submit_flag(
                db=db,
                challenge_id_or_slug=challenge_id,
                submitted_flag=submitted_flag,
                user=user,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                return json_response(404, err_resp("Reto no encontrado."))
            return json_response(400, err_resp("No se pudo validar el reto."))

        if not result.is_correct:
            return json_response(401, err_resp("Flag incorrecta."))

        data = await build_academy_state(db, user)
        return json_response(200, ok_resp(result.message, data=data))

    return json_response(400, err_resp("Accion desconocida."))
