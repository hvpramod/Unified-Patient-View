"""Kafka publisher for ingestion events."""
from __future__ import annotations
import json
from datetime import datetime
from aiokafka import AIOKafkaProducer
import structlog

from app.config import settings

log = structlog.get_logger()

_producer: AIOKafkaProducer | None = None


async def get_producer() -> AIOKafkaProducer:
    global _producer
    if _producer is None:
        _producer = AIOKafkaProducer(
            bootstrap_servers=settings.kafka_bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode(),
        )
        await _producer.start()
    return _producer


async def publish_patient_updated(patient_id: str, changed_types: list[str]) -> None:
    producer = await get_producer()
    event = {
        "event": "patient.data.updated",
        "patient_id": patient_id,
        "changed_resource_types": changed_types,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await producer.send_and_wait(settings.kafka_topic_patient_updated, event)
    log.info("kafka_published", topic=settings.kafka_topic_patient_updated, patient_id=patient_id)


async def publish_labs_new(patient_id: str, lab_resource_ids: list[str]) -> None:
    producer = await get_producer()
    event = {
        "event": "patient.labs.new",
        "patient_id": patient_id,
        "lab_resource_ids": lab_resource_ids,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await producer.send_and_wait(settings.kafka_topic_labs_new, event)


async def publish_medications_changed(patient_id: str, medication_resource_ids: list[str]) -> None:
    producer = await get_producer()
    event = {
        "event": "patient.medications.changed",
        "patient_id": patient_id,
        "medication_resource_ids": medication_resource_ids,
        "timestamp": datetime.utcnow().isoformat(),
    }
    await producer.send_and_wait(settings.kafka_topic_medications_changed, event)


async def close_producer() -> None:
    global _producer
    if _producer:
        await _producer.stop()
        _producer = None
