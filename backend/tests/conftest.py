import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.database import Base, get_db
from app.main import app
from app.models.user import User
from app.models.challenge import Challenge
from app.services.security import hash_password, hash_flag, create_access_token

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine_test = create_async_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = async_sessionmaker(bind=engine_test, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestingSessionLocal() as session:
        yield session

    async with engine_test.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def admin_user(db_session: AsyncSession):
    admin = User(
        username="admin_test",
        email="admin@test.com",
        hashed_password=hash_password("adminpass123"),
        role="admin",
        nationality="CL",
        score=0,
        is_active=True,
    )
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    return admin


@pytest_asyncio.fixture(scope="function")
async def admin_token(admin_user: User):
    return create_access_token(admin_user.id)


@pytest_asyncio.fixture(scope="function")
async def regular_user(db_session: AsyncSession):
    user = User(
        username="player1",
        email="player1@test.com",
        hashed_password=hash_password("playerpass123"),
        role="user",
        nationality="CL",
        score=0,
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def user_token(regular_user: User):
    return create_access_token(regular_user.id)


@pytest_asyncio.fixture(scope="function")
async def sample_challenge(db_session: AsyncSession):
    ch = Challenge(
        slug="web-sample",
        title="Sample Web Challenge",
        description="Sample challenge for testing flag submission.",
        category="web",
        difficulty="EASY",
        points=100,
        flag="EclipSec{sample_flag_test}",
        flag_hash=hash_flag("EclipSec{sample_flag_test}"),
        target_url="/web-sample/",
        is_active=True,
        solves_count=0,
    )
    db_session.add(ch)
    await db_session.commit()
    await db_session.refresh(ch)
    return ch
