"""Patient data endpoints."""
from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import redis.asyncio as aioredis
import structlog

from app.auth import CurrentUser, require_apc
from app.db import get_db, get_redis

log = structlog.get_logger()
router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("/{patient_id}")
async def get_patient(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    result = await db.execute(
        text("SELECT id, external_ids, first_name, last_name, date_of_birth, gender, mrn FROM patients WHERE id = :id"),
        {"id": patient_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Patient not found")
    return {
        "id": str(row[0]),
        "external_ids": row[1],
        "first_name": row[2],
        "last_name": row[3],
        "date_of_birth": str(row[4]) if row[4] else None,
        "gender": row[5],
        "mrn": row[6],
    }


@router.get("/{patient_id}/timeline")
async def get_patient_timeline(
    patient_id: str,
    resource_types: str | None = Query(None, description="Comma-separated FHIR resource types"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    filters = "WHERE patient_id = :patient_id AND (valid_to IS NULL OR valid_to > NOW())"
    params: dict = {"patient_id": patient_id, "limit": limit, "offset": offset}

    if resource_types:
        types = [t.strip() for t in resource_types.split(",")]
        filters += " AND resource_type = ANY(:types)"
        params["types"] = types

    result = await db.execute(
        text(f"""
            SELECT id, resource_type, source_system, content, ingested_at, valid_from
            FROM fhir_resources
            {filters}
            ORDER BY valid_from DESC NULLS LAST
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.fetchall()
    return {
        "patient_id": patient_id,
        "total": len(rows),
        "offset": offset,
        "items": [
            {
                "id": str(row[0]),
                "resource_type": row[1],
                "source_system": row[2],
                "content": row[3] if isinstance(row[3], dict) else json.loads(row[3] or "{}"),
                "ingested_at": str(row[4]),
                "valid_from": str(row[5]),
            }
            for row in rows
        ],
    }


@router.get("/{patient_id}/medications")
async def get_medications(
    patient_id: str,
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    query = """
        SELECT id, source_system, content, ingested_at
        FROM fhir_resources
        WHERE patient_id = :patient_id
          AND resource_type IN ('MedicationRequest', 'MedicationStatement')
          AND (valid_to IS NULL OR valid_to > NOW())
        ORDER BY ingested_at DESC
    """
    result = await db.execute(text(query), {"patient_id": patient_id})
    meds = []
    for row in result.fetchall():
        content = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")
        med_status = content.get("status", "unknown")
        if status and med_status != status:
            continue
        meds.append({
            "id": str(row[0]),
            "source_system": row[1],
            "drug_name": content.get("medicationCodeableConcept", {}).get("text", ""),
            "status": med_status,
            "dosage": content.get("dosageInstruction", [{}])[0].get("text", "") if content.get("dosageInstruction") else "",
            "content": content,
            "ingested_at": str(row[3]),
        })
    return {"patient_id": patient_id, "medications": meds}


@router.get("/{patient_id}/labs")
async def get_labs(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    result = await db.execute(
        text("""
            SELECT id, source_system, content, ingested_at, valid_from
            FROM fhir_resources
            WHERE patient_id = :patient_id
              AND resource_type IN ('Observation', 'DiagnosticReport')
              AND (valid_to IS NULL OR valid_to > NOW())
            ORDER BY valid_from DESC NULLS LAST
        """),
        {"patient_id": patient_id},
    )
    labs = []
    for row in result.fetchall():
        content = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")
        labs.append({
            "id": str(row[0]),
            "source_system": row[1],
            "test_name": content.get("code", {}).get("text", ""),
            "value": content.get("valueQuantity", {}).get("value"),
            "unit": content.get("valueQuantity", {}).get("unit", ""),
            "interpretation": (content.get("interpretation") or [{}])[0].get("text", ""),
            "collected_at": content.get("effectiveDateTime", str(row[4])),
            "content": content,
        })
    return {"patient_id": patient_id, "labs": labs}


@router.get("/{patient_id}/conditions")
async def get_conditions(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    result = await db.execute(
        text("""
            SELECT id, source_system, content, ingested_at
            FROM fhir_resources
            WHERE patient_id = :patient_id
              AND resource_type = 'Condition'
              AND (valid_to IS NULL OR valid_to > NOW())
            ORDER BY ingested_at DESC
        """),
        {"patient_id": patient_id},
    )
    conditions = []
    for row in result.fetchall():
        content = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")
        conditions.append({
            "id": str(row[0]),
            "source_system": row[1],
            "condition_name": content.get("code", {}).get("text", ""),
            "clinical_status": content.get("clinicalStatus", {}).get("coding", [{}])[0].get("code", ""),
            "onset_date": content.get("onsetDateTime", ""),
            "content": content,
        })
    return {"patient_id": patient_id, "conditions": conditions}
