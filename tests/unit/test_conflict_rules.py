"""Unit tests for conflict detection rules."""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/conflict-detection"))

from app.rules import (
    run_all_rules,
    _r001_medication_duplicate,
    _r002_status_mismatch,
    _r003_dose_discrepancy,
)
from upv_models.conflicts import ConflictType


def make_med(id, drug_name, status, source, dose_value=None):
    content = {
        "status": status,
        "medicationCodeableConcept": {"text": drug_name},
    }
    if dose_value:
        content["dosageInstruction"] = [
            {"doseAndRate": [{"doseQuantity": {"value": dose_value, "unit": "mg"}}]}
        ]
    return {
        "id": id,
        "resource_type": "MedicationRequest",
        "source_system": source,
        "content": content,
    }


def test_r001_detects_duplicate():
    meds = [
        make_med("1", "Lisinopril 10mg", "active", "athena"),
        make_med("2", "Lisinopril", "active", "healthgorilla"),
    ]
    conflicts = _r001_medication_duplicate("patient-1", meds)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.MEDICATION_DUPLICATE


def test_r001_no_duplicate_same_source():
    meds = [
        make_med("1", "Lisinopril 10mg", "active", "athena"),
        make_med("2", "Lisinopril 10mg", "active", "athena"),
    ]
    conflicts = _r001_medication_duplicate("patient-1", meds)
    assert len(conflicts) == 0


def test_r002_detects_status_mismatch():
    meds = [
        make_med("1", "Metformin", "active", "athena"),
        make_med("2", "Metformin", "stopped", "healthgorilla"),
    ]
    conflicts = _r002_status_mismatch("patient-1", meds)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.STATUS_MISMATCH
    assert conflicts[0].severity.value == "HIGH"


def test_r003_detects_dose_discrepancy():
    meds = [
        make_med("1", "Metoprolol", "active", "athena", dose_value=25.0),
        make_med("2", "Metoprolol", "active", "healthgorilla", dose_value=50.0),
    ]
    conflicts = _r003_dose_discrepancy("patient-1", meds)
    assert len(conflicts) == 1
    assert conflicts[0].conflict_type == ConflictType.DOSE_DISCREPANCY


def test_r003_no_conflict_within_threshold():
    meds = [
        make_med("1", "Metoprolol", "active", "athena", dose_value=10.0),
        make_med("2", "Metoprolol", "active", "healthgorilla", dose_value=10.5),
    ]
    conflicts = _r003_dose_discrepancy("patient-1", meds)
    assert len(conflicts) == 0


def test_run_all_rules_combines():
    meds = [
        make_med("1", "Lisinopril", "active", "athena"),
        make_med("2", "Lisinopril", "active", "healthgorilla"),
        make_med("3", "Metformin", "active", "athena"),
        make_med("4", "Metformin", "stopped", "pathway"),
    ]
    conflicts = run_all_rules("patient-1", meds)
    types = {c.conflict_type for c in conflicts}
    assert ConflictType.MEDICATION_DUPLICATE in types
    assert ConflictType.STATUS_MISMATCH in types
