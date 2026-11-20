from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.challenge import Challenge
from app.models.solve import Solve
from app.models.user import User
from app.services.security import REDACTED_FLAG_MARKER, create_access_token, hash_flag, hash_password


@pytest.mark.asyncio
async def test_leaderboard_rankings_and_countries(client: AsyncClient, db_session: AsyncSession):
    u1 = User(
        username="chilean_pro",
        email="u1@test.com",
        hashed_password=hash_password("p"),
        nationality="CL",
        score=300,
        role="user",
        is_active=True,
    )
    u2 = User(
        username="arg_master",
        email="u2@test.com",
        hashed_password=hash_password("p"),
        nationality="AR",
        score=500,
        role="user",
        is_active=True,
    )
    u3 = User(
        username="peru_elite",
        email="u3@test.com",
        hashed_password=hash_password("p"),
        nationality="PE",
        score=100,
        role="user",
        is_active=True,
    )

    db_session.add_all([u1, u2, u3])
    await db_session.commit()

    resp = await client.get("/api/v1/leaderboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_players"] == 3
    leaders = data["leaderboard"]
    assert len(leaders) == 3

    assert leaders[0]["username"] == "arg_master"
    assert leaders[0]["rank"] == 1
    assert leaders[0]["score"] == 500
    assert leaders[0]["nationality"] == "AR"

    assert leaders[1]["username"] == "chilean_pro"
    assert leaders[1]["rank"] == 2
    assert leaders[1]["score"] == 300

    country_resp = await client.get("/api/v1/leaderboard/countries")
    assert country_resp.status_code == 200
    countries = country_resp.json()
    assert len(countries) == 3
    assert countries[0]["nationality"] == "AR"
    assert countries[0]["total_score"] == 500


@pytest.mark.asyncio
async def test_leaderboard_tiebreaker_consistent_across_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
):
    now = datetime.now(timezone.utc)
    ch = Challenge(
        slug="tiebreak-ch",
        title="Tiebreak Challenge",
        description="Ranking tiebreak verification",
        category="web",
        difficulty="MEDIUM",
        points=200,
        flag=REDACTED_FLAG_MARKER,
        flag_hash=hash_flag("EclipSec{tiebreak_flag}"),
        is_active=True,
        solves_count=2,
    )
    player_b = User(
        username="player_earlier_reg_later_solve",
        email="playerb@test.com",
        hashed_password=hash_password("pass123456"),
        nationality="CL",
        score=200,
        role="user",
        is_active=True,
        created_at=now - timedelta(hours=3),
        last_connected_at=now,
    )
    player_a = User(
        username="player_later_reg_earlier_solve",
        email="playera@test.com",
        hashed_password=hash_password("pass123456"),
        nationality="CL",
        score=200,
        role="user",
        is_active=True,
        created_at=now - timedelta(hours=1),
        last_connected_at=now,
    )
    db_session.add_all([ch, player_b, player_a])
    await db_session.commit()
    await db_session.refresh(ch)
    await db_session.refresh(player_a)
    await db_session.refresh(player_b)

    db_session.add_all(
        [
            Solve(
                user_id=player_a.id,
                challenge_id=ch.id,
                points_awarded=200,
                solved_at=now - timedelta(minutes=30),
            ),
            Solve(
                user_id=player_b.id,
                challenge_id=ch.id,
                points_awarded=200,
                solved_at=now - timedelta(minutes=5),
            ),
        ]
    )
    await db_session.commit()

    lb_resp = await client.get("/api/v1/leaderboard")
    assert lb_resp.status_code == 200
    leaders = lb_resp.json()["leaderboard"]
    assert leaders[0]["username"] == player_a.username
    assert leaders[0]["rank"] == 1
    assert leaders[1]["username"] == player_b.username
    assert leaders[1]["rank"] == 2

    prof_a = await client.get(f"/api/v1/users/{player_a.username}/profile")
    prof_b = await client.get(f"/api/v1/users/{player_b.username}/profile")
    assert prof_a.status_code == prof_b.status_code == 200
    assert prof_a.json()["global_rank"] == 1
    assert prof_a.json()["globalRank"] == 1
    assert prof_b.json()["global_rank"] == 2
    assert prof_b.json()["globalRank"] == 2

    token_a = create_access_token(player_a.id)
    token_b = create_access_token(player_b.id)
    acad_a = await client.post(
        "/api/ctf-academy",
        json={"action": "state"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    acad_b = await client.post(
        "/api/ctf-academy",
        json={"action": "state"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert acad_a.status_code == acad_b.status_code == 200
    assert acad_a.json()["data"]["currentUser"]["globalRank"] == 1
    assert acad_b.json()["data"]["currentUser"]["globalRank"] == 2
