import pytest
from httpx import AsyncClient
from app.models.challenge import Challenge


@pytest.mark.asyncio
async def test_public_challenge_exposes_registry_metadata_but_not_flag(
    client: AsyncClient, local_challenge: Challenge
):
    """Local challenges expose repository/path/version publicly, never the flag."""
    resp = await client.get(f"/api/v1/challenges/{local_challenge.slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["repository"] == "ElRetrillo/retos_ctf"
    assert data["path"] == "web/sqli-001"
    assert data["version"] == "1.0"
    assert "flag" not in data


@pytest.mark.asyncio
async def test_start_requires_auth(client: AsyncClient, local_challenge: Challenge):
    resp = await client.post(f"/api/v1/challenges/{local_challenge.slug}/start")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_start_returns_instance_with_download_metadata(
    client: AsyncClient, local_challenge: Challenge, user_token: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "running"
    assert data["id"]
    ch = data["challenge"]
    # The CLI needs these to download and run the challenge locally
    assert ch["repository"] == "ElRetrillo/retos_ctf"
    assert ch["path"] == "web/sqli-001"
    assert ch["version"] == "1.0"
    assert ch["slug"] == "web-sqli-001"
    assert "flag" not in ch


@pytest.mark.asyncio
async def test_start_is_idempotent(
    client: AsyncClient, local_challenge: Challenge, user_token: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    first = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers
    )
    second = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers
    )
    assert first.status_code == second.status_code == 200
    # Same running instance returned, not a duplicate
    assert first.json()["id"] == second.json()["id"]


@pytest.mark.asyncio
async def test_start_unknown_challenge_404(client: AsyncClient, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.post("/api/v1/challenges/does-not-exist/start", headers=headers)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_stop_running_instance(
    client: AsyncClient, local_challenge: Challenge, user_token: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    await client.post(f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers)
    resp = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/stop", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "stopped"
    assert data["stopped_at"] is not None


@pytest.mark.asyncio
async def test_stop_without_running_instance_404(
    client: AsyncClient, local_challenge: Challenge, user_token: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    resp = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/stop", headers=headers
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_restart_after_stop_creates_new_instance(
    client: AsyncClient, local_challenge: Challenge, user_token: str
):
    headers = {"Authorization": f"Bearer {user_token}"}
    first = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers
    )
    await client.post(f"/api/v1/challenges/{local_challenge.slug}/stop", headers=headers)
    third = await client.post(
        f"/api/v1/challenges/{local_challenge.slug}/start", headers=headers
    )
    assert third.status_code == 200
    assert third.json()["id"] != first.json()["id"]
    assert third.json()["status"] == "running"
