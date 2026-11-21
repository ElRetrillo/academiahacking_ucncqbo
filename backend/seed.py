import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import NotRequired, Optional, TypedDict

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal, init_db
from app.models.challenge import Challenge
from app.models.user import User
from app.services.security import (
    MAX_BCRYPT_PASSWORD_BYTES,
    REDACTED_FLAG_MARKER,
    hash_flag,
    hash_password,
)

logger = logging.getLogger(__name__)

_DEFAULT_DEV_ADMIN_PASSWORDS = ("admin123456", "CHANGE_ME", "example_")


class ChallengeSeedSpec(TypedDict):
    slug: str
    title: str
    category: str
    difficulty: str
    points: int
    default_flag: str
    description: str
    target_url: Optional[str]
    hints: Optional[str]
    version: NotRequired[str]
    repository: NotRequired[str]
    path: NotRequired[str]


CHALLENGES_DATA: list[ChallengeSeedSpec] = [
    {
        "slug": "web-001",
        "title": "Hidden in Plain Sight",
        "category": "web",
        "difficulty": "EASY",
        "points": 100,
        "default_flag": "EclipSec{h1dd3n_1n_pl41n_s1ght}",
        "description": "Find the hidden flag in the client source code and comments of the internal administration portal.",
        "target_url": "/web-001/",
        "hints": "Look inside HTML comments using Inspect Element (F12).",
    },
    {
        "slug": "web-002",
        "title": "Robots & Crawlers",
        "category": "web",
        "difficulty": "EASY",
        "points": 100,
        "default_flag": "EclipSec{r0b0ts_4r3_y0ur_fr13nd5}",
        "description": "Discover hidden endpoints that web crawlers are instructed not to index.",
        "target_url": "/web-002/",
        "hints": "Check standard web robot exclusion protocols at /robots.txt.",
    },
    {
        "slug": "web-003",
        "title": "Cookie Tampering",
        "category": "web",
        "difficulty": "EASY",
        "points": 150,
        "default_flag": "EclipSec{c00k13_m0nst3r_m4n1pul4t10n}",
        "description": "Manipulate session cookies in your browser to escalate privileges to admin.",
        "target_url": "/web-003/",
        "hints": "Inspect the 'role' cookie in the Application tab of DevTools.",
    },
    {
        "slug": "web-004",
        "title": "Ping of Death",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 250,
        "default_flag": "EclipSec{p1ng_0f_d34th_cmdi}",
        "description": "Exploit an unsanitized command injection flaw inside a network ping diagnostic tool.",
        "target_url": "/web-004/",
        "hints": "Use command separators like ; or && to chain shell commands (e.g. cat flag.txt).",
    },
    {
        "slug": "web-005",
        "title": "LFI to RCE",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 300,
        "default_flag": "EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}",
        "description": "Perform Local File Inclusion (LFI) to read sensitive system files on the host.",
        "target_url": "/web-005/",
        "hints": "Traverse directories using ../ to reach /flag.txt.",
    },
    {
        "slug": "web-006",
        "title": "SQLi Login Bypass",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 300,
        "default_flag": "EclipSec{sql1_byp4ss_l0g1n}",
        "description": "Bypass authentication on a vulnerable SQLite login form using classic SQL Injection.",
        "target_url": "/web-006/",
        "hints": "Craft an input that forces the WHERE condition to evaluate to true, e.g., ' OR 1=1 --",
    },
    {
        "slug": "web-007",
        "title": "IDOR Profiles",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 250,
        "default_flag": "EclipSec{1d0r_c4n_b3_d4ng3r0us}",
        "description": "Access unauthorized user profile resources by altering direct object identifiers.",
        "target_url": "/web-007/",
        "hints": "Try modifying the ?id= query parameter to target administrative profile IDs.",
    },
    {
        "slug": "web-008",
        "title": "Server-Side Template Injection",
        "category": "web",
        "difficulty": "HARD",
        "points": 450,
        "default_flag": "EclipSec{sst1_t3mpl4t3_1nj3ct10n}",
        "description": "Exploit Jinja2 Server-Side Template Injection (SSTI) to inspect environment variables.",
        "target_url": "/web-008/",
        "hints": "Test template expressions like {{ 7*7 }} and investigate config / os.environ.",
    },
    {
        "slug": "web-009",
        "title": "Source Code Leak",
        "category": "web",
        "difficulty": "EASY",
        "points": 150,
        "default_flag": "EclipSec{b4ckup_f1l3s_4r3_l34ks}",
        "description": "Uncover backup files left behind by developers to expose hardcoded credentials.",
        "target_url": "/web-009/",
        "hints": "Common backup extensions include .bak, .old, ~, .swp.",
    },
    {
        "slug": "web-010",
        "title": "Headers Matter",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 250,
        "default_flag": "EclipSec{h34d3rs_c4n_b3_sp00f3d}",
        "description": "Forge HTTP Request Headers (User-Agent and X-Forwarded-For) to satisfy server access controls.",
        "target_url": "/web-010/",
        "hints": "Set User-Agent to 'SecureBrowser1.0' and X-Forwarded-For to '127.0.0.1'.",
    },
    {
        "slug": "web-011",
        "title": "Command Execution GET",
        "category": "web",
        "difficulty": "HARD",
        "points": 400,
        "default_flag": "EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}",
        "description": "Perform Remote Command Execution through an unvalidated administrative GET query parameter.",
        "target_url": "/web-011/",
        "hints": "Use ?cmd=cat+flag.txt to dump the target flag.",
    },
    {
        "slug": "web-sqli-001",
        "title": "Login Bypass",
        "category": "web",
        "difficulty": "EASY",
        "points": 100,
        "version": "1.0",
        "default_flag": "EclipSec{l0g1n_byp4ss_sqli_success_9f81a7}",
        "description": "Bypass the login form of the SecureCorp admin portal and authenticate as admin to reveal the flag. Runs locally with the EclipSec CLI.",
        "target_url": None,
        "hints": "Analyze how the login query is built. What happens if the input is not treated as data?",
        "repository": settings.CHALLENGES_REPOSITORY,
        "path": "web/sqli-001",
    },
]


