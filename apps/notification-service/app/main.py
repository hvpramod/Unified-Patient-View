"""Notification service — Kafka consumer for lab events, sends Teams notifications."""
import asyncio
import json
import httpx
from aiokafka import AIOKafkaConsumer
from fastapi import FastAPI
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.teams import notify_critical_labs

log = structlog.get_logger()


async def handle_labs_event(event: dict) -> None:
    patient_id = event.get("patient_id")
    if not patient_id:
        return
    # Fetch lab intelligence summary from AI agent service
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(
                f"{settings.ai_agent_service_url}/internal/summaries/lab/{patient_id}"
            )
            if resp.status_code == 200:
                lab_summary = resp.json()
                if lab_summary.get("has_critical_values"):
                    sent = await notify_critical_labs(patient_id, lab_summary)
                    log.info("teams_notification_sent", patient_id=patient_id, sent=sent)
        except Exception as e:
            log.error("notification_fetch_error", patient_id=patient_id, error=str(e))


async def run_notification_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_labs_new,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="notification-service-group",
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    log.info("notification_consumer_started")
    try:
        async for msg in consumer:
            try:
                await handle_labs_event(msg.value)
            except Exception as e:
                log.error("notification_consumer_error", error=str(e))
    finally:
        await consumer.stop()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(run_notification_consumer())
    yield
    task.cancel()


app = FastAPI(title="UPV Notification Service", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "notification-service"}
