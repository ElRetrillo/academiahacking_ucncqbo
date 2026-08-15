import asyncio
from datetime import datetime, timezone
from sqlalchemy import select
from app.database import engine, AsyncSessionLocal, init_db
from app.models.user import User
from app.models.challenge import Challenge
from app.models.solve import Solve, Submission
from app.services.security import hash_password, hash_flag
from app.config import settings

CHALLENGES_DATA = [
    {
        "slug": "web-001",
        "title": "Hidden in Plain Sight",
        "category": "web",
        "difficulty": "EASY",
        "points": 100,
        "flag": "EclipSec{h1dd3n_1n_pl41n_s1ght}",
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
        "flag": "EclipSec{r0b0ts_4r3_y0ur_fr13nd5}",
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
        "flag": "EclipSec{c00k13_m0nst3r_m4n1pul4t10n}",
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
        "flag": "EclipSec{p1ng_0f_d34th_c0mm4nd_1nj}",
        "description": "Exploit an unsanitized command injection flaw inside a network ping diagnostic tool.",
        "target_url": "/web-004/",
        "hints": "Use command separators like ; or && to chain shell commands.",
    },
    {
        "slug": "web-005",
        "title": "LFI to RCE",
        "category": "web",
        "difficulty": "MEDIUM",
        "points": 300,
        "flag": "EclipSec{l0c4l_f1l3_1nclus10n_m4st3r}",
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
        "flag": "EclipSec{sql1_byp4ss_l0g1n}",
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
        "flag": "EclipSec{1d0r_c4n_b3_d4ng3r0us}",
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
        "flag": "EclipSec{sst1_t3mpl4t3_1nj3ct10n}",
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
        "flag": "EclipSec{b4ckup_f1l3s_4r3_l34ks}",
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
        "flag": "EclipSec{h34d3rs_c4n_b3_sp00f3d}",
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
        "flag": "EclipSec{c0mm4nd_3x3cut10n_v1a_g3t}",
        "description": "Perform Remote Command Execution through an unvalidated administrative GET query parameter.",
        "target_url": "/web-011/",
        "hints": "Use ?cmd=cat+/flag.txt to dump the target flag.",
    },
]

DEMO_USERS = [
    {"username": "vortex_hacker", "email": "vortex@example.com", "nationality": "CL", "password": "password123"},
    {"username": "cyber_pampa", "email": "pampa@example.com", "nationality": "AR", "password": "password123"},
    {"username": "inca_sec", "email": "incasec@example.com", "nationality": "PE", "password": "password123"},
    {"username": "aztec_guard", "email": "aztec@example.com", "nationality": "MX", "password": "password123"},
    {"username": "iberian_pwn", "email": "iberian@example.com", "nationality": "ES", "password": "password123"},
]


async def seed():
    print("Initializing database tables...")
    await init_db()

    async with AsyncSessionLocal() as db:
        # 1. Seed Admin User
        admin_res = await db.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
        admin = admin_res.scalar_one_or_none()
        if not admin:
            print(f"Creating default admin account: {settings.ADMIN_USERNAME} ({settings.ADMIN_EMAIL})")
            admin = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                role="admin",
                nationality="CL",
                score=0,
                is_active=True,
                created_at=datetime.now(timezone.utc),
                last_connected_at=datetime.now(timezone.utc),
            )
            db.add(admin)
            await db.commit()
            print("✓ Admin user created.")
        else:
            print("✓ Admin user already exists.")

        # 2. Seed Challenges
        print("Seeding CTF challenges...")
        for ch_data in CHALLENGES_DATA:
            res = await db.execute(select(Challenge).where(Challenge.slug == ch_data["slug"]))
            existing_ch = res.scalar_one_or_none()
            if not existing_ch:
                ch = Challenge(
                    slug=ch_data["slug"],
                    title=ch_data["title"],
                    category=ch_data["category"],
                    difficulty=ch_data["difficulty"],
                    points=ch_data["points"],
                    flag=ch_data["flag"],
                    flag_hash=hash_flag(ch_data["flag"]),
                    description=ch_data["description"],
                    target_url=ch_data["target_url"],
                    hints=ch_data["hints"],
                    is_active=True,
                    solves_count=0,
                    created_at=datetime.now(timezone.utc),
                )
                db.add(ch)
                print(f"  + Added challenge: {ch_data['slug']} - {ch_data['title']} ({ch_data['points']} pts)")
            else:
                print(f"  ✓ Challenge {ch_data['slug']} already exists.")
        await db.commit()

        # 3. Seed Demo Users & some initial solves for leaderboard demonstration
        print("Seeding demo players...")
        created_users = []
        for user_data in DEMO_USERS:
            res = await db.execute(select(User).where(User.username == user_data["username"]))
            existing_u = res.scalar_one_or_none()
            if not existing_u:
                u = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    nationality=user_data["nationality"],
                    role="user",
                    score=0,
                    is_active=True,
                    created_at=datetime.now(timezone.utc),
                    last_connected_at=datetime.now(timezone.utc),
                )
                db.add(u)
                await db.commit()
                await db.refresh(u)
                created_users.append(u)
                print(f"  + Added demo player: {u.username} [{u.nationality}]")
            else:
                created_users.append(existing_u)

        # 4. Simulate a few initial solves for demo users
        web_001_res = await db.execute(select(Challenge).where(Challenge.slug == "web-001"))
        web_001 = web_001_res.scalar_one_or_none()
        web_002_res = await db.execute(select(Challenge).where(Challenge.slug == "web-002"))
        web_002 = web_002_res.scalar_one_or_none()

        if web_001 and created_users:
            for player in created_users[:3]:
                solve_check = await db.execute(
                    select(Solve).where(Solve.user_id == player.id, Solve.challenge_id == web_001.id)
                )
                if not solve_check.scalar_one_or_none():
                    solve = Solve(
                        user_id=player.id,
                        challenge_id=web_001.id,
                        points_awarded=web_001.points,
                        solved_at=datetime.now(timezone.utc),
                    )
                    db.add(solve)
                    player.score += web_001.points
                    web_001.solves_count += 1
            await db.commit()

        if web_002 and len(created_users) >= 2:
            top_player = created_users[0]
            solve_check = await db.execute(
                select(Solve).where(Solve.user_id == top_player.id, Solve.challenge_id == web_002.id)
            )
            if not solve_check.scalar_one_or_none():
                solve = Solve(
                    user_id=top_player.id,
                    challenge_id=web_002.id,
                    points_awarded=web_002.points,
                    solved_at=datetime.now(timezone.utc),
                )
                db.add(solve)
                top_player.score += web_002.points
                web_002.solves_count += 1
            await db.commit()

        print("Seeding completed successfully!")


if __name__ == "__main__":
    asyncio.run(seed())
