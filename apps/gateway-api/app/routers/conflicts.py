"""Conflict endpoints."""
from __future__ import annotations
import json
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.auth import CurrentUser, require_apc
from app.db import get_db
from app.audit import emit_audit_event

log = structlog.get_logger()
router = APIRouter(tags=["conflicts"])


class ConflictActionRequest(BaseModel):
    action: str  # ACCEPT | REJECT | ANNOTATE
    annotation: str | None = None


@router.get("/patients/{patient_id}/conflicts")
async def get_patient_conflicts(
    patient_id: str,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    result = await db.execute(
        text("""
            SELECT id, conflict_type, resource_type, resource_ids, severity,
                   description, auto_resolved, resolution, confidence_score,
                   sources, detected_at, resolved_at
            FROM conflicts
            WHERE patient_id = :patient_id
            ORDER BY
                CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 WHEN 'MEDIUM' THEN 3 ELSE 4 END,
                detected_at DESC
        """),
        {"patient_id": patient_id},
    )
    rows = result.fetchall()
    return {
        "patient_id": patient_id,
        "conflicts": [
            {
                "id": str(row[0]),
                "conflict_type": row[1],
                "resource_type": row[2],
                "severity": row[4],
                "description": row[5],
                "auto_resolved": row[6],
                "confidence_score": float(row[8] or 0),
                "sources": row[9] if isinstance(row[9], list) else json.loads(row[9] or "[]"),
                "detected_at": str(row[10]),
                "resolved_at": str(row[11]) if row[11] else None,
            }
            for row in rows
        ],
        "open_count": sum(1 for r in rows if not r[6] and not r[11]),
    }


@router.patch("/conflicts/{conflict_id}")
async def resolve_conflict(
    conflict_id: str,
    body: ConflictActionRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    if body.action not in ("ACCEPT", "REJECT", "ANNOTATE"):
        raise HTTPException(status_code=400, detail="Invalid action")

    result = await db.execute(
        text("SELECT patient_id FROM conflicts WHERE id = :id"),
        {"id": conflict_id},
    )
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Conflict not found")

    patient_id = str(row[0])

    await db.execute(
        text("""
            UPDATE conflicts
            SET resolved_at = :resolved_at,
                resolution = :resolution::jsonb
            WHERE id = :id
        """),
        {
            "id": conflict_id,
            "resolved_at": datetime.utcnow() if body.action in ("ACCEPT", "REJECT") else None,
            "resolution": json.dumps({
                "action": body.action,
                "annotation": body.annotation,
                "resolved_by": user.user_id,
                "auto_resolved": False,
            }),
        },
    )

    # Record APC action
    await db.execute(
        text("""
            INSERT INTO apc_actions (user_id, conflict_id, action_type, annotation, acted_at)
            VALUES (:user_id::uuid, :conflict_id::uuid, :action_type, :annotation, NOW())
        """),
        {
            "user_id": user.user_id,
            "conflict_id": conflict_id,
            "action_type": body.action,
            "annotation": body.annotation,
        },
    )
    await db.commit()

    await emit_audit_event(
        db=db,
        event_type=f"APC_CONFLICT_{body.action}",
        actor_id=user.user_id,
        actor_role=user.role,
        patient_id=patient_id,
        resource_type="Conflict",
        resource_id=conflict_id,
        payload={"action": body.action, "annotation": body.annotation},
    )

    return {"status": "updated", "conflict_id": conflict_id, "action": body.action}
