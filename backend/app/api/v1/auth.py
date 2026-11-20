from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    clear_session_cookies,
    extract_token_from_request,
    get_current_user,
    revoke_token,
    set_session_cookies,
    verify_csrf_if_cookie,
)
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    LogoutResponse,
    RegisterRequest,
    SessionResponse,
    TokenResponse,
)
from app.schemas.user import UserProfile, UserProfileDetail, UserUpdate
from app.services.auth_service import AuthService
from app.services.rate_limiter import rate_limit_auth
from app.services.user_service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserProfile,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(rate_limit_auth)],
)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new player account."""
    user = await AuthService.register_user(db, req)
    return await AuthService.get_user_profile(db, user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Authenticate and obtain a CLI/BFF Bearer token."""
    return await AuthService.authenticate_user(db, req, token_type="cli")


@router.post(
    "/session/login",
    response_model=SessionResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def session_login(
    req: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate web session using HttpOnly and CSRF cookies without exposing tokens in JSON."""
    token_resp = await AuthService.authenticate_user(db, req, token_type="web")
    set_session_cookies(response, token_resp.access_token)
    return SessionResponse(authenticated=True, user=token_resp.user)


@router.post("/session/logout", response_model=LogoutResponse)
@router.post("/logout", response_model=LogoutResponse)
async def session_logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db),
):
    """Revoke active session token and clear browser cookies."""
    token, is_cookie_auth = extract_token_from_request(request)
    if is_cookie_auth:
        verify_csrf_if_cookie(request, True)
    if token:
        await revoke_token(db, token)
    clear_session_cookies(response)
    return LogoutResponse(authenticated=False, message="Session closed.")


@router.get("/me", response_model=UserProfileDetail)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve the authenticated player profile and live statistics."""
    return await UserService.get_user_profile_detail(db, current_user.username)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update profile details such as nationality or password."""
    return await AuthService.update_profile(db, current_user, req)
