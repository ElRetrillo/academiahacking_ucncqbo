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


@pytest.mark.asyncio
async def test_challenge_filters_recent_and_categories(client: AsyncClient, sample_challenge: Challenge):
    # 1. Test /challenges/recent
    recent_resp = await client.get("/api/v1/challenges/recent?limit=5")
    assert recent_resp.status_code == 200
    recent_list = recent_resp.json()
    assert len(recent_list) == 1
    assert recent_list[0]["slug"] == sample_challenge.slug

    # 2. Test /challenges/categories
    cats_resp = await client.get("/api/v1/challenges/categories")
    assert cats_resp.status_code == 200
    cats_list = cats_resp.json()
    assert len(cats_list) == 1
    assert cats_list[0]["category"] == "web"
    assert cats_list[0]["count"] == 1

    # 3. Test filtering by category and difficulty
    filter_resp = await client.get("/api/v1/challenges?category=web&difficulty=EASY")
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) == 1

    no_match_resp = await client.get("/api/v1/challenges?category=pwn")
    assert no_match_resp.status_code == 200
    assert len(no_match_resp.json()) == 0


# ── target_url resolution against CHALLENGES_BASE_URL ────────────────────────

from app.config import settings
from app.services.challenge_service import resolve_target_url


@pytest.mark.parametrize(
    "base, stored, expected",
    [
        ("https://ctf.example.com", "/web-001/", "https://ctf.example.com/web-001/"),
        ("https://ctf.example.com/", "/web-001/", "https://ctf.example.com/web-001/"),
        ("https://ctf.example.com", "https://other.host/x", "https://other.host/x"),
        ("https://ctf.example.com", "//evil.example/x", "//evil.example/x"),
        ("https://ctf.example.com", None, None),
        ("https://ctf.example.com", "", ""),
        ("", "/web-001/", "/web-001/"),
    ],
)
def test_resolve_target_url(monkeypatch, base, stored, expected):
    monkeypatch.setattr(settings, "CHALLENGES_BASE_URL", base)
    assert resolve_target_url(stored) == expected


@pytest.mark.asyncio
async def test_public_challenge_listing_serves_absolute_target_url(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr(settings, "CHALLENGES_BASE_URL", "https://ctf.example.com")
    db_session.add(
        Challenge(
            slug="web-900",
            title="Resolver check",
            description="d",
            category="web",
            difficulty="EASY",
            points=10,
            flag="EclipSec{x}",
            flag_hash="h",
            target_url="/web-900/",
            is_active=True,
        )
    )
    await db_session.commit()

    listing = await client.get("/api/v1/challenges")
    assert listing.status_code == 200
    urls = {c["slug"]: c["target_url"] for c in listing.json()}
    assert urls["web-900"] == "https://ctf.example.com/web-900/"

    detail = await client.get("/api/v1/challenges/web-900")
    assert detail.json()["target_url"] == "https://ctf.example.com/web-900/"
