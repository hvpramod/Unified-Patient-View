import asyncio
from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog
from app.consumer import run_consumer

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_consumer())
    log.info("conflict_detection_service_started")
    yield
    task.cancel()


app = FastAPI(title="UPV Conflict Detection Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "conflict-detection"}
