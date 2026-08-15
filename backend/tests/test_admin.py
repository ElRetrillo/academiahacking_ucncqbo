import pytest
from httpx import AsyncClient
from app.models.challenge import Challenge
from app.models.user import User


@pytest.mark.asyncio
async def test_admin_create_and_update_challenge(client: AsyncClient, admin_token: str, user_token: str):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    user_headers = {"Authorization": f"Bearer {user_token}"}

    payload = {
        "slug": "pwn-001",
        "title": "Buffer Overflow Intro",
        "category": "pwn",
        "difficulty": "HARD",
        "points": 500,
        "flag": "EclipSec{b0f_1ntr0_pwn3d}",
        "description": "Exploit standard stack smashing vulnerability.",
        "target_url": "/pwn-001/",
        "hints": "Look for gets() function.",
    }

    # 1. Regular user trying to create challenge -> 403 Forbidden
    forbidden_resp = await client.post("/api/v1/admin/challenges", json=payload, headers=user_headers)
    assert forbidden_resp.status_code == 403

    # 2. Admin creating challenge -> 201 Created
    create_resp = await client.post("/api/v1/admin/challenges", json=payload, headers=admin_headers)
    assert create_resp.status_code == 201
    created_data = create_resp.json()
    assert created_data["slug"] == "pwn-001"
    assert created_data["points"] == 500
    assert created_data["difficulty"] == "HARD"
    assert created_data["flag"] == "EclipSec{b0f_1ntr0_pwn3d}"
    challenge_id = created_data["id"]

    # 3. Update points and difficulty
    update_payload = {
        "difficulty": "INSANE",
        "points": 650,
    }
    update_resp = await client.put(f"/api/v1/admin/challenges/{challenge_id}", json=update_payload, headers=admin_headers)
    assert update_resp.status_code == 200
    assert update_resp.json()["difficulty"] == "INSANE"
    assert update_resp.json()["points"] == 650


@pytest.mark.asyncio
async def test_admin_list_and_update_users(client: AsyncClient, admin_token: str, regular_user: User):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # List users
    users_resp = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert users_resp.status_code == 200
    users_list = users_resp.json()
    assert len(users_list) >= 2

    # Promote regular user or adjust score
    mod_payload = {
        "score": 1000,
        "nationality": "UY",
    }
    mod_resp = await client.put(f"/api/v1/admin/users/{regular_user.id}", json=mod_payload, headers=admin_headers)
    assert mod_resp.status_code == 200
    assert mod_resp.json()["score"] == 1000
    assert mod_resp.json()["nationality"] == "UY"
