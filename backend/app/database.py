from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from sqlalchemy import inspect, text
from app.config import settings

# Engine configuration
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENVIRONMENT == "development"),
    connect_args=connect_args,
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


def _missing_columns(sync_conn, table: str, columns: set) -> set:
    """Return the subset of `columns` not present on `table` (empty if no table)."""
    inspector = inspect(sync_conn)
    if table not in inspector.get_table_names():
        return set()
    existing = {col["name"] for col in inspector.get_columns(table)}
    return columns - existing


async def run_lightweight_migrations():
    """Additive, idempotent schema patches for tables that predate new columns.

    There is no Alembic; create_all never ALTERs an existing table. This adds the
    local-challenge metadata columns to a `challenges` table that was created by
    an older version, so deployed databases pick them up without a manual migration.
    Only ADD COLUMN is used, so it is safe and non-destructive.
    """
    is_postgres = engine.dialect.name == "postgresql"
    ts_type = "TIMESTAMP WITH TIME ZONE" if is_postgres else "TIMESTAMP"
    wanted = {"version", "repository", "path", "updated_at"}

    async with engine.begin() as conn:
        missing = await conn.run_sync(_missing_columns, "challenges", wanted)
        if not missing:
            return
        ddl = {
            "version": "ALTER TABLE challenges ADD COLUMN version VARCHAR(20)",
            "repository": "ALTER TABLE challenges ADD COLUMN repository VARCHAR(255)",
            "path": "ALTER TABLE challenges ADD COLUMN path VARCHAR(255)",
            "updated_at": f"ALTER TABLE challenges ADD COLUMN updated_at {ts_type}",
        }
        for col in ("version", "repository", "path", "updated_at"):
            if col in missing:
                await conn.execute(text(ddl[col]))
        # Backfill so NOT NULL expectations hold for existing rows.
        if "version" in missing:
            await conn.execute(text("UPDATE challenges SET version = '1.0' WHERE version IS NULL"))
        if "updated_at" in missing:
            await conn.execute(text("UPDATE challenges SET updated_at = created_at WHERE updated_at IS NULL"))


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await run_lightweight_migrations()
