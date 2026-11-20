from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.config import Settings, settings
from app.models.challenge import Challenge
from app.models.solve import Solve, Submission
from app.models.user import User
from app.repositories import SqlAlchemyChallengeRepository, SqlAlchemyTokenRevocationRepository
from app.services.rate_limiter import InMemorySlidingWindowRateLimiter, get_client_ip
from app.services.security import REDACTED_FLAG_MARKER, hash_flag, verify_flag


def test_production_settings_fail_fast():
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="change-this-in-production-super-secret-ctf-key-2026",
            FLAG_HMAC_SECRET="valid-production-hmac-secret-with-more-than-32-chars",
            CORS_ORIGINS=["https://eclipsec.cl"],
            CORS_ORIGIN_REGEX="",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="valid-production-jwt-secret-with-more-than-32-chars",
            FLAG_HMAC_SECRET="short",
            CORS_ORIGINS=["https://eclipsec.cl"],
            CORS_ORIGIN_REGEX="",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="valid-production-jwt-secret-with-more-than-32-chars",
            FLAG_HMAC_SECRET="valid-production-hmac-secret-with-more-than-32-chars",
            CORS_ORIGINS=["https://eclipsec.cl"],
            CORS_ORIGIN_REGEX=r"^https:\/\/.*\.vercel\.app$",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            JWT_SECRET="valid-production-jwt-secret-with-more-than-32-chars",
            FLAG_HMAC_SECRET="valid-production-hmac-secret-with-more-than-32-chars",
            CORS_ORIGINS=["https://eclipsec.cl"],
            COOKIE_SAMESITE="none",
            COOKIE_SECURE=False,
        )

    valid = Settings(
        ENVIRONMENT="production",
        JWT_SECRET="prod-jwt-9f8e7d6c5b4a3210fedcba9876543210",
        FLAG_HMAC_SECRET="prod-hmac-0123456789abcdef0123456789abcdef",
        CORS_ORIGINS=["https://eclipsec.cl"],
        CORS_ORIGIN_REGEX="",
    )
    assert valid.cookie_secure_effective is True


@pytest.mark.asyncio
async def test_session_cookie_csrf_and_jti_revocation(
    client: AsyncClient,
    regular_user: User,
    sample_challenge: Challenge,
):
    login_resp = await client.post(
        "/api/v1/auth/session/login",
        json={"username_or_email": regular_user.username, "password": "playerpass123"},
    )
    assert login_resp.status_code == 200
    body = login_resp.json()
    assert body["authenticated"] is True
    assert "access_token" not in body
    assert body["user"]["username"] == regular_user.username
    assert settings.COOKIE_NAME in login_resp.cookies
    assert settings.CSRF_COOKIE_NAME in login_resp.cookies

    me_resp = await client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == regular_user.email

    missing_csrf = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{sample_flag_test}"},
    )
    assert missing_csrf.status_code == 403

    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    valid_submit = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{sample_flag_test}"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert valid_submit.status_code == 200
    assert valid_submit.json()["is_correct"] is True

    captured_session_cookie = client.cookies.get(settings.COOKIE_NAME)
    logout_resp = await client.post(
        "/api/v1/auth/session/logout",
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["authenticated"] is False

    client.cookies.clear()
    client.cookies.set(settings.COOKIE_NAME, captured_session_cookie)
    reused_resp = await client.get("/api/v1/auth/me")
    assert reused_resp.status_code == 401


@pytest.mark.asyncio
async def test_public_profile_hides_pii(client: AsyncClient, regular_user: User, user_token: str):
    public_resp = await client.get(f"/api/v1/users/{regular_user.username}/profile")
    assert public_resp.status_code == 200
    public_data = public_resp.json()
    assert public_data["username"] == regular_user.username
    for pii_field in ("email", "role", "is_active", "isActive", "last_connected_at", "lastConnectedAt"):
        assert pii_field not in public_data

    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {user_token}"})
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == regular_user.email


@pytest.mark.asyncio
async def test_hmac_flag_verification_rejects_redacted_and_hashes_submissions(
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    sample_challenge: Challenge,
    user_token: str,
):
    assert verify_flag(REDACTED_FLAG_MARKER, REDACTED_FLAG_MARKER, sample_challenge.flag_hash) is False
    assert verify_flag("EclipSec{sample_flag_test}", REDACTED_FLAG_MARKER, sample_challenge.flag_hash) is True

    headers = {"Authorization": f"Bearer {user_token}"}
    wrong_flag = "EclipSec{secret_guess_never_store_plain}"
    resp = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": wrong_flag},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["is_correct"] is False

    sub_res = await db_session.execute(select(Submission).where(Submission.user_id == regular_user.id))
    submission = sub_res.scalar_one()
    assert submission.submitted_flag != wrong_flag
    assert submission.submitted_flag == hash_flag(wrong_flag)


@pytest.mark.asyncio
async def test_rate_limiting_returns_429(client: AsyncClient, regular_user: User, sample_challenge: Challenge, user_token: str):
    for _ in range(settings.RATE_LIMIT_AUTH_MAX):
        r = await client.post(
            "/api/v1/auth/login",
            json={"username_or_email": regular_user.username, "password": "wrong"},
        )
        assert r.status_code == 401

    limited_login = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": regular_user.username, "password": "wrong"},
    )
    assert limited_login.status_code == 429
    assert "Retry-After" in limited_login.headers

    headers = {"Authorization": f"Bearer {user_token}"}
    for _ in range(settings.RATE_LIMIT_FLAG_MAX):
        r = await client.post(
            f"/api/v1/challenges/{sample_challenge.slug}/submit",
            json={"flag": "EclipSec{wrong}"},
            headers=headers,
        )
        assert r.status_code == 200

    limited_flag = await client.post(
        f"/api/v1/challenges/{sample_challenge.slug}/submit",
        json={"flag": "EclipSec{wrong}"},
        headers=headers,
    )
    assert limited_flag.status_code == 429
    assert "Retry-After" in limited_flag.headers


