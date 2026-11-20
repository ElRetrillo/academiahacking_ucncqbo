import pytest
from httpx import AsyncClient
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings, settings
from app.models.challenge import Challenge
from app.models.solve import Submission
from app.models.user import User
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
