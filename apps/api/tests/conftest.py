import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

test_database_url = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://wishlist@localhost:5433/wishlist_test",
)
test_sync_database_url = os.environ.get(
    "TEST_SYNC_DATABASE_URL",
    "postgresql+psycopg://wishlist@localhost:5433/wishlist_test",
)

# Force tests to use isolated DB so they cannot wipe local/dev tables.
os.environ["DATABASE_URL"] = test_database_url
os.environ["SYNC_DATABASE_URL"] = test_sync_database_url
os.environ.setdefault("JWT_SECRET", "test")
os.environ.setdefault("REFRESH_SECRET", "test")
os.environ.setdefault("VIEWER_TOKEN_PEPPER", "pepper")
os.environ.setdefault("WEB_ORIGIN", "http://localhost:3000")

from app.db.base import Base
from app.db.session import get_db
from app.main import app


def _ensure_test_db_exists(sync_url: str) -> None:
    target = make_url(sync_url)
    admin: URL = target.set(database="postgres")
    engine = create_engine(admin, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as conn:
            exists = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :name"),
                {"name": target.database},
            ).scalar()
            if not exists:
                conn.execute(text(f'CREATE DATABASE "{target.database}"'))
    finally:
        engine.dispose()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def test_engine():
    _ensure_test_db_exists(os.environ["SYNC_DATABASE_URL"])
    engine = create_async_engine(os.environ["DATABASE_URL"], future=True, poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine) -> AsyncSession:
    Session = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)
    async with Session() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession):
    async def override_db():
        yield db_session

    app.dependency_overrides[get_db] = override_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
