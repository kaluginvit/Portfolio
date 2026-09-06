import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import app.database as db_module
import app.middleware.audit as audit_module
from app.database import DATABASE_URL
from app.main import app
from app.models.models import AgentRun, AuditRun, Dataset, Record


@pytest_asyncio.fixture(autouse=True)
async def patch_database():
    """Создаёт engine ВНУТРИ event loop текущего теста.

    asyncpg привязывает соединения к тому loop, в котором они созданы.
    Сессионный engine был бы создан в session loop, а test-функция работает
    в своём function loop — отсюда 'Future attached to a different loop'.
    Создавая engine function-scoped, мы гарантируем совпадение loops.

    audit_module.AsyncSessionLocal патчится отдельно: middleware импортирует
    его через 'from app.database import AsyncSessionLocal' (локальная копия).
    """
    test_engine = create_async_engine(DATABASE_URL, echo=False)
    test_sessions = async_sessionmaker(test_engine, expire_on_commit=False)

    db_module.engine = test_engine
    db_module.AsyncSessionLocal = test_sessions
    audit_module.AsyncSessionLocal = test_sessions

    yield test_engine

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def clean_db(patch_database):
    """Очищает все таблицы перед каждым тестом для изоляции."""
    async with AsyncSession(patch_database) as session:
        await session.execute(delete(Record))
        await session.execute(delete(AuditRun))
        await session.execute(delete(AgentRun))
        await session.execute(delete(Dataset))
        await session.commit()


@pytest_asyncio.fixture
async def client(patch_database):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def db(patch_database):
    async with AsyncSession(patch_database, expire_on_commit=False) as session:
        yield session
