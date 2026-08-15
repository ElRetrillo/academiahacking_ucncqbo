import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.models.challenge import Challenge
from app.models.solve import Solve
from app.services.security import hash_password


@pytest.mark.asyncio
async def test_leaderboard_rankings_and_countries(client: AsyncClient, db_session: AsyncSession):
    # Create 3 users with different nationalities and scores
    u1 = User(username="chilean_pro", email="u1@test.com", hashed_password=hash_password("p"), nationality="CL", score=300, role="user", is_active=True)
    u2 = User(username="arg_master", email="u2@test.com", hashed_password=hash_password("p"), nationality="AR", score=500, role="user", is_active=True)
    u3 = User(username="peru_elite", email="u3@test.com", hashed_password=hash_password("p"), nationality="PE", score=100, role="user", is_active=True)

    db_session.add_all([u1, u2, u3])
    await db_session.commit()

    # Query leaderboard
    resp = await client.get("/api/v1/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_players"] == 3
    leaders = data["leaderboard"]
    assert len(leaders) == 3

    # Rank 1 must be highest score (arg_master with 500)
    assert leaders[0]["username"] == "arg_master"
    assert leaders[0]["rank"] == 1
    assert leaders[0]["score"] == 500
    assert leaders[0]["nationality"] == "AR"

    # Rank 2 must be chilean_pro with 300
    assert leaders[1]["username"] == "chilean_pro"
    assert leaders[1]["rank"] == 2
    assert leaders[1]["score"] == 300

    # Countries leaderboard
    country_resp = await client.get("/api/v1/leaderboard/countries")
    assert country_resp.status_code == 200
    countries = country_resp.json()
    assert len(countries) == 3
    # AR should be first since total_score is 500
    assert countries[0]["nationality"] == "AR"
    assert countries[0]["total_score"] == 500
