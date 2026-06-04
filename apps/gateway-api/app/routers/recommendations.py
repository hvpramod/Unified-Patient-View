"""APC recommendation action endpoints."""
from __future__ import annotations
import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.auth import CurrentUser, require_apc
from app.db import get_db
from app.audit import emit_audit_event

log = structlog.get_logger()
router = APIRouter(prefix="/recommendations", tags=["recommendations"])


class RecommendationActionRequest(BaseModel):
    action: str  # ACCEPT | REJECT | ANNOTATE
    annotation: str | None = None


@router.post("/{recommendation_id}/action")
async def act_on_recommendation(
    recommendation_id: str,
    body: RecommendationActionRequest,
    db: AsyncSession = Depends(get_db),
    user: CurrentUser = Depends(require_apc),
):
    if body.action not in ("ACCEPT", "REJECT", "ANNOTATE"):
        raise HTTPException(status_code=400, detail="Invalid action")

    await db.execute(
        text("""
            INSERT INTO apc_actions
                (user_id, recommendation_id, action_type, annotation, acted_at)
            VALUES
                (:user_id::uuid, :rec_id::uuid, :action_type, :annotation, NOW())
        """),
        {
            "user_id": user.user_id,
            "rec_id": recommendation_id,
            "action_type": body.action,
            "annotation": body.annotation,
        },
    )
    await db.commit()

    await emit_audit_event(
        db=db,
        event_type=f"APC_RECOMMENDATION_{body.action}",
        actor_id=user.user_id,
        actor_role=user.role,
        patient_id=None,
        resource_type="AIRecommendation",
        resource_id=recommendation_id,
        payload={"action": body.action, "annotation": body.annotation},
    )

    return {"status": "recorded", "recommendation_id": recommendation_id, "action": body.action}
