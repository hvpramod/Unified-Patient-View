"""Summary endpoints — serve pre-generated AI summaries from Redis cache / DB."""
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
router = APIRouter(prefix="/patients", tags=["summaries"])


async def _get_summary(
    patient_id: str,
    summary_type: str,
    db: AsyncSession,
    redis: aioredis.Redis,
) -> dict:
    # Try Redis cache first (<3s guarantee)
    cache_key = f"summary:{patient_id}:{summary_type}"
    cached = await redis.get(cache_key)
    if cached:
        data = json.loads(cached)
        data["_from_cache"] = True
        return data

    # Fallback to PostgreSQL
    result = await db.execute(
        text("""
            SELECT id, model_used, content, sources, confidence_score,
                   reasoning_summary, generated_at
            FROM ai_summaries
            WHERE patient_id = :patient_id
              AND summary_type = :summary_type
              AND is_current = true
            ORDER BY generated_at DESC LIMIT 1
        """),
        {"patient_id": patient_id, "summary_type": summary_type},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"No {summary_type} summary available yet")

    content = row[2] if isinstance(row[2], dict) else json.loads(row[2] or "{}")
    return {
        "summary_id": str(row[0]),
        "patient_id": patient_id,
        "summary_type": summary_type,
        "model_used": row[1],
        "content": content,
        "sources": row[3] if isinstance(row[3], list) else json.loads(row[3] or "[]"),
        "confidence_score": float(row[4] or 0),
        "reasoning_summary": row[5],
        "generated_at": str(row[6]),
        "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        "_from_cache": False,
    }


@router.get("/{patient_id}/summary/clinical")
async def get_clinical_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: CurrentUser = Depends(require_apc),
):
    return await _get_summary(patient_id, "CLINICAL", db, redis)


@router.get("/{patient_id}/summary/medication-reconciliation")
async def get_medication_reconciliation_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: CurrentUser = Depends(require_apc),
):
    return await _get_summary(patient_id, "MEDICATION_RECONCILIATION", db, redis)


@router.get("/{patient_id}/summary/lab-intelligence")
async def get_lab_intelligence_summary(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: CurrentUser = Depends(require_apc),
):
    return await _get_summary(patient_id, "LAB_INTELLIGENCE", db, redis)


@router.get("/{patient_id}/summary/visit-prep")
async def get_visit_prep_summary(
    patient_id: str,
    appt_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    redis: aioredis.Redis = Depends(get_redis),
    user: CurrentUser = Depends(require_apc),
):
    return await _get_summary(patient_id, "VISIT_PREP", db, redis)
