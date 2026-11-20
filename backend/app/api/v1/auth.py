from fastapi import APIRouter, Depends, Request, Response, status

from app.api.deps import (
    clear_session_cookies,
    extract_token_from_request,
    get_auth_service,
    get_current_user,
    get_token_repository,
    get_user_service,
    revoke_token,
    set_session_cookies,
    verify_csrf_if_cookie,
)
from app.models.user import User
from app.repositories.protocols import TokenRevocationRepositoryProtocol
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
async def register(
    req: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Register a new player account."""
    user = await auth_service.register_user(req)
    return await auth_service.get_user_profile(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def login(
    req: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate and obtain a CLI/BFF Bearer token."""
    return await auth_service.authenticate_user(req, token_type="cli")


@router.post(
    "/session/login",
    response_model=SessionResponse,
    dependencies=[Depends(rate_limit_auth)],
)
async def session_login(
    req: LoginRequest,
    response: Response,
    auth_service: AuthService = Depends(get_auth_service),
):
    """Authenticate web session using HttpOnly and CSRF cookies without exposing tokens in JSON."""
    token_resp = await auth_service.authenticate_user(req, token_type="web")
    set_session_cookies(response, token_resp.access_token)
    return SessionResponse(authenticated=True, user=token_resp.user)


@router.post("/session/logout", response_model=LogoutResponse)
@router.post("/logout", response_model=LogoutResponse)
async def session_logout(
    request: Request,
    response: Response,
    token_repo: TokenRevocationRepositoryProtocol = Depends(get_token_repository),
):
    """Revoke active session token and clear browser cookies."""
    token, is_cookie_auth = extract_token_from_request(request)
    if is_cookie_auth:
        verify_csrf_if_cookie(request, True)
    if token:
        await revoke_token(token_repo, token)
    clear_session_cookies(response)
    return LogoutResponse(authenticated=False, message="Session closed.")


@router.get("/me", response_model=UserProfileDetail)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service),
):
    """Retrieve the authenticated player profile and live statistics."""
    return await user_service.get_user_profile_detail(current_user.username)


@router.put("/me", response_model=UserProfile)
async def update_profile(
    req: UserUpdate,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
):
    """Update profile details such as nationality or password."""
    return await auth_service.update_profile(current_user, req)
