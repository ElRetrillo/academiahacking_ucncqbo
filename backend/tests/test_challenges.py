import pytest
from httpx import AsyncClient
from app.models.challenge import Challenge


@pytest.mark.asyncio
async def test_list_and_get_challenges(client: AsyncClient, sample_challenge: Challenge, user_token: str):
    # Unauthenticated list
    resp = await client.get("/api/v1/challenges")
    assert resp.status_code == 200
    challenges = resp.json()
    assert len(challenges) == 1
    assert challenges[0]["slug"] == "web-sample"
    assert challenges[0]["is_solved"] is False
    assert "flag" not in challenges[0]  # Flag must NOT be leaked to public

    # Authenticated list
    headers = {"Authorization": f"Bearer {user_token}"}
    auth_resp = await client.get("/api/v1/challenges", headers=headers)
    assert auth_resp.status_code == 200
    assert auth_resp.json()[0]["is_solved"] is False


@pytest.mark.asyncio
async def test_submit_flag_lifecycle(client: AsyncClient, sample_challenge: Challenge, user_token: str):
    headers = {"Authorization": f"Bearer {user_token}"}

    # 1. Submit incorrect flag
    bad_resp = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{wrong_flag}"},
        headers=headers,
    )
    assert bad_resp.status_code == 200
    bad_data = bad_resp.json()
    assert bad_data["is_correct"] is False
    assert bad_data["points_awarded"] == 0

    # 2. Submit correct flag
    good_resp = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{sample_flag_test}"},
        headers=headers,
    )
    assert good_resp.status_code == 200
    good_data = good_resp.json()
    assert good_data["is_correct"] is True
    assert good_data["points_awarded"] == sample_challenge.points
    assert good_data["new_total_score"] == sample_challenge.points

    # 3. Submit again (duplicate prevention)
    dup_resp = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{sample_flag_test}"},
        headers=headers,
    )
    assert dup_resp.status_code == 200
    dup_data = dup_resp.json()
    assert dup_data["is_correct"] is True
    assert dup_data["points_awarded"] == 0  # No extra points for re-solving
    assert "already solved" in dup_data["message"].lower()

    # 4. Check that challenge now appears as is_solved=True in list
    list_resp = await client.get("/api/v1/challenges", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()[0]["is_solved"] is True
    assert list_resp.json()[0]["solves_count"] == 1
