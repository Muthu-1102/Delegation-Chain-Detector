"""
Manual DB connectivity check.

Usage:
    DATABASE_URL=postgresql://user:pass@host:port/db python test.py

Never hardcode credentials here -- this reads from the same DATABASE_URL
env var / .env file the app itself uses (see app.core.config.Settings).
"""

from __future__ import annotations

import asyncio

from app.core.config import get_settings


async def main() -> None:
    settings = get_settings()

    # DATABASE_URL is an asyncpg SQLAlchemy URL (postgresql+asyncpg://...);
    # asyncpg.connect() wants the plain postgresql:// form.
    dsn = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://", 1)

    import asyncpg

    conn = await asyncpg.connect(dsn)
    print("Connected!")
    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())