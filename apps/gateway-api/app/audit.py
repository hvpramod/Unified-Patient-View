"""Audit event emission helper."""
from __future__ import annotations
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

log = structlog.get_logger()


async def emit_audit_event(
    db: AsyncSession,
    event_type: str,
    actor_id: str,
    actor_role: str,
    patient_id: str | None,
    resource_type: str | None,
    resource_id: str | None,
    payload: dict,
    source_ip: str | None = None,
    session_id: str | None = None,
) -> None:
    try:
        await db.execute(
            text("""
                INSERT INTO audit_log
                    (event_type, actor_id, actor_role, patient_id, resource_type,
                     resource_id, payload, source_ip, session_id, event_at)
                VALUES
                    (:event_type, :actor_id::uuid, :actor_role,
                     :patient_id::uuid, :resource_type, :resource_id::uuid,
                     :payload::jsonb, :source_ip::inet, :session_id::uuid, NOW())
            """),
            {
                "event_type": event_type,
                "actor_id": actor_id or None,
                "actor_role": actor_role,
                "patient_id": patient_id or None,
                "resource_type": resource_type,
                "resource_id": resource_id or None,
                "payload": json.dumps(payload, default=str),
                "source_ip": source_ip,
                "session_id": session_id,
            },
        )
        await db.commit()
    except Exception as e:
        log.error("audit_emit_error", event_type=event_type, error=str(e))
