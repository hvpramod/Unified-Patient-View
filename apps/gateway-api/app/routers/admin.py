"""Admin endpoints — user management, data source health."""
from __future__ import annotations
import httpx
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog

from app.auth import CurrentUser, require_admin
from app.db import get_db
from app.config import settings

log = structlog.get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])


class CreateUserRequest(BaseModel):
    azure_oid: str
    email: str
    full_name: str
    role: str = "APC"


class UpdateUserRequest(BaseModel):
    role: str | None = None
    is_active: bool | None = None


@router.get("/users")
async def list_users(db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(require_admin)):
    result = await db.execute(text("SELECT id, azure_oid, email, full_name, role, is_active, created_at FROM users ORDER BY created_at DESC"))
    return [
        {"id": str(r[0]), "azure_oid": r[1], "email": r[2], "full_name": r[3], "role": r[4], "is_active": r[5], "created_at": str(r[6])}
        for r in result.fetchall()
    ]


@router.post("/users", status_code=201)
async def create_user(body: CreateUserRequest, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(require_admin)):
    if body.role not in ("APC", "ADMIN", "VIEWER"):
        raise HTTPException(status_code=400, detail="Invalid role")
    result = await db.execute(
        text("""
            INSERT INTO users (azure_oid, email, full_name, role, is_active)
            VALUES (:azure_oid, :email, :full_name, :role, true)
            RETURNING id
        """),
        body.model_dump(),
    )
    user_id = str(result.fetchone()[0])
    await db.commit()
    return {"id": user_id, **body.model_dump()}


@router.patch("/users/{user_id}")
async def update_user(user_id: str, body: UpdateUserRequest, db: AsyncSession = Depends(get_db), user: CurrentUser = Depends(require_admin)):
    updates = {k: v for k, v in body.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")
    set_clause = ", ".join(f"{k} = :{k}" for k in updates)
    await db.execute(text(f"UPDATE users SET {set_clause} WHERE id = :user_id::uuid"), {**updates, "user_id": user_id})
    await db.commit()
    return {"status": "updated", "user_id": user_id}


@router.get("/data-sources")
async def get_data_source_health(user: CurrentUser = Depends(require_admin)):
    """Check health of all connected source systems."""
    results = {}
    async with httpx.AsyncClient(timeout=5.0) as client:
        for name, url in [
            ("ingestion-service", f"{settings.ingestion_service_url}/health"),
            ("ai-agent-service", f"{settings.ai_agent_service_url}/health"),
        ]:
            try:
                resp = await client.get(url)
                results[name] = {"status": "ok" if resp.status_code == 200 else "degraded"}
            except Exception as e:
                results[name] = {"status": "unreachable", "error": str(e)}
    return {"services": results}


@router.post("/data-sources/{source_id}/trigger-sync")
async def trigger_sync(source_id: str, patient_id: str, user: CurrentUser = Depends(require_admin)):
    async with httpx.AsyncClient(timeout=10.0) as client:
        await client.post(
            f"{settings.ai_agent_service_url}/internal/summaries/generate",
            json={"patient_id": patient_id},
        )
    return {"status": "triggered", "patient_id": patient_id}
