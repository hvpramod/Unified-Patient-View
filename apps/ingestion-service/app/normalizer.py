"""FHIR R4 normalizer — converts source-specific payloads to canonical FHIR resources."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from typing import Any

from upv_models.fhir import FHIRResource, FHIRResourceType, SourceSystem, NormalizedMedication, NormalizedLab


def _hash_content(content: dict[str, Any]) -> str:
    serialized = json.dumps(content, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def normalize_athena_medication(raw: dict[str, Any], patient_id: str) -> FHIRResource:
    """Convert Athena medication payload to FHIR MedicationRequest."""
    fhir_content = {
        "resourceType": "MedicationRequest",
        "id": str(raw.get("medicationid", "")),
        "status": _map_athena_med_status(raw.get("medicationstatus", "")),
        "medicationCodeableConcept": {
            "text": raw.get("medication", ""),
            "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": raw.get("rxnorm", "")}],
        },
        "dosageInstruction": [{"text": raw.get("dosage", ""), "route": {"text": raw.get("route", "")}}],
        "subject": {"reference": f"Patient/{patient_id}"},
        "authoredOn": raw.get("startdate", ""),
        "_source": {"system": "athena", "id": raw.get("medicationid", ""), "raw": raw},
    }
    return FHIRResource(
        patient_id=patient_id,
        resource_type=FHIRResourceType.MEDICATION_REQUEST,
        resource_id=str(raw.get("medicationid", "")),
        source_system=SourceSystem.ATHENA,
        content=fhir_content,
        content_hash=_hash_content(fhir_content),
        valid_from=_parse_date(raw.get("startdate")),
    )


def normalize_athena_lab(raw: dict[str, Any], patient_id: str) -> FHIRResource:
    """Convert Athena lab result to FHIR Observation."""
    value = raw.get("value")
    interpretation = _interpret_lab(raw.get("flag", ""))
    fhir_content = {
        "resourceType": "Observation",
        "id": str(raw.get("labresultid", "")),
        "status": "final",
        "code": {
            "text": raw.get("description", ""),
            "coding": [{"system": "http://loinc.org", "code": raw.get("loinccode", "")}],
        },
        "valueQuantity": {"value": value, "unit": raw.get("resultunit", "")},
        "interpretation": [{"text": interpretation}],
        "referenceRange": [{"text": raw.get("referencerange", "")}],
        "effectiveDateTime": raw.get("resultdatetime", ""),
        "subject": {"reference": f"Patient/{patient_id}"},
        "_source": {"system": "athena", "id": raw.get("labresultid", ""), "raw": raw},
    }
    return FHIRResource(
        patient_id=patient_id,
        resource_type=FHIRResourceType.OBSERVATION,
        resource_id=str(raw.get("labresultid", "")),
        source_system=SourceSystem.ATHENA,
        content=fhir_content,
        content_hash=_hash_content(fhir_content),
        valid_from=_parse_date(raw.get("resultdatetime")),
    )


def normalize_healthgorilla_resource(raw: dict[str, Any], patient_id: str) -> FHIRResource:
    """HealthGorilla already returns FHIR R4 — pass-through with source tagging."""
    resource_type_str = raw.get("resourceType", "Observation")
    try:
        resource_type = FHIRResourceType(resource_type_str)
    except ValueError:
        resource_type = FHIRResourceType.OBSERVATION

    content = {**raw, "_source": {"system": "healthgorilla", "id": raw.get("id", ""), "raw": raw}}
    return FHIRResource(
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=raw.get("id", ""),
        source_system=SourceSystem.HEALTH_GORILLA,
        content=content,
        content_hash=_hash_content(content),
        valid_from=datetime.utcnow(),
    )


def normalize_pathway_resource(raw: dict[str, Any], patient_id: str) -> FHIRResource:
    """Pathway returns FHIR-compatible — minimal normalization."""
    resource_type_str = raw.get("resourceType", "Condition")
    try:
        resource_type = FHIRResourceType(resource_type_str)
    except ValueError:
        resource_type = FHIRResourceType.CONDITION

    content = {**raw, "_source": {"system": "pathway", "id": raw.get("id", ""), "raw": raw}}
    return FHIRResource(
        patient_id=patient_id,
        resource_type=resource_type,
        resource_id=raw.get("id", ""),
        source_system=SourceSystem.PATHWAY,
        content=content,
        content_hash=_hash_content(content),
        valid_from=datetime.utcnow(),
    )


def _map_athena_med_status(status: str) -> str:
    mapping = {
        "ACTIVE": "active",
        "DISCONTINUED": "stopped",
        "DELETED": "cancelled",
        "HISTORICAL": "completed",
    }
    return mapping.get(status.upper(), "unknown")


def _interpret_lab(flag: str) -> str:
    mapping = {"H": "H", "L": "L", "HH": "HH", "LL": "LL", "A": "A", "N": "N", "": "N"}
    return mapping.get(flag.upper(), "N")


def _parse_date(date_str: Any) -> datetime:
    if not date_str:
        return datetime.utcnow()
    try:
        from dateutil import parser
        return parser.parse(str(date_str))
    except Exception:
        return datetime.utcnow()
