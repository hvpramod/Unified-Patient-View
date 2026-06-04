"""Audit log query endpoint — ADMIN only."""
from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.auth import CurrentUser, require_admin
from app.db import get_db

log = structlog.get_logger()
router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("")
async def query_audit_log(
    patient_id: str | None = Query(None),
    actor_id: str | None = Query(None),
    event_type: str | None = Query(None),
    from_date: str | None = Query(None),
    to_date: str | None = Query(None),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_admin),
):
    conditions = ["1=1"]
    params: dict = {"limit": limit, "offset": offset}

    if patient_id:
        conditions.append("patient_id = :patient_id::uuid")
        params["patient_id"] = patient_id
    if actor_id:
        conditions.append("actor_id = :actor_id::uuid")
        params["actor_id"] = actor_id
    if event_type:
        conditions.append("event_type = :event_type")
        params["event_type"] = event_type
    if from_date:
        conditions.append("event_at >= :from_date::timestamptz")
        params["from_date"] = from_date
    if to_date:
        conditions.append("event_at <= :to_date::timestamptz")
        params["to_date"] = to_date

    where = " AND ".join(conditions)
    result = await db.execute(
        text(f"""
            SELECT id, event_type, actor_id, actor_role, patient_id,
                   resource_type, resource_id, payload, source_ip, event_at
            FROM audit_log
            WHERE {where}
            ORDER BY event_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.fetchall()
    return {
        "total": len(rows),
        "events": [
            {
                "id": str(row[0]),
                "event_type": row[1],
                "actor_id": str(row[2]) if row[2] else None,
                "actor_role": row[3],
                "patient_id": str(row[4]) if row[4] else None,
                "resource_type": row[5],
                "resource_id": str(row[6]) if row[6] else None,
                "payload": row[7],
                "source_ip": str(row[8]) if row[8] else None,
                "event_at": str(row[9]),
            }
            for row in rows
        ],
    }
