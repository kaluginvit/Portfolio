import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

# SSL_VERIFY=false disables certificate verification (needed for corporate proxy/antivirus SSL interception)
SSL_VERIFY = os.environ.get("SSL_VERIFY", "true").lower() != "false"

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+asyncpg://screener:screener@localhost:5432/screener",
)

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
