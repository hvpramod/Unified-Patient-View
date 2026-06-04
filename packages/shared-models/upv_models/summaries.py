from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class SummaryType(str, Enum):
    CLINICAL = "CLINICAL"
    MEDICATION_RECONCILIATION = "MEDICATION_RECONCILIATION"
    LAB_INTELLIGENCE = "LAB_INTELLIGENCE"
    VISIT_PREP = "VISIT_PREP"


class SourceReference(BaseModel):
    resource_id: str
    resource_type: str
    source_system: str
    timestamp: Optional[datetime] = None
    description: Optional[str] = None


class AIRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    recommendation_type: str
    title: str
    description: str
    action_required: bool = True
    confidence_score: float = Field(ge=0.0, le=1.0)
    sources: list[SourceReference]
    requires_clinician_review: bool = True
    fda_disclaimer: str = "Clinical Decision Support — For Clinician Review Only"


class AISummary(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    summary_type: SummaryType
    model_used: str
    model_version: str
    content: dict[str, Any]
    recommendations: list[AIRecommendation] = []
    sources: list[SourceReference]
    confidence_score: float = Field(ge=0.0, le=1.0)
    reasoning_summary: str
    input_hash: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    is_current: bool = True
    fda_disclaimer: str = "Clinical Decision Support — For Clinician Review Only"


class APCAction(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    summary_id: Optional[str] = None
    conflict_id: Optional[str] = None
    recommendation_id: Optional[str] = None
    action_type: str  # ACCEPT | REJECT | ANNOTATE
    annotation: Optional[str] = None
    acted_at: datetime = Field(default_factory=datetime.utcnow)