@pytest.mark.asyncio
async def test_ctf_academy_hardening_and_security_headers(
    client: AsyncClient,
    sample_challenge: Challenge,
):
    short_pw = await client.post(
        "/api/ctf-academy",
        json={"action": "register", "username": "academy_user", "password": "12345"},
    )
    assert short_pw.status_code == 400
    assert short_pw.json()["ok"] is False

    short_login = await client.post(
        "/api/ctf-academy",
        json={"action": "login", "username": "ab", "password": "anypassword"},
    )
    assert short_login.status_code == 401
    assert short_login.json()["ok"] is False

    reg_resp = await client.post(
        "/api/ctf-academy",
        json={"action": "register", "username": "academy_user", "password": "securepassword1"},
    )
    assert reg_resp.status_code == 200
    reg_body = reg_resp.json()
    assert reg_body["ok"] is True
    assert "token" not in reg_body
    assert reg_resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert reg_resp.headers.get("X-Frame-Options") == "DENY"
    assert reg_resp.headers.get("Cache-Control") == "no-store"

    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    complete_no_csrf = await client.post(
        "/api/ctf-academy",
        json={"action": "complete", "challengeId": sample_challenge.slug, "flag": "EclipSec{sample_flag_test}"},
    )
    assert complete_no_csrf.status_code == 403

    complete_ok = await client.post(
        "/api/ctf-academy",
        json={"action": "complete", "challengeId": sample_challenge.slug, "flag": "EclipSec{sample_flag_test}"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert complete_ok.status_code == 200
    assert complete_ok.json()["data"]["currentUser"]["score"] == sample_challenge.points

    logout_resp = await client.post(
        "/api/ctf-academy",
        json={"action": "logout"},
        headers={"X-CSRF-Token": csrf_token},
    )
    assert logout_resp.status_code == 200

    state_after_logout = await client.post("/api/ctf-academy", json={"action": "state"})
    assert state_after_logout.status_code == 200
    assert state_after_logout.json()["data"]["currentUser"] is None


@pytest.mark.asyncio
async def test_bcrypt_72_byte_limit_handled_safely(client: AsyncClient, regular_user: User, user_token: str):
    over_ascii = "a" * 80
    over_multibyte = "\u00e9" * 40

    for idx, bad_pw in enumerate((over_ascii, over_multibyte)):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "username": f"longpw_user_{idx}",
                "email": f"longpw_{idx}@example.com",
                "password": bad_pw,
                "nationality": "CL",
            },
        )
        assert resp.status_code == 422

        acad_resp = await client.post(
            "/api/ctf-academy",
            json={"action": "register", "username": f"acad_long_{idx}", "password": bad_pw},
        )
        assert acad_resp.status_code == 400
        assert acad_resp.json()["ok"] is False

    update_resp = await client.put(
        "/api/v1/auth/me",
        json={"current_password": "playerpass123", "new_password": over_multibyte},
        headers={"Authorization": f"Bearer {user_token}"},
    )
    assert update_resp.status_code == 422

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": regular_user.username, "password": over_ascii},
    )
    assert login_resp.status_code == 401


def test_trusted_proxy_client_ip_and_bounded_rate_limiter(monkeypatch):
    request = Request(
        scope={
            "type": "http",
            "method": "POST",
            "path": "/api/v1/auth/login",
            "client": ("10.0.0.1", 12345),
            "headers": [(b"x-forwarded-for", b"198.51.100.10, 203.0.113.9")],
        }
    )

    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 0)
    assert get_client_ip(request) == "10.0.0.1"

    monkeypatch.setattr(settings, "TRUSTED_PROXY_COUNT", 1)
    assert get_client_ip(request) == "203.0.113.9"

    bounded_limiter = InMemorySlidingWindowRateLimiter(max_keys=3)
    for k in ("k1", "k2", "k3", "k4"):
        allowed, _ = bounded_limiter.check(k, limit=5, window_seconds=60)
        assert allowed is True
    assert len(bounded_limiter._buckets) == 3
    assert "k1" not in bounded_limiter._buckets


