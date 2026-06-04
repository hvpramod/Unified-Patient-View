import asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
import structlog

from app.orchestrator import run_orchestrator, run_all_agents_for_patient
from app.agents.visit_prep import run_visit_prep
from app.orchestrator import fetch_patient_resources, save_summary, cache_summary, get_redis

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_orchestrator())
    log.info("ai_agent_service_started")
    yield
    task.cancel()


app = FastAPI(title="UPV AI Agent Service", lifespan=lifespan)


class GenerateSummaryRequest(BaseModel):
    patient_id: str
    appointment_id: str | None = None
    appointment_date: str | None = None


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ai-agent-service"}


@app.post("/internal/summaries/generate")
async def trigger_summary_generation(req: GenerateSummaryRequest):
    """Internal endpoint to trigger agent run for a patient."""
    asyncio.create_task(run_all_agents_for_patient(req.patient_id))
    return {"status": "triggered", "patient_id": req.patient_id}


@app.post("/internal/summaries/visit-prep")
async def generate_visit_prep(req: GenerateSummaryRequest):
    """Generate visit prep summary on demand (appointment-specific)."""
    resources = await fetch_patient_resources(req.patient_id)
    result = await run_visit_prep(
        req.patient_id, resources,
        appointment_id=req.appointment_id,
        appointment_date=req.appointment_date,
    )
    summary_id = await save_summary(result)
    redis = await get_redis()
    await cache_summary(redis, req.patient_id, "VISIT_PREP", {**result, "summary_id": summary_id})
    await redis.aclose()
    return {"status": "generated", "summary_id": summary_id}
