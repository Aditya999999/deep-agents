"""
ForgeX Deep Agent Platform — Main FastAPI Application

Entry point per spec §5. Configures CORS, mounts routers,
runs startup initialization (DB, built-in tools).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uuid

from app.core.config import settings
from app.core.logging import setup_logging, get_logger, correlation_id_var
from app.infrastructure.db.sqlite import init_db, async_session_factory
from app.application.tool_service import ToolService

from app.api.routers import health, agent_configs, tools, skills, memories, agent_stream

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    # ── Startup ──
    setup_logging(debug=settings.debug)
    logger.info("ForgeX Deep Agent Platform starting...")

    # Initialize database
    await init_db()
    logger.info("Database initialized")

    # Seed built-in tools
    async with async_session_factory() as session:
        tool_service = ToolService(session)
        await tool_service.ensure_builtin_tools()
        await session.commit()
    logger.info("Built-in tools seeded")

    logger.info(f"ForgeX ready — env={settings.app_env}, debug={settings.debug}")

    yield

    # ── Shutdown ──
    logger.info("ForgeX shutting down...")


# ── Create App ─────────────────────────────────────────────────────────────

app = FastAPI(
    title="ForgeX Deep Agent Platform",
    description="Configurable, skill-based Deep Agent with self-learning and memory",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Correlation ID Middleware ──────────────────────────────────────────────

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Attach correlation ID to every request per spec §26."""
    cid = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    correlation_id_var.set(cid)
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = cid
    return response


# ── Global Error Handler ──────────────────────────────────────────────────

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Sanitized error response per spec §23."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "correlation_id": correlation_id_var.get("unknown"),
        },
    )


# ── Mount Routers ──────────────────────────────────────────────────────────

app.include_router(health.router)
app.include_router(agent_configs.router)
app.include_router(tools.router)
app.include_router(skills.router)
app.include_router(memories.router)
app.include_router(agent_stream.router)


# ── Root ───────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {
        "name": "ForgeX Deep Agent Platform",
        "version": "1.0.0",
        "docs": "/docs",
    }
