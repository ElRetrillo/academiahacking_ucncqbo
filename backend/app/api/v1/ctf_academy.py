from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.deps import (
    clear_session_cookies,
    extract_token_from_request,
    get_ctf_academy_service,
    get_token_repository,
    get_user_repository,
    is_token_revoked,
    revoke_token,
    set_session_cookies,
    touch_last_connected,
    verify_csrf_if_cookie,
)
from app.config import settings
from app.models.user import User
from app.repositories.protocols import TokenRevocationRepositoryProtocol, UserRepositoryProtocol
from app.services.ctf_academy_service import CtfAcademyService
from app.services.rate_limiter import enforce_rate_limit, get_client_ip
from app.services.security import decode_token_payload

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


async def get_authenticated_academy_user(
    request: Request,
    user_repo: UserRepositoryProtocol,
    token_repo: TokenRevocationRepositoryProtocol,
    require_csrf: bool = False,
) -> tuple[Optional[User], Optional[str], Optional[JSONResponse]]:
    token, is_cookie_auth = extract_token_from_request(request)
    if not token:
        return None, None, None

    payload = decode_token_payload(token)
    if not payload or await is_token_revoked(token_repo, payload.get("jti")):
        return None, token, None

    if require_csrf and is_cookie_auth:
        try:
            verify_csrf_if_cookie(request, True)
        except HTTPException:
            return None, token, json_response(
                status.HTTP_403_FORBIDDEN,
                err_resp("Validacion CSRF fallida."),
            )

    user_id = payload.get("sub")
    user = await user_repo.get_by_id(str(user_id), active_only=True) if user_id else None
    if user:
        await touch_last_connected(user_repo, user)
    return user, token, None


@router.post("/api/ctf-academy")
async def ctf_academy_handler(
    body: CtfAcademyRequest,
    request: Request,
    academy_service: CtfAcademyService = Depends(get_ctf_academy_service),
    user_repo: UserRepositoryProtocol = Depends(get_user_repository),
    token_repo: TokenRevocationRepositoryProtocol = Depends(get_token_repository),
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
        try:
            user, new_token = await academy_service.register_academy_user(
                username=body.username or "",
                password=body.password or "",
            )
        except HTTPException as exc:
            return json_response(exc.status_code, err_resp(exc.detail))

        data = await academy_service.build_state(user)
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
        try:
            user, token = await academy_service.login_academy_user(
                username=body.username or "",
                password=body.password or "",
            )
        except HTTPException as exc:
            return json_response(exc.status_code, err_resp(exc.detail))

        data = await academy_service.build_state(user)
        resp = json_response(200, ok_resp("Sesion iniciada.", data=data))
        set_session_cookies(resp, token)
        return resp

    if action == "logout":
        token, is_cookie_auth = extract_token_from_request(request)
        if is_cookie_auth:
            try:
                verify_csrf_if_cookie(request, True)
            except HTTPException:
                return json_response(status.HTTP_403_FORBIDDEN, err_resp("Validacion CSRF fallida."))
        if token:
            await revoke_token(token_repo, token)
        resp = json_response(200, ok_resp("Sesion cerrada."))
        clear_session_cookies(resp)
        return resp

    if action == "state":
        user, _, _ = await get_authenticated_academy_user(
            request, user_repo, token_repo, require_csrf=False
        )
        data = await academy_service.build_state(user)
        return json_response(200, ok_resp("Estado cargado.", data=data))

    if action == "complete":
        enforce_rate_limit(
            "ctf_academy_flag",
            client_ip,
            settings.RATE_LIMIT_FLAG_MAX,
            settings.RATE_LIMIT_FLAG_WINDOW_SECONDS,
        )
        user, token, err_response = await get_authenticated_academy_user(
            request, user_repo, token_repo, require_csrf=True
        )
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
            result = await academy_service.complete_challenge(
                user=user,
                challenge_id=challenge_id,
                submitted_flag=submitted_flag,
            )
        except HTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                return json_response(404, err_resp("Reto no encontrado."))
            return json_response(400, err_resp("No se pudo validar el reto."))

        if not result.is_correct:
            return json_response(401, err_resp("Flag incorrecta."))

        data = await academy_service.build_state(user)
        return json_response(200, ok_resp(result.message, data=data))

    return json_response(400, err_resp("Accion desconocida."))
