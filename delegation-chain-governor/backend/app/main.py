from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.api import (
    routes_audit,
    routes_auth,
    routes_health,
    routes_logs,
    routes_query,
    routes_resolution,   # NEW
    routes_workflow,
)
  
 # NEW
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_health.router)
app.include_router(routes_auth.router)
app.include_router(routes_query.router)
app.include_router(routes_workflow.router)
app.include_router(routes_audit.router)
app.include_router(routes_logs.router)
app.include_router(routes_resolution.router) 