from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class AuditEvent(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str
    actor_id: str
    actor_role: str
    patient_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    payload: dict[str, Any]
    source_ip: Optional[str] = None
    session_id: Optional[str] = None
    event_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEventType:
    # Data events
    DATA_INGESTED = "DATA_INGESTED"
    DATA_CONFLICT_DETECTED = "DATA_CONFLICT_DETECTED"
    DATA_CONFLICT_RESOLVED = "DATA_CONFLICT_RESOLVED"
    # AI events
    AI_SUMMARY_GENERATED = "AI_SUMMARY_GENERATED"
    AI_RECOMMENDATION_CREATED = "AI_RECOMMENDATION_CREATED"
    # APC actions
    APC_RECOMMENDATION_ACCEPTED = "APC_RECOMMENDATION_ACCEPTED"
    APC_RECOMMENDATION_REJECTED = "APC_RECOMMENDATION_REJECTED"
    APC_ANNOTATION_ADDED = "APC_ANNOTATION_ADDED"
    # Writeback events
    ATHENA_WRITEBACK_INITIATED = "ATHENA_WRITEBACK_INITIATED"
    ATHENA_WRITEBACK_SUCCESS = "ATHENA_WRITEBACK_SUCCESS"
    ATHENA_WRITEBACK_FAILED = "ATHENA_WRITEBACK_FAILED"
    # Auth events
    USER_LOGIN = "USER_LOGIN"
    USER_LOGOUT = "USER_LOGOUT"
    # Notifications
    TEAMS_NOTIFICATION_SENT = "TEAMS_NOTIFICATION_SENT"
