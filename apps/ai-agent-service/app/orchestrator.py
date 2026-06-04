"""Agent orchestrator — Kafka consumer that triggers agent runs and caches results."""
from __future__ import annotations
import json
import asyncio
from datetime import datetime, timedelta
import redis.asyncio as aioredis
from aiokafka import AIOKafkaConsumer
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import structlog

from app.config import settings
from app.agents.clinical_summary import run_clinical_summary
from app.agents.medication_reconciliation import run_medication_reconciliation
from app.agents.lab_intelligence import run_lab_intelligence
from app.agents.visit_prep import run_visit_prep

log = structlog.get_logger()

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_redis():
    return await aioredis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)


async def fetch_patient_resources(patient_id: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, resource_type, source_system, content, content_hash
                FROM fhir_resources
                WHERE patient_id = :patient_id
                  AND (valid_to IS NULL OR valid_to > NOW())
                ORDER BY ingested_at DESC
            """),
            {"patient_id": patient_id},
        )
        return [
            {
                "id": str(row[0]),
                "resource_type": row[1],
                "source_system": row[2],
                "content": row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
            }
            for row in result.fetchall()
        ]


async def fetch_patient_conflicts(patient_id: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, conflict_type, description, severity, confidence_score
                FROM conflicts
                WHERE patient_id = :patient_id AND auto_resolved = false AND resolved_at IS NULL
            """),
            {"patient_id": patient_id},
        )
        return [
            {"id": str(row[0]), "type": row[1], "description": row[2], "severity": row[3], "confidence_score": float(row[4] or 0)}
            for row in result.fetchall()
        ]


async def save_summary(summary: dict) -> str:
    async with AsyncSessionLocal() as session:
        # Mark old summaries as not current
        await session.execute(
            text("""
                UPDATE ai_summaries SET is_current = false
                WHERE patient_id = :patient_id AND summary_type = :summary_type AND is_current = true
            """),
            {"patient_id": summary["patient_id"], "summary_type": summary["summary_type"]},
        )
        summary_id = str(__import__("uuid").uuid4())
        await session.execute(
            text("""
                INSERT INTO ai_summaries
                    (id, patient_id, summary_type, model_used, content, sources,
                     confidence_score, reasoning_summary, input_hash, expires_at, is_current)
                VALUES
                    (:id, :patient_id, :summary_type, :model_used, :content::jsonb, :sources::jsonb,
                     :confidence_score, :reasoning_summary, :input_hash, :expires_at, true)
            """),
            {
                "id": summary_id,
                "patient_id": summary["patient_id"],
                "summary_type": summary["summary_type"],
                "model_used": summary.get("model_used", "unknown"),
                "content": json.dumps(summary.get("content", {}), default=str),
                "sources": json.dumps(summary.get("sources", []), default=str),
                "confidence_score": summary.get("confidence_score", 0.0),
                "reasoning_summary": summary.get("reasoning_summary", ""),
                "input_hash": summary.get("input_hash", ""),
                "expires_at": datetime.utcnow() + timedelta(seconds=settings.summary_cache_ttl_seconds),
            },
        )
        await session.commit()
        return summary_id


async def cache_summary(redis: aioredis.Redis, patient_id: str, summary_type: str, summary: dict) -> None:
    key = f"summary:{patient_id}:{summary_type}"
    await redis.setex(key, settings.summary_cache_ttl_seconds, json.dumps(summary, default=str))


async def run_all_agents_for_patient(patient_id: str) -> None:
    log.info("agent_run_starting", patient_id=patient_id)
    resources = await fetch_patient_resources(patient_id)
    conflicts = await fetch_patient_conflicts(patient_id)
    redis = await get_redis()

    tasks = [
        run_clinical_summary(patient_id, resources),
        run_medication_reconciliation(patient_id, resources, conflicts),
        run_lab_intelligence(patient_id, resources),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, Exception):
            log.error("agent_error", patient_id=patient_id, error=str(result))
            continue
        try:
            summary_id = await save_summary(result)
            await cache_summary(redis, patient_id, result["summary_type"], {**result, "summary_id": summary_id})
            log.info("summary_cached", patient_id=patient_id, summary_type=result["summary_type"])
        except Exception as e:
            log.error("summary_save_error", error=str(e))

    await redis.aclose()


async def run_orchestrator() -> None:
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_patient_updated,
        settings.kafka_topic_labs_new,
        settings.kafka_topic_medications_changed,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="ai-agent-orchestrator-group",
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    log.info("ai_orchestrator_started")
    try:
        async for msg in consumer:
            patient_id = msg.value.get("patient_id")
            if patient_id:
                asyncio.create_task(run_all_agents_for_patient(patient_id))
    finally:
        await consumer.stop()
