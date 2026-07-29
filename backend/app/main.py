import logging
from contextlib import asynccontextmanager
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.v1.router import api_router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from common.logging_config import configure_logging
from worker.config import get_config as get_worker_config
from worker.pipeline.orchestrator import run_cycle

settings = get_settings()
logger = configure_logging("backend")

scheduler = BackgroundScheduler()


def _run_worker_cycle() -> None:
    try:
        run_cycle()
    except Exception:
        logging.getLogger("worker").exception("Worker cycle crashed unexpectedly")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("Backend API starting", extra={"extra_fields": {"environment": settings.environment}})

    worker_config = get_worker_config()
    scheduler.add_job(
        _run_worker_cycle,
        "interval",
        minutes=worker_config.loop_interval_minutes,
        next_run_time=datetime.now(),  # fire once immediately, then on the interval
    )
    scheduler.start()
    logger.info(
        "Worker scheduler started",
        extra={"extra_fields": {"interval_minutes": worker_config.loop_interval_minutes}},
    )
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(
    title="AI News Platform — Admin API",
    version="0.1.0",
    description="Admin/config API for the news aggregation & auto-publishing platform. "
    "Public website reads go directly to Supabase (RLS-protected, anon key) — this API is admin-only.",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}
