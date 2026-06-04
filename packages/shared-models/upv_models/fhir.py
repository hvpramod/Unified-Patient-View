from __future__ import annotations
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class SourceSystem(str, Enum):
    ATHENA = "athena"
    HEALTH_GORILLA = "healthgorilla"
    PATHWAY = "pathway"
    HOSPITAL = "hospital"
    MANUAL = "manual"


class FHIRResourceType(str, Enum):
    PATIENT = "Patient"
    MEDICATION_REQUEST = "MedicationRequest"
    MEDICATION_STATEMENT = "MedicationStatement"
    CONDITION = "Condition"
    OBSERVATION = "Observation"
    ENCOUNTER = "Encounter"
    ALLERGY_INTOLERANCE = "AllergyIntolerance"
    PROCEDURE = "Procedure"
    CARE_PLAN = "CarePlan"
    SERVICE_REQUEST = "ServiceRequest"
    DIAGNOSTIC_REPORT = "DiagnosticReport"
    DOCUMENT_REFERENCE = "DocumentReference"


class FHIRResource(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    patient_id: str
    resource_type: FHIRResourceType
    resource_id: str
    source_system: SourceSystem
    source_version: str = "1"
    fhir_version: str = "R4"
    content: dict[str, Any]
    content_hash: str
    valid_from: datetime
    valid_to: Optional[datetime] = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)


class NormalizedMedication(BaseModel):
    resource_id: str
    patient_id: str
    source_system: SourceSystem
    drug_name: str
    generic_name: Optional[str] = None
    rxnorm_code: Optional[str] = None
    dose: Optional[str] = None
    dose_value: Optional[float] = None
    dose_unit: Optional[str] = None
    frequency: Optional[str] = None
    route: Optional[str] = None
    status: str  # active | discontinued | on-hold | completed
    prescribed_date: Optional[datetime] = None
    discontinued_date: Optional[datetime] = None
    prescriber: Optional[str] = None
    raw_content: dict[str, Any]


class NormalizedLab(BaseModel):
    resource_id: str
    patient_id: str
    source_system: SourceSystem
    test_name: str
    loinc_code: Optional[str] = None
    value: Optional[float] = None
    value_string: Optional[str] = None
    unit: Optional[str] = None
    reference_range_low: Optional[float] = None
    reference_range_high: Optional[float] = None
    interpretation: Optional[str] = None  # N | H | L | HH | LL | A
    is_critical: bool = False
    collected_at: Optional[datetime] = None
    reported_at: Optional[datetime] = None
    raw_content: dict[str, Any]


class NormalizedCondition(BaseModel):
    resource_id: str
    patient_id: str
    source_system: SourceSystem
    condition_name: str
    icd10_code: Optional[str] = None
    snomed_code: Optional[str] = None
    clinical_status: str  # active | resolved | inactive
    onset_date: Optional[datetime] = None
    resolved_date: Optional[datetime] = None
    raw_content: dict[str, Any]
