from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.challenges import router as challenges_router
from app.api.v1.leaderboard import router as leaderboard_router
from app.api.v1.admin import router as admin_router
from app.api.v1.ctf_academy import router as ctf_academy_router
from app.api.v1.users import router as users_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(challenges_router)
api_v1_router.include_router(leaderboard_router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(users_router)

# Exported separately — mounted at root (no /api/v1 prefix) to match EclipSec frontend contract
__all__ = ["api_v1_router", "ctf_academy_router"]
