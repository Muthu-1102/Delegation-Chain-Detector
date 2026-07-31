#!/usr/bin/env bash
set -euo pipefail

echo "[entrypoint] Waiting for database..."
python - <<'PY'
import asyncio
import sys
import time

from sqlalchemy import text
from app.db.session import engine

async def wait() -> None:
    for attempt in range(1, 31):
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            print("[entrypoint] Database is reachable.")
            return
        except Exception as exc:  # noqa: BLE001 -- deliberately broad, this is a readiness poll
            print(f"[entrypoint] DB not ready (attempt {attempt}/30): {exc}")
            time.sleep(2)
    print("[entrypoint] Database did not become reachable in time.", file=sys.stderr)
    sys.exit(1)

asyncio.run(wait())
PY

# NOTE for multi-replica deployments: if you run more than one backend
# instance, prefer running migrations as a separate one-off step in your
# deploy pipeline (e.g. `docker compose run --rm backend alembic upgrade
# head` before scaling up) rather than on every container boot, to avoid
# N replicas racing to apply the same migration simultaneously. For a
# single-instance deploy this is safe as-is.
echo "[entrypoint] Running Alembic migrations..."
alembic upgrade head

echo "[entrypoint] Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000