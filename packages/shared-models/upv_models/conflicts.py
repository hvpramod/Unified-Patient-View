from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class ConflictType(str, Enum):
    MEDICATION_DUPLICATE = "MEDICATION_DUPLICATE"
    STATUS_MISMATCH = "STATUS_MISMATCH"
    DOSE_DISCREPANCY = "DOSE_DISCREPANCY"
    LAB_DISCREPANCY = "LAB_DISCREPANCY"
    ALLERGY_CONFLICT = "ALLERGY_CONFLICT"
    DRUG_INTERACTION = "DRUG_INTERACTION"


class ConflictSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ConflictResolution(BaseModel):
    resolved_value: Optional[str] = None
    resolved_source: Optional[str] = None
    resolution_rationale: str
    auto_resolved: bool


class Conflict(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    conflict_type: ConflictType
    resource_type: str
    resource_ids: list[str]
    severity: ConflictSeverity
    description: str
    auto_resolved: bool = False
    resolution: Optional[ConflictResolution] = None
    confidence_score: float = Field(ge=0.0, le=1.0)
    sources: list[str]
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None
