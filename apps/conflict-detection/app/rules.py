"""Rule-based conflict detection engine (R-001 through R-006)."""
from __future__ import annotations
from itertools import combinations
from typing import Any
from upv_models.conflicts import Conflict, ConflictType, ConflictSeverity, ConflictResolution


def run_all_rules(patient_id: str, fhir_resources: list[dict]) -> list[Conflict]:
    medications = [r for r in fhir_resources if r["resource_type"] in ("MedicationRequest", "MedicationStatement")]
    observations = [r for r in fhir_resources if r["resource_type"] == "Observation"]

    conflicts: list[Conflict] = []
    conflicts.extend(_r001_medication_duplicate(patient_id, medications))
    conflicts.extend(_r002_status_mismatch(patient_id, medications))
    conflicts.extend(_r003_dose_discrepancy(patient_id, medications))
    conflicts.extend(_r004_lab_discrepancy(patient_id, observations))
    return conflicts


def _r001_medication_duplicate(patient_id: str, meds: list[dict]) -> list[Conflict]:
    """R-001: Same drug name, different source, both Active."""
    conflicts = []
    active = [m for m in meds if _get_status(m) == "active"]
    for a, b in combinations(active, 2):
        if _get_source(a) == _get_source(b):
            continue
        if _drug_names_match(_get_drug_name(a), _get_drug_name(b)):
            conflicts.append(Conflict(
                patient_id=patient_id,
                conflict_type=ConflictType.MEDICATION_DUPLICATE,
                resource_type="MedicationRequest",
                resource_ids=[a["id"], b["id"]],
                severity=ConflictSeverity.MEDIUM,
                description=(
                    f"Duplicate active medication detected: '{_get_drug_name(a)}' "
                    f"appears in both {_get_source(a)} and {_get_source(b)}"
                ),
                confidence_score=0.90,
                sources=[_get_source(a), _get_source(b)],
            ))
    return conflicts


def _r002_status_mismatch(patient_id: str, meds: list[dict]) -> list[Conflict]:
    """R-002: Active in one source, Discontinued in another."""
    conflicts = []
    by_drug: dict[str, list[dict]] = {}
    for med in meds:
        key = _normalize_drug_name(_get_drug_name(med))
        by_drug.setdefault(key, []).append(med)

    for drug_name, drug_meds in by_drug.items():
        if len(drug_meds) < 2:
            continue
        statuses = {(_get_source(m), _get_status(m)) for m in drug_meds}
        has_active = any(s == "active" for _, s in statuses)
        has_discontinued = any(s in ("stopped", "cancelled") for _, s in statuses)
        if has_active and has_discontinued:
            ids = [m["id"] for m in drug_meds]
            sources = list({_get_source(m) for m in drug_meds})
            conflicts.append(Conflict(
                patient_id=patient_id,
                conflict_type=ConflictType.STATUS_MISMATCH,
                resource_type="MedicationRequest",
                resource_ids=ids,
                severity=ConflictSeverity.HIGH,
                description=(
                    f"Conflicting medication status for '{drug_name}': "
                    f"listed as Active in one source and Discontinued in another"
                ),
                confidence_score=0.95,
                sources=sources,
            ))
    return conflicts


def _r003_dose_discrepancy(patient_id: str, meds: list[dict]) -> list[Conflict]:
    """R-003: Same drug, active, dose differs by >20% across sources."""
    conflicts = []
    active = [m for m in meds if _get_status(m) == "active"]
    by_drug: dict[str, list[dict]] = {}
    for med in active:
        key = _normalize_drug_name(_get_drug_name(med))
        by_drug.setdefault(key, []).append(med)

    for drug_name, drug_meds in by_drug.items():
        if len(drug_meds) < 2:
            continue
        doses = [(_get_dose_value(m), _get_source(m), m["id"]) for m in drug_meds]
        valid_doses = [(d, s, i) for d, s, i in doses if d is not None and d > 0]
        if len(valid_doses) < 2:
            continue
        for (d1, s1, i1), (d2, s2, i2) in combinations(valid_doses, 2):
            if s1 == s2:
                continue
            pct_diff = abs(d1 - d2) / max(d1, d2)
            if pct_diff > 0.20:
                conflicts.append(Conflict(
                    patient_id=patient_id,
                    conflict_type=ConflictType.DOSE_DISCREPANCY,
                    resource_type="MedicationRequest",
                    resource_ids=[i1, i2],
                    severity=ConflictSeverity.HIGH,
                    description=(
                        f"Dose discrepancy for '{drug_name}': "
                        f"{d1} ({s1}) vs {d2} ({s2}) — {pct_diff:.0%} difference"
                    ),
                    confidence_score=0.88,
                    sources=[s1, s2],
                ))
    return conflicts


