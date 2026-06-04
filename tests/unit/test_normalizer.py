"""Unit tests for FHIR normalizer."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/ingestion-service"))

from app.normalizer import normalize_athena_medication, normalize_athena_lab
from upv_models.fhir import FHIRResourceType, SourceSystem


def test_normalize_athena_medication_active():
    raw = {
        "medicationid": "med-123",
        "medication": "Lisinopril 10mg",
        "medicationstatus": "ACTIVE",
        "dosage": "10mg daily",
        "route": "oral",
        "startdate": "2024-01-15",
        "rxnorm": "314076",
    }
    resource = normalize_athena_medication(raw, "patient-abc")
    assert resource.resource_type == FHIRResourceType.MEDICATION_REQUEST
    assert resource.source_system == SourceSystem.ATHENA
    assert resource.patient_id == "patient-abc"
    assert resource.content["status"] == "active"
    assert resource.content["medicationCodeableConcept"]["text"] == "Lisinopril 10mg"
    assert resource.content_hash is not None


def test_normalize_athena_medication_discontinued():
    raw = {
        "medicationid": "med-456",
        "medication": "Lisinopril 10mg",
        "medicationstatus": "DISCONTINUED",
        "dosage": "10mg daily",
        "startdate": "2023-01-01",
    }
    resource = normalize_athena_medication(raw, "patient-abc")
    assert resource.content["status"] == "stopped"


def test_normalize_athena_lab():
    raw = {
        "labresultid": "lab-789",
        "description": "HbA1c",
        "loinccode": "17856-6",
        "value": "7.4",
        "resultunit": "%",
        "flag": "H",
        "referencerange": "< 5.7%",
        "resultdatetime": "2024-03-01T10:00:00",
    }
    resource = normalize_athena_lab(raw, "patient-abc")
    assert resource.resource_type == FHIRResourceType.OBSERVATION
    assert resource.source_system == SourceSystem.ATHENA
    assert resource.content["code"]["coding"][0]["code"] == "17856-6"
    assert resource.content["interpretation"][0]["text"] == "H"


def test_content_hash_is_deterministic():
    raw = {"medicationid": "1", "medication": "Test", "medicationstatus": "ACTIVE", "startdate": "2024-01-01"}
    r1 = normalize_athena_medication(raw, "p1")
    r2 = normalize_athena_medication(raw, "p1")
    assert r1.content_hash == r2.content_hash


def test_content_hash_changes_with_content():
    raw1 = {"medicationid": "1", "medication": "Drug A", "medicationstatus": "ACTIVE", "startdate": "2024-01-01"}
    raw2 = {"medicationid": "1", "medication": "Drug B", "medicationstatus": "ACTIVE", "startdate": "2024-01-01"}
    r1 = normalize_athena_medication(raw1, "p1")
    r2 = normalize_athena_medication(raw2, "p1")
    assert r1.content_hash != r2.content_hash
