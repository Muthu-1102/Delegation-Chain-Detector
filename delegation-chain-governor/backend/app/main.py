from __future__ import annotations

import logging
import sys
import uuid

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import (
    routes_audit,
    routes_auth,
    routes_health,
    routes_logs,
    routes_query,
    routes_resolution,
    routes_workflow,
)
from app.core.config import get_settings

# Fail fast: raises RuntimeError immediately if production secrets/config
# are missing or insecure, instead of booting into a vulnerable state.
settings = get_settings()

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO if settings.ENVIRONMENT != "development" else logging.DEBUG,
    format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
)
logger = logging.getLogger("dcg")

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["x-request-id"] = request_id
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Never leak stack traces / internals to clients. Log the full exception
    server-side with the request id for correlation.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled exception on request_id=%s", request_id)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error", "request_id": request_id},
    )


app.include_router(routes_health.router)
app.include_router(routes_auth.router)
app.include_router(routes_query.router)
app.include_router(routes_workflow.router)
app.include_router(routes_audit.router)
app.include_router(routes_logs.router)
app.include_router(routes_resolution.router)