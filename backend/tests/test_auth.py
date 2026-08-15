import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "username": "new_player",
        "email": "player@eclipsec.cl",
        "password": "supersecurepassword123",
        "nationality": "CL",
    }
    reg_resp = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 201
    user_data = reg_resp.json()
    assert user_data["username"] == "new_player"
    assert user_data["nationality"] == "CL"
    assert user_data["score"] == 0
    assert "created_at" in user_data
    assert "last_connected_at" in user_data

    # 2. Login
    login_payload = {
        "username_or_email": "new_player",
        "password": "supersecurepassword123",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["user"]["username"] == "new_player"

    # 3. Get /me with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_resp = await client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["username"] == "new_player"
    assert me_data["email"] == "player@eclipsec.cl"


@pytest.mark.asyncio
async def test_duplicate_registration_fails(client: AsyncClient):
    reg_payload = {
        "username": "duplicate_user",
        "email": "dup@eclipsec.cl",
        "password": "securepassword",
        "nationality": "AR",
    }
    r1 = await client.post("/api/v1/auth/register", json=reg_payload)
    assert r1.status_code == 201

    r2 = await client.post("/api/v1/auth/register", json=reg_payload)
    assert r2.status_code == 400
    assert "already registered" in r2.json()["detail"]


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    update_payload = {"nationality": "PE"}
    resp = await client.put("/api/v1/auth/me", json=update_payload, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["nationality"] == "PE"
