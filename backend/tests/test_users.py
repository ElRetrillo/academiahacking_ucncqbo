import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.challenge import Challenge
from app.models.solve import Solve


@pytest.mark.asyncio
async def test_get_user_profile_detail(
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    sample_challenge: Challenge,
):
    # 1. Verify initially the user has a "Noob" rank and 0 solves
    resp = await client.get(f"/api/v1/users/{regular_user.username}/profile")
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == regular_user.username
    assert data["rank_name"] == "Noob"
    assert data["score"] == 0
    assert data["solves_count"] == 0
    assert len(data["solves_by_category"]) == 0
    assert len(data["recent_solves"]) == 0
    assert data["global_rank"] == 1  # Only player in DB

    # 2. Simulate solving the sample challenge
    solve = Solve(
        user_id=regular_user.id,
        challenge_id=sample_challenge.id,
        points_awarded=sample_challenge.points,
    )
    regular_user.score += sample_challenge.points
    db_session.add(solve)
    await db_session.commit()
    await db_session.refresh(regular_user)

    # 3. Retrieve the updated profile details
    resp2 = await client.get(f"/api/v1/users/{regular_user.username}/profile")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["score"] == 100
    assert data2["rank_name"] == "Script Kiddie"
    assert data2["solves_count"] == 1
    
    # 4. Check category breakdown
    assert len(data2["solves_by_category"]) == 1
    breakdown = data2["solves_by_category"][0]
    assert breakdown["category"] == "web"
    assert breakdown["count"] == 1

    # 5. Check recent solves list
    assert len(data2["recent_solves"]) == 1
    recent = data2["recent_solves"][0]
    assert recent["challenge_title"] == sample_challenge.title
    assert recent["category"] == "web"
    assert recent["points_awarded"] == sample_challenge.points


@pytest.mark.asyncio
async def test_get_nonexistent_user_profile(client: AsyncClient):
    resp = await client.get("/api/v1/users/does_not_exist/profile")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "User not found."