def load_flag_overrides() -> dict[str, str]:
    flags_file = settings.CHALLENGES_FLAGS_FILE.strip()
    if not flags_file:
        return {}
    path = Path(flags_file)
    if not path.is_file():
        raise FileNotFoundError(f"CHALLENGES_FLAGS_FILE not found: {flags_file}")
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("CHALLENGES_FLAGS_FILE must contain a JSON object mapping slug -> flag.")
    return {str(k): str(v).strip() for k, v in raw.items()}


def resolve_challenge_flag(slug: str, dev_default: str, file_overrides: dict[str, str]) -> str:
    env_key = f"FLAG_{slug.upper().replace('-', '_')}"
    env_val = os.environ.get(env_key, "").strip()
    if env_val:
        return env_val

    file_val = file_overrides.get(slug, "").strip()
    if file_val:
        return file_val

    if settings.ENVIRONMENT.lower() == "production":
        raise RuntimeError(
            f"Missing flag override for challenge '{slug}' in production ({env_key} or CHALLENGES_FLAGS_FILE)."
        )
    return dev_default


async def ensure_admin_user(db: AsyncSession) -> bool:
    admin_res = await db.execute(select(User.id).where(User.role == "admin").limit(1))
    if admin_res.scalar_one_or_none():
        return False

    password = settings.ADMIN_PASSWORD.strip()
    if not password:
        return False

    is_prod = settings.ENVIRONMENT.lower() == "production"
    is_weak_or_placeholder = len(password) < 12 or any(m in password for m in _DEFAULT_DEV_ADMIN_PASSWORDS)
    if is_prod and is_weak_or_placeholder:
        logger.warning("Skipping admin creation: configure a strong ADMIN_PASSWORD (12+ chars) in production.")
        return False

    if len(password.encode("utf-8")) > MAX_BCRYPT_PASSWORD_BYTES:
        logger.warning("Skipping admin creation: ADMIN_PASSWORD exceeds %s UTF-8 bytes.", MAX_BCRYPT_PASSWORD_BYTES)
        return False

    admin_username = settings.ADMIN_USERNAME.strip()
    admin_email = settings.ADMIN_EMAIL.strip().lower()

    conflict_res = await db.execute(
        select(User.id)
        .where(
            or_(
                func.lower(User.username) == admin_username.lower(),
                func.lower(User.email) == admin_email,
            )
        )
        .limit(1)
    )
    if conflict_res.scalar_one_or_none():
        logger.warning("Skipping admin creation: ADMIN_USERNAME or ADMIN_EMAIL is already in use.")
        return False

    now = datetime.now(timezone.utc)
    admin = User(
        username=admin_username,
        email=admin_email,
        hashed_password=hash_password(password),
        role="admin",
        nationality="CL",
        score=0,
        is_active=True,
        created_at=now,
        last_connected_at=now,
    )
    db.add(admin)
    await db.commit()
    return True


async def sync_seed_data(db: AsyncSession) -> dict[str, int]:
    file_overrides = load_flag_overrides()
    admin_created = await ensure_admin_user(db)

    existing_res = await db.execute(select(Challenge.slug))
    existing_slugs = set(existing_res.scalars().all())

    challenges_added = 0
    for ch_data in CHALLENGES_DATA:
        slug = ch_data["slug"]
        if slug in existing_slugs:
            continue

        resolved_flag = resolve_challenge_flag(slug, ch_data["default_flag"], file_overrides)
        ch = Challenge(
            slug=slug,
            title=ch_data["title"],
            category=ch_data["category"],
            difficulty=ch_data["difficulty"],
            points=ch_data["points"],
            flag=REDACTED_FLAG_MARKER,
            flag_hash=hash_flag(resolved_flag),
            description=ch_data["description"],
            target_url=ch_data.get("target_url"),
            hints=ch_data.get("hints"),
            version=ch_data.get("version", "1.0"),
            repository=ch_data.get("repository"),
            path=ch_data.get("path"),
            is_active=True,
            solves_count=0,
            created_at=datetime.now(timezone.utc),
        )
        db.add(ch)
        challenges_added += 1

    if challenges_added > 0:
        await db.commit()

    return {
        "admin_created": 1 if admin_created else 0,
        "challenges_added": challenges_added,
    }


async def seed() -> dict[str, int]:
    await init_db()
    async with AsyncSessionLocal() as db:
        return await sync_seed_data(db)


if __name__ == "__main__":
    asyncio.run(seed())
