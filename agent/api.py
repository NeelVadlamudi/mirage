"""Audit agent API: the ask, proposals and audit-log endpoints plus a health check.

    uvicorn agent.api:app --port 8000
"""

import logging
from contextlib import asynccontextmanager

import duckdb
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from agent import build_db, config, state
from agent.routes import router

logging.basicConfig(level=config.LOG_LEVEL, format="%(asctime)s %(levelname)s %(name)s %(message)s")



@asynccontextmanager
async def lifespan(app: FastAPI):
    build_db.ensure()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Mirage audit agent",
    description="Answers shelf-gap questions about the Mirage clubs and queues next steps for a person to approve.",
    version="1.0.0",
    docs_url="/docs" if config.ENABLE_API_DOCS else None,
    redoc_url="/redoc" if config.ENABLE_API_DOCS else None,
    openapi_url="/openapi.json" if config.ENABLE_API_DOCS else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key"],
)
app.include_router(router)


@app.get("/")
async def root():
    return {"name": "Mirage audit agent", "health": "/api/health", "docs": "/docs" if config.ENABLE_API_DOCS else None}


@app.get("/api/health")
async def health():
    """Liveness check (Render health check). Opens the Mirage copy read-only."""
    con = duckdb.connect(build_db.ensure(), read_only=True)
    try:
        stores = con.execute("SELECT count(*) FROM dim_store").fetchone()[0]
    finally:
        con.close()
    return {"status": "ok", "stores": stores, "proposals": len(state.list_proposals())}