@pytest.mark.asyncio
async def test_challenge_and_admin_validation_and_self_lockout_guard(
    client: AsyncClient,
    admin_user: User,
    regular_user: User,
    admin_token: str,
):
    headers = {"Authorization": f"Bearer {admin_token}"}
    base_payload = {
        "slug": "val-check",
        "title": "Validation Check",
        "description": "Challenge validation test",
        "category": "WEB",
        "difficulty": "hard",
        "points": 100,
        "flag": "EclipSec{valid_flag_1}",
    }

    invalid_variants = [
        {"target_url": "javascript:alert(1)"},
        {"target_url": "//evil.example/payload"},
        {"flag": "   "},
        {"flag": REDACTED_FLAG_MARKER},
        {"difficulty": "IMPOSSIBLE"},
        {"path": "../secret"},
    ]
    for patch in invalid_variants:
        resp = await client.post("/api/v1/admin/challenges", json={**base_payload, **patch}, headers=headers)
        assert resp.status_code == 422

    ok_resp = await client.post("/api/v1/admin/challenges", json=base_payload, headers=headers)
    assert ok_resp.status_code == 201
    assert ok_resp.json()["category"] == "web"
    assert ok_resp.json()["difficulty"] == "HARD"

    bad_role = await client.put(
        f"/api/v1/admin/users/{regular_user.id}",
        json={"role": "superadmin"},
        headers=headers,
    )
    assert bad_role.status_code == 422

    negative_score = await client.put(
        f"/api/v1/admin/users/{regular_user.id}",
        json={"score": -10},
        headers=headers,
    )
    assert negative_score.status_code == 422

    self_deactivate = await client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        json={"is_active": False},
        headers=headers,
    )
    assert self_deactivate.status_code == 400

    self_downgrade = await client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        json={"role": "user"},
        headers=headers,
    )
    assert self_downgrade.status_code == 400


@pytest.mark.asyncio
async def test_case_insensitive_email_dedup_and_token_revocation_pruning(
    client: AsyncClient,
    db_session: AsyncSession,
):
    reg1 = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "MixedUser",
            "email": "MixedCase@Example.Com",
            "password": "securepassword123",
            "nationality": "cl",
        },
    )
    assert reg1.status_code == 201
    assert reg1.json()["email"] == "mixedcase@example.com"
    assert reg1.json()["nationality"] == "CL"

    reg2 = await client.post(
        "/api/v1/auth/register",
        json={
            "username": "OtherUser",
            "email": "MIXEDCASE@example.com",
            "password": "securepassword123",
            "nationality": "CL",
        },
    )
    assert reg2.status_code == 400

    login_mixed = await client.post(
        "/api/v1/auth/login",
        json={"username_or_email": "MIXEDCASE@EXAMPLE.COM", "password": "securepassword123"},
    )
    assert login_mixed.status_code == 200

    repo = SqlAlchemyTokenRevocationRepository(db_session)
    now = datetime.now(timezone.utc)
    await repo.revoke("expired-jti", now - timedelta(hours=1))
    await repo.revoke("active-jti", now + timedelta(hours=1))
    await repo.revoke("active-jti", now + timedelta(hours=1))

    assert await repo.is_revoked("active-jti") is True
    assert await repo.is_revoked("expired-jti") is False


@pytest.mark.asyncio
async def test_sqlite_foreign_key_cascade_and_concurrent_solve_idempotency(
    client: AsyncClient,
    db_session: AsyncSession,
    regular_user: User,
    sample_challenge: Challenge,
    admin_token: str,
):
    solve = Solve(
        user_id=regular_user.id,
        challenge_id=sample_challenge.id,
        points_awarded=sample_challenge.points,
    )
    db_session.add(solve)
    await db_session.commit()

    del_resp = await client.delete(
        f"/api/v1/admin/challenges/{sample_challenge.id}",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert del_resp.status_code == 204

    remaining = await db_session.execute(
        select(Solve).where(Solve.challenge_id == sample_challenge.id)
    )
    assert remaining.scalar_one_or_none() is None

    ch2 = Challenge(
        slug="race-test",
        title="Race Test",
        description="Concurrency solve test",
        category="web",
        difficulty="EASY",
        points=150,
        flag=REDACTED_FLAG_MARKER,
        flag_hash=hash_flag("EclipSec{race_ok}"),
        is_active=True,
        solves_count=0,
    )
    db_session.add(ch2)
    await db_session.commit()
    await db_session.refresh(ch2)

    repo = SqlAlchemyChallengeRepository(db_session)
    now = datetime.now(timezone.utc)
    flag_digest = hash_flag("EclipSec{race_ok}")

    awarded1, score1 = await repo.record_correct_solve(regular_user, ch2, flag_digest, now)
    assert awarded1 is True
    assert score1 == 150

    awarded2, score2 = await repo.record_correct_solve(regular_user, ch2, flag_digest, now)
    assert awarded2 is False
    assert score2 == 150
    await db_session.refresh(ch2)
    assert ch2.solves_count == 1
