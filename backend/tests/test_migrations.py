from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect


def test_alembic_upgrade_downgrade_and_reupgrade(tmp_path: Path, monkeypatch):
    db_path = tmp_path / "alembic_migration_test.db"
    async_url = f"sqlite+aiosqlite:///{db_path.as_posix()}"
    sync_url = f"sqlite:///{db_path.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", async_url)

    backend_dir = Path(__file__).resolve().parent.parent
    alembic_cfg = Config(str(backend_dir / "alembic.ini"))
    alembic_cfg.set_main_option("sqlalchemy.url", async_url)

    command.upgrade(alembic_cfg, "head")

    sync_engine = create_engine(sync_url)
    try:
        inspector = inspect(sync_engine)
        tables = set(inspector.get_table_names())
        assert {
            "users",
            "challenges",
            "solves",
            "submissions",
            "challenge_instances",
            "revoked_tokens",
            "alembic_version",
        }.issubset(tables)

        assert "ix_users_active_role_score" in {i["name"] for i in inspector.get_indexes("users")}
        assert "ix_challenges_active_category_difficulty" in {
            i["name"] for i in inspector.get_indexes("challenges")
        }
        assert "ix_solves_user_solved_at" in {i["name"] for i in inspector.get_indexes("solves")}
        assert "ix_submissions_user_challenge_submitted" in {
            i["name"] for i in inspector.get_indexes("submissions")
        }
        assert "ix_instance_user_challenge_status" in {
            i["name"] for i in inspector.get_indexes("challenge_instances")
        }
        assert "ix_revoked_tokens_expires_at" in {
            i["name"] for i in inspector.get_indexes("revoked_tokens")
        }
    finally:
        sync_engine.dispose()

    command.downgrade(alembic_cfg, "base")

    sync_engine_after_downgrade = create_engine(sync_url)
    try:
        inspector_down = inspect(sync_engine_after_downgrade)
        remaining_tables = set(inspector_down.get_table_names())
        for domain_table in (
            "users",
            "challenges",
            "solves",
            "submissions",
            "challenge_instances",
            "revoked_tokens",
        ):
            assert domain_table not in remaining_tables
    finally:
        sync_engine_after_downgrade.dispose()

    command.upgrade(alembic_cfg, "head")

    sync_engine_reupgraded = create_engine(sync_url)
    try:
        assert "users" in set(inspect(sync_engine_reupgraded).get_table_names())
    finally:
        sync_engine_reupgraded.dispose()
