"""Database operations for ingestion service."""
from __future__ import annotations
from typing import Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text
import structlog

from app.config import settings
from upv_models.fhir import FHIRResource

log = structlog.get_logger()

engine = create_async_engine(settings.database_url, pool_size=10, max_overflow=5)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def upsert_fhir_resource(resource: FHIRResource) -> bool:
    """Insert or update a FHIR resource. Returns True if content changed."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            text("""
                SELECT content_hash FROM fhir_resources
                WHERE patient_id = :patient_id
                  AND resource_id = :resource_id
                  AND source_system = :source_system
                  AND resource_type = :resource_type
                ORDER BY ingested_at DESC LIMIT 1
            """),
            {
                "patient_id": resource.patient_id,
                "resource_id": resource.resource_id,
                "source_system": resource.source_system.value,
                "resource_type": resource.resource_type.value,
            },
        )
        row = result.fetchone()
        if row and row[0] == resource.content_hash:
            return False  # no change

        await session.execute(
            text("""
                INSERT INTO fhir_resources
                    (id, patient_id, resource_type, resource_id, source_system,
                     source_version, fhir_version, content, content_hash, valid_from, ingested_at)
                VALUES
                    (:id, :patient_id, :resource_type, :resource_id, :source_system,
                     :source_version, :fhir_version, :content::jsonb, :content_hash, :valid_from, NOW())
            """),
            {
                "id": resource.id,
                "patient_id": resource.patient_id,
                "resource_type": resource.resource_type.value,
                "resource_id": resource.resource_id,
                "source_system": resource.source_system.value,
                "source_version": resource.source_version,
                "fhir_version": resource.fhir_version,
                "content": resource.model_dump_json(),
                "content_hash": resource.content_hash,
                "valid_from": resource.valid_from,
            },
        )
        await session.commit()
        return True


async def get_all_patient_ids() -> list[dict]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT id, external_ids FROM patients WHERE TRUE"))
        return [{"id": str(row[0]), "external_ids": row[1] or {}} for row in result.fetchall()]
