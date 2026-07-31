"""Async SQLAlchemy engine + session factory."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# Supabase's transaction-mode pgbouncer pooler (port 6543) reuses a single
# physical connection across unrelated client sessions. asyncpg caches
# prepared statements per connection by default, which then collide across
# sessions and eventually raise "prepared statement already exists" errors.
# Disable the statement cache when talking to that pooler. If you're on
# Supabase's session pooler / direct connection (port 5432), this isn't
# needed, but it's harmless to leave on.
_connect_args = {}
if ":6543" in settings.DATABASE_URL:
    _connect_args = {"statement_cache_size": 0, "prepared_statement_cache_size": 0}

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True,
    connect_args=_connect_args,
)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session