def _r004_lab_discrepancy(patient_id: str, observations: list[dict]) -> list[Conflict]:
    """R-004: Same test, same 3-day window, values differ >15% across sources."""
    from datetime import datetime, timedelta
    conflicts = []

    def get_test_code(obs: dict) -> str:
        content = obs.get("content", {})
        coding = content.get("code", {}).get("coding", [{}])
        return coding[0].get("code", "") if coding else ""

    def get_value(obs: dict) -> float | None:
        try:
            return float(obs.get("content", {}).get("valueQuantity", {}).get("value", 0) or 0) or None
        except (ValueError, TypeError):
            return None

    def get_date(obs: dict) -> datetime | None:
        try:
            from dateutil import parser
            return parser.parse(obs.get("content", {}).get("effectiveDateTime", ""))
        except Exception:
            return None

    by_code: dict[str, list[dict]] = {}
    for obs in observations:
        code = get_test_code(obs)
        if code:
            by_code.setdefault(code, []).append(obs)

    for code, obs_list in by_code.items():
        if len(obs_list) < 2:
            continue
        for a, b in combinations(obs_list, 2):
            if _get_source(a) == _get_source(b):
                continue
            da, db = get_date(a), get_date(b)
            if da and db and abs((da - db).days) > 3:
                continue
            va, vb = get_value(a), get_value(b)
            if va is None or vb is None or va == 0 or vb == 0:
                continue
            pct_diff = abs(va - vb) / max(va, vb)
            if pct_diff > 0.15:
                conflicts.append(Conflict(
                    patient_id=patient_id,
                    conflict_type=ConflictType.LAB_DISCREPANCY,
                    resource_type="Observation",
                    resource_ids=[a["id"], b["id"]],
                    severity=ConflictSeverity.MEDIUM,
                    description=(
                        f"Lab discrepancy for LOINC {code}: "
                        f"{va} ({_get_source(a)}) vs {vb} ({_get_source(b)}) — {pct_diff:.0%} difference"
                    ),
                    confidence_score=0.85,
                    sources=[_get_source(a), _get_source(b)],
                ))
    return conflicts


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_status(resource: dict) -> str:
    return resource.get("content", {}).get("status", "unknown").lower()


def _get_source(resource: dict) -> str:
    return resource.get("source_system", "unknown")


def _get_drug_name(resource: dict) -> str:
    content = resource.get("content", {})
    return (
        content.get("medicationCodeableConcept", {}).get("text", "")
        or content.get("medication", {}).get("concept", {}).get("text", "")
        or ""
    )


def _normalize_drug_name(name: str) -> str:
    import re
    return re.sub(r"\s+\d+.*$", "", name.lower().strip())


def _drug_names_match(a: str, b: str) -> bool:
    return _normalize_drug_name(a) == _normalize_drug_name(b) and bool(_normalize_drug_name(a))


def _get_dose_value(resource: dict) -> float | None:
    content = resource.get("content", {})
    dosage = content.get("dosageInstruction", [{}])
    if not dosage:
        return None
    try:
        return float(dosage[0].get("doseAndRate", [{}])[0].get("doseQuantity", {}).get("value", 0) or 0) or None
    except (IndexError, KeyError, ValueError, TypeError):
        return None
