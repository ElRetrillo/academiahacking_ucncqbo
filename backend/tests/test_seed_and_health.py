import json
from pathlib import Path

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.main import app
from app.models.challenge import Challenge
from app.models.user import User
from app.services.security import REDACTED_FLAG_MARKER, hash_flag, hash_password
from seed import CHALLENGES_DATA, ensure_admin_user, load_flag_overrides, resolve_challenge_flag, sync_seed_data


@pytest.mark.asyncio
async def test_health_and_root_endpoints(client: AsyncClient):
    root_resp = await client.get("/")
    assert root_resp.status_code == 200
    assert root_resp.json() == {"status": "ok"}

    health_resp = await client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json() == {"status": "ok", "database": "ok"}

    class BrokenSession:
        async def execute(self, *args, **kwargs):
            raise RuntimeError("database offline")

    async def broken_db():
        yield BrokenSession()

    previous_override = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = broken_db
    try:
        degraded_resp = await client.get("/health")
        assert degraded_resp.status_code == 503
        assert degraded_resp.json() == {"status": "degraded", "database": "error"}
    finally:
        if previous_override is not None:
            app.dependency_overrides[get_db] = previous_override
        else:
            app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_seed_idempotency_and_partial_sync(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    existing = Challenge(
        slug="web-001",
        title="Existing Custom Title",
        description="Custom description preserved",
        category="web",
        difficulty="EASY",
        points=100,
        flag=REDACTED_FLAG_MARKER,
        flag_hash=hash_flag("EclipSec{custom}"),
        target_url="/web-001/",
        is_active=True,
    )
    db_session.add(existing)
    await db_session.commit()

    first_summary = await sync_seed_data(db_session)
    assert first_summary["admin_created"] == 1
    assert first_summary["challenges_added"] == len(CHALLENGES_DATA) - 1

    ch_res = await db_session.execute(select(Challenge))
    all_challenges = ch_res.scalars().all()
    assert len(all_challenges) == len(CHALLENGES_DATA)
    for ch in all_challenges:
        assert ch.flag == REDACTED_FLAG_MARKER
        assert ch.flag_hash

    preserved = next(c for c in all_challenges if c.slug == "web-001")
    assert preserved.title == "Existing Custom Title"

    second_summary = await sync_seed_data(db_session)
    assert second_summary == {"admin_created": 0, "challenges_added": 0}


def test_seed_production_fail_fast_and_overrides(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "CHALLENGES_FLAGS_FILE", "")
    monkeypatch.delenv("FLAG_WEB_001", raising=False)
    monkeypatch.delenv("FLAG_WEB_002", raising=False)

    with pytest.raises(RuntimeError):
        resolve_challenge_flag("web-001", "EclipSec{dev_default}", {})

    monkeypatch.setenv("FLAG_WEB_001", "EclipSec{override_from_env}")
    assert resolve_challenge_flag("web-001", "EclipSec{dev_default}", {}) == "EclipSec{override_from_env}"

    flags_file = tmp_path / "flags.json"
    flags_file.write_text(
        json.dumps({"web-002": "EclipSec{override_from_file}"}),
        encoding="utf-8",
    )
    monkeypatch.setattr(settings, "CHALLENGES_FLAGS_FILE", str(flags_file))
    overrides = load_flag_overrides()
    assert resolve_challenge_flag("web-002", "EclipSec{dev_default}", overrides) == "EclipSec{override_from_file}"


@pytest.mark.asyncio
async def test_seed_admin_avoids_username_collision(db_session: AsyncSession, monkeypatch):
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    non_admin = User(
        username=settings.ADMIN_USERNAME,
        email="not-admin@example.com",
        hashed_password=hash_password("playerpass123"),
        role="user",
        nationality="CL",
        score=0,
        is_active=True,
    )
    db_session.add(non_admin)
    await db_session.commit()

    created = await ensure_admin_user(db_session)
    assert created is False
