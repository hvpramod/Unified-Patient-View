"""Kafka consumer — triggers conflict detection on patient data changes."""
from __future__ import annotations
import json
import asyncio
from aiokafka import AIOKafkaConsumer
import structlog
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import settings
from app.rules import run_all_rules

log = structlog.get_logger()

engine = create_async_engine(settings.database_url)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def fetch_patient_resources(patient_id: str) -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT id, resource_type, source_system, content, content_hash
                FROM fhir_resources
                WHERE patient_id = :patient_id
                  AND (valid_to IS NULL OR valid_to > NOW())
            """),
            {"patient_id": patient_id},
        )
        return [
            {
                "id": str(row[0]),
                "resource_type": row[1],
                "source_system": row[2],
                "content": row[3],
                "content_hash": row[4],
            }
            for row in result.fetchall()
        ]


async def save_conflicts(patient_id: str, conflicts: list) -> None:
    async with AsyncSessionLocal() as session:
        # Clear old unresolved conflicts for this patient
        await session.execute(
            text("DELETE FROM conflicts WHERE patient_id = :pid AND auto_resolved = false AND resolved_at IS NULL"),
            {"pid": patient_id},
        )
        for conflict in conflicts:
            should_auto_resolve = conflict.confidence_score >= 0.95 and conflict.severity.value in ("LOW", "MEDIUM")
            resolution = None
            if should_auto_resolve:
                resolution = json.dumps({
                    "resolution_rationale": "Auto-resolved by rule engine (high confidence)",
                    "auto_resolved": True,
                })
            await session.execute(
                text("""
                    INSERT INTO conflicts
                        (id, patient_id, conflict_type, resource_type, resource_ids,
                         severity, description, auto_resolved, resolution, confidence_score, sources, detected_at)
                    VALUES
                        (:id, :patient_id, :conflict_type, :resource_type, :resource_ids::uuid[],
                         :severity, :description, :auto_resolved, :resolution::jsonb,
                         :confidence_score, :sources::jsonb, NOW())
                """),
                {
                    "id": conflict.id,
                    "patient_id": patient_id,
                    "conflict_type": conflict.conflict_type.value,
                    "resource_type": conflict.resource_type,
                    "resource_ids": "{" + ",".join(conflict.resource_ids) + "}",
                    "severity": conflict.severity.value,
                    "description": conflict.description,
                    "auto_resolved": should_auto_resolve,
                    "resolution": resolution,
                    "confidence_score": conflict.confidence_score,
                    "sources": json.dumps(conflict.sources),
                },
            )
        await session.commit()
        log.info("conflicts_saved", patient_id=patient_id, count=len(conflicts))


async def handle_patient_updated(event: dict) -> None:
    patient_id = event.get("patient_id")
    if not patient_id:
        return
    resources = await fetch_patient_resources(patient_id)
    conflicts = run_all_rules(patient_id, resources)
    await save_conflicts(patient_id, conflicts)
    log.info("conflict_detection_complete", patient_id=patient_id, conflict_count=len(conflicts))


async def run_consumer() -> None:
    consumer = AIOKafkaConsumer(
        settings.kafka_topic_patient_updated,
        bootstrap_servers=settings.kafka_bootstrap_servers,
        group_id="conflict-detection-group",
        value_deserializer=lambda v: json.loads(v.decode()),
        auto_offset_reset="earliest",
    )
    await consumer.start()
    log.info("conflict_consumer_started")
    try:
        async for msg in consumer:
            try:
                await handle_patient_updated(msg.value)
            except Exception as e:
                log.error("conflict_consumer_error", error=str(e), msg=msg.value)
    finally:
        await consumer.stop()
