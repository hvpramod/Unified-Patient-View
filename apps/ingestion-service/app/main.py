import asyncio
import structlog
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.poller import run_poll_loop
from app.publisher import close_producer

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_poll_loop())
    log.info("ingestion_service_started")
    yield
    task.cancel()
    await close_producer()
    log.info("ingestion_service_stopped")


app = FastAPI(title="UPV Ingestion Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ingestion-service"}
