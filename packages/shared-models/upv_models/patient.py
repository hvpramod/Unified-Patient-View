from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from datetime import date, datetime
import uuid


class PatientIdentifier(BaseModel):
    system: str
    value: str


class Patient(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    external_ids: dict[str, str] = {}  # {"athena": "123", "healthgorilla": "456"}
    first_name: str
    last_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    mrn: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PatientSummaryCard(BaseModel):
    """Lightweight card for patient list views."""
    id: str
    full_name: str
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    mrn: Optional[str] = None
    active_conditions_count: int = 0
    active_medications_count: int = 0
    open_conflicts_count: int = 0
    last_updated: Optional[datetime] = None
