"""
Generate realistic synthetic patients with full clinical data.

Usage:
    python scripts/generate_patients.py --count 20
    python scripts/generate_patients.py --count 100 --clear
    python scripts/generate_patients.py --count 5 --scenario diabetic
    python scripts/generate_patients.py --list-scenarios

Scenarios:
    diabetic       - T2DM patients with HbA1c conflicts across sources
    cardiac        - CHF / CAD patients with polypharmacy conflicts
    ckd            - Chronic Kidney Disease with lab discrepancies
    hypertensive   - Hypertension management with dose conflicts
    elderly        - 70+ multi-morbidity patients
    mixed          - Random mix of all above (default)
"""
import argparse
import hashlib
import json
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, date

import psycopg2
from psycopg2.extras import Json
from faker import Faker

fake = Faker("en_US")
random.seed(42)

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://upv:upv@localhost:5432/upv")

SOURCES = ["athena", "healthgorilla", "pathway"]
SOURCE_DISPLAY = {"athena": "Athena", "healthgorilla": "Health Gorilla", "pathway": "Pathway"}


def uid() -> str:
    return str(uuid.uuid4())


def h(content: dict) -> str:
    return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()


def rand_date(years_ago_min: int, years_ago_max: int) -> str:
    days = random.randint(years_ago_min * 365, years_ago_max * 365)
    d = date.today() - timedelta(days=days)
    return d.isoformat()


def rand_datetime(years_ago_min: int, years_ago_max: int) -> str:
    days = random.randint(years_ago_min * 365, years_ago_max * 365)
    d = datetime.utcnow() - timedelta(days=days)
    return d.isoformat() + "Z"


# ── Clinical scenario definitions ─────────────────────────────────────────────

SCENARIOS = {
    "diabetic": {
        "conditions": [
            {"text": "Type 2 Diabetes Mellitus", "icd10": "E11.9"},
            {"text": "Hypertension", "icd10": "I10"},
            {"text": "Hyperlipidemia", "icd10": "E78.5"},
        ],
        "medications": [
            {"name": "Metformin 1000mg", "rxnorm": "861007", "dose": "1000mg twice daily", "statuses": ["active", "active"]},
            {"name": "Glipizide 5mg",    "rxnorm": "310488", "dose": "5mg daily",          "statuses": ["active", "stopped"]},  # conflict
            {"name": "Lisinopril 10mg",  "rxnorm": "314076", "dose": "10mg daily",          "statuses": ["active", "active"]},
            {"name": "Atorvastatin 40mg","rxnorm": "617312", "dose": "40mg at bedtime",      "statuses": ["active", "active"]},
        ],
        "labs": [
            {"name": "HbA1c",     "loinc": "17856-6", "units": "%",          "values": [(7.2, 8.4),  (6.8, 9.1)], "flag": "H"},
            {"name": "Glucose",   "loinc": "2345-7",  "units": "mg/dL",      "values": [(110, 310),  (95,  280)], "flag": "H"},
            {"name": "Creatinine","loinc": "2160-0",  "units": "mg/dL",      "values": [(0.9, 1.5),  (0.8, 1.4)], "flag": "N"},
        ],
        "age_range": (45, 75),
    },
    "cardiac": {
        "conditions": [
            {"text": "Congestive Heart Failure", "icd10": "I50.9"},
            {"text": "Coronary Artery Disease",  "icd10": "I25.10"},
            {"text": "Atrial Fibrillation",      "icd10": "I48.91"},
            {"text": "Hypertension",             "icd10": "I10"},
        ],
        "medications": [
            {"name": "Metoprolol Succinate 50mg","rxnorm": "866514", "dose": "50mg daily",   "statuses": ["active", "active"]},
            {"name": "Furosemide 40mg",          "rxnorm": "310429", "dose": "40mg daily",   "statuses": ["active", "stopped"]},  # conflict
            {"name": "Warfarin 5mg",             "rxnorm": "855332", "dose": "5mg daily",    "statuses": ["active", "active"]},
            {"name": "Lisinopril 20mg",          "rxnorm": "314077", "dose": "20mg daily",   "statuses": ["active", "active"]},
            {"name": "Spironolactone 25mg",      "rxnorm": "313988", "dose": "25mg daily",   "statuses": ["active", "active"]},
        ],
        "labs": [
            {"name": "BNP",          "loinc": "42637-9", "units": "pg/mL",     "values": [(200, 1200), (150, 900)], "flag": "H"},
            {"name": "Troponin T",   "loinc": "6598-7",  "units": "ng/mL",     "values": [(0.01, 0.15),(0.01,0.12)], "flag": "A"},
            {"name": "INR",          "loinc": "6301-6",  "units": "",          "values": [(1.8, 3.5),  (2.0, 3.2)], "flag": "N"},
            {"name": "Potassium",    "loinc": "2823-3",  "units": "mEq/L",     "values": [(3.5, 5.5),  (3.4, 5.6)], "flag": "H"},
        ],
        "age_range": (55, 80),
    },
    "ckd": {
        "conditions": [
            {"text": "Chronic Kidney Disease Stage 3b", "icd10": "N18.3"},
            {"text": "Type 2 Diabetes Mellitus",        "icd10": "E11.9"},
            {"text": "Hypertension",                    "icd10": "I10"},
            {"text": "Anemia of Chronic Disease",       "icd10": "D63.1"},
        ],
        "medications": [
            {"name": "Metformin 500mg",  "rxnorm": "861007", "dose": "500mg daily",  "statuses": ["active", "stopped"]},  # conflict — renally dosed
            {"name": "Amlodipine 5mg",   "rxnorm": "197361", "dose": "5mg daily",    "statuses": ["active", "active"]},
            {"name": "Erythropoietin",   "rxnorm": "1310158","dose": "4000 units/wk","statuses": ["active", "active"]},
            {"name": "Ferrous Sulfate",  "rxnorm": "310325", "dose": "325mg TID",    "statuses": ["active", "active"]},
        ],
        "labs": [
            {"name": "eGFR (CKD-EPI)",  "loinc": "62238-1", "units": "mL/min/1.73m²","values": [(25, 45),  (20, 40)], "flag": "L"},
            {"name": "Creatinine",      "loinc": "2160-0",  "units": "mg/dL",          "values": [(2.0, 4.0),(2.2, 4.5)], "flag": "H"},
            {"name": "Hemoglobin",      "loinc": "718-7",   "units": "g/dL",           "values": [(8.0, 11.0),(7.5,10.5)], "flag": "L"},
            {"name": "Potassium",       "loinc": "2823-3",  "units": "mEq/L",          "values": [(4.5, 6.5),(4.8, 6.8)], "flag": "H"},
            {"name": "Phosphorus",      "loinc": "2777-1",  "units": "mg/dL",          "values": [(4.0, 7.0),(3.8, 7.2)], "flag": "H"},
        ],
        "age_range": (50, 80),
    },
    "hypertensive": {
        "conditions": [
            {"text": "Essential Hypertension",       "icd10": "I10"},
            {"text": "Hyperlipidemia",               "icd10": "E78.5"},
            {"text": "Obesity",                      "icd10": "E66.01"},
        ],
        "medications": [
            {"name": "Amlodipine 10mg",    "rxnorm": "197380", "dose": "10mg daily",    "statuses": ["active", "active"]},
            {"name": "Lisinopril 10mg",    "rxnorm": "314076", "dose": "10mg daily",    "statuses": ["active", "stopped"]},  # conflict
            {"name": "Hydrochlorothiazide 25mg","rxnorm":"310798","dose":"25mg daily",  "statuses": ["active", "active"]},
            {"name": "Atorvastatin 20mg",  "rxnorm": "617310", "dose": "20mg daily",   "statuses": ["active", "active"]},
        ],
        "labs": [
            {"name": "Sodium",    "loinc": "2951-2",  "units": "mEq/L",  "values": [(132, 148),(130, 145)], "flag": "N"},
            {"name": "Potassium", "loinc": "2823-3",  "units": "mEq/L",  "values": [(3.0, 4.5),(2.9, 4.4)], "flag": "L"},
            {"name": "LDL",       "loinc": "13457-7", "units": "mg/dL",  "values": [(100, 190),(95,  185)], "flag": "H"},
            {"name": "HDL",       "loinc": "2085-9",  "units": "mg/dL",  "values": [(30,  65), (28,  60)],  "flag": "L"},
        ],
        "age_range": (40, 70),
    },
    "elderly": {
        "conditions": [
            {"text": "Type 2 Diabetes Mellitus",  "icd10": "E11.9"},
            {"text": "Hypertension",              "icd10": "I10"},
            {"text": "Osteoarthritis",            "icd10": "M15.9"},
            {"text": "Hypothyroidism",            "icd10": "E03.9"},
            {"text": "Atrial Fibrillation",       "icd10": "I48.91"},
            {"text": "Osteoporosis",              "icd10": "M81.0"},
        ],
        "medications": [
            {"name": "Metformin 500mg",   "rxnorm": "861007", "dose": "500mg daily",   "statuses": ["active", "active"]},
            {"name": "Levothyroxine 50mcg","rxnorm":"966226", "dose": "50mcg daily",    "statuses": ["active", "active"]},
            {"name": "Warfarin 2.5mg",    "rxnorm": "855316", "dose": "2.5mg daily",   "statuses": ["active", "active"]},
            {"name": "Omeprazole 20mg",   "rxnorm": "402014", "dose": "20mg daily",    "statuses": ["active", "stopped"]},  # conflict
            {"name": "Alendronate 70mg",  "rxnorm": "548503", "dose": "70mg weekly",   "statuses": ["active", "active"]},
            {"name": "Calcium 500mg",     "rxnorm": "1156253","dose": "500mg twice daily","statuses": ["active", "active"]},
        ],
        "labs": [
            {"name": "TSH",        "loinc": "3016-3",  "units": "mIU/L",  "values": [(0.4, 8.0),(0.3, 7.5)], "flag": "H"},
            {"name": "INR",        "loinc": "6301-6",  "units": "",       "values": [(1.5, 4.0),(1.6, 3.8)], "flag": "H"},
            {"name": "HbA1c",      "loinc": "17856-6", "units": "%",      "values": [(6.5, 8.5),(6.3, 8.8)], "flag": "H"},
            {"name": "Vitamin D",  "loinc": "1989-3",  "units": "ng/mL",  "values": [(8, 25),   (7, 22)],    "flag": "L"},
            {"name": "Calcium",    "loinc": "17861-6", "units": "mg/dL",  "values": [(8.5,10.5),(8.3,10.2)], "flag": "N"},
        ],
        "age_range": (70, 90),
    },
}


def make_patient(scenario_name: str) -> dict:
    scenario = SCENARIOS[scenario_name]
    age_min, age_max = scenario["age_range"]
    dob = date.today() - timedelta(days=random.randint(age_min * 365, age_max * 365))
    gender = random.choice(["Male", "Female", "Female"])  # slight female skew
    if gender == "Female":
        name = (fake.first_name_female(), fake.last_name())
    else:
        name = (fake.first_name_male(), fake.last_name())

    return {
        "id": uid(),
        "external_ids": {
            "athena": f"AT-{random.randint(100000, 999999)}",
            "healthgorilla": f"HG-{random.randint(100000, 999999)}",
        },
        "first_name": name[0],
        "last_name": name[1],
        "date_of_birth": dob.isoformat(),
        "gender": gender,
        "mrn": f"MRN-{random.randint(100000, 999999)}",
        "_scenario": scenario_name,
    }


def make_fhir_resources(patient_id: str, scenario_name: str) -> list[dict]:
    scenario = SCENARIOS[scenario_name]
    resources = []
    primary_source = random.choice(["athena", "healthgorilla"])
    secondary_source = random.choice([s for s in SOURCES if s != primary_source])

    # ── Conditions ────────────────────────────────────────────────────────
    for cond in scenario["conditions"]:
        onset = rand_datetime(3, 10)
        resources.append({
            "id": uid(), "resource_type": "Condition",
            "resource_id": f"cond-{uid()[:8]}", "source_system": primary_source,
            "content": {
                "resourceType": "Condition",
                "clinicalStatus": {"coding": [{"code": "active"}]},
                "code": {"text": cond["text"], "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": cond["icd10"]}]},
                "subject": {"reference": f"Patient/{patient_id}"},
                "onsetDateTime": onset,
                "_source": {"system": primary_source},
            },
            "valid_from": onset,
        })

    # ── Medications ────────────────────────────────────────────────────────
    for med in scenario["medications"]:
        authored = rand_datetime(1, 5)
        status_a = med["statuses"][0]
        status_b = med["statuses"][1]
        is_conflict = status_a != status_b

        # Primary source
        resources.append({
            "id": uid(), "resource_type": "MedicationRequest",
            "resource_id": f"med-{primary_source}-{uid()[:8]}", "source_system": primary_source,
            "content": {
                "resourceType": "MedicationRequest",
                "status": status_a,
                "medicationCodeableConcept": {
                    "text": med["name"],
                    "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": med["rxnorm"]}],
                },
                "dosageInstruction": [{"text": med["dose"]}],
                "subject": {"reference": f"Patient/{patient_id}"},
                "authoredOn": authored,
                "_source": {"system": primary_source},
            },
            "valid_from": authored,
        })

        # Secondary source (always present for conflict scenarios)
        if is_conflict or random.random() > 0.4:
            resources.append({
                "id": uid(), "resource_type": "MedicationStatement",
                "resource_id": f"med-{secondary_source}-{uid()[:8]}", "source_system": secondary_source,
                "content": {
                    "resourceType": "MedicationStatement",
                    "status": status_b,
                    "medicationCodeableConcept": {
                        "text": med["name"],
                        "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": med["rxnorm"]}],
                    },
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "effectiveDateTime": authored,
                    "_source": {"system": secondary_source},
                },
                "valid_from": authored,
            })

    # ── Lab Results (3 time points each) ──────────────────────────────────
    for lab in scenario["labs"]:
        lo, hi = lab["values"][0]
        lo2, hi2 = lab["values"][1]
        dates = sorted([rand_datetime(0, 1), rand_datetime(0, 1), rand_datetime(0, 1)])
        val_a = round(random.uniform(lo, hi), 1)
        val_b = round(random.uniform(lo2, hi2), 1)

        # Primary source result
        resources.append({
            "id": uid(), "resource_type": "Observation",
            "resource_id": f"lab-{primary_source}-{uid()[:8]}", "source_system": primary_source,
            "content": {
                "resourceType": "Observation", "status": "final",
                "code": {"text": lab["name"], "coding": [{"system": "http://loinc.org", "code": lab["loinc"]}]},
                "valueQuantity": {"value": val_a, "unit": lab["units"]},
                "interpretation": [{"text": lab["flag"]}],
                "effectiveDateTime": dates[-1],
                "subject": {"reference": f"Patient/{patient_id}"},
                "_source": {"system": primary_source},
            },
            "valid_from": dates[-1],
        })

        # Secondary source result (introduces lab discrepancy if >15% diff)
        if abs(val_a - val_b) / max(val_a, val_b if val_b > 0 else 0.001) > 0.05 or random.random() > 0.5:
            resources.append({
                "id": uid(), "resource_type": "Observation",
                "resource_id": f"lab-{secondary_source}-{uid()[:8]}", "source_system": secondary_source,
                "content": {
                    "resourceType": "Observation", "status": "final",
                    "code": {"text": lab["name"], "coding": [{"system": "http://loinc.org", "code": lab["loinc"]}]},
                    "valueQuantity": {"value": val_b, "unit": lab["units"]},
                    "interpretation": [{"text": lab["flag"]}],
                    "effectiveDateTime": dates[-1],
                    "subject": {"reference": f"Patient/{patient_id}"},
                    "_source": {"system": secondary_source},
                },
                "valid_from": dates[-1],
            })

    # ── Encounters ────────────────────────────────────────────────────────
    for _ in range(random.randint(1, 3)):
        start = rand_datetime(0, 2)
        resources.append({
            "id": uid(), "resource_type": "Encounter",
            "resource_id": f"enc-{uid()[:8]}", "source_system": random.choice(SOURCES),
            "content": {
                "resourceType": "Encounter", "status": "finished",
                "class": {"code": random.choice(["AMB", "IMP"]), "display": random.choice(["ambulatory", "inpatient"])},
                "type": [{"text": random.choice(["Office visit", "Follow-up", "Urgent care", "Specialist consult"])}],
                "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": start, "end": start},
                "_source": {"system": random.choice(SOURCES)},
            },
            "valid_from": start,
        })

    return resources


def detect_conflicts(patient_id: str, resources: list[dict]) -> list[dict]:
    """Rule-based conflict detection matching production rules."""
    conflicts = []
    meds = [r for r in resources if r["resource_type"] in ("MedicationRequest", "MedicationStatement")]
    labs = [r for r in resources if r["resource_type"] == "Observation"]

    # Group meds by normalized drug name
    by_drug: dict[str, list] = {}
    for med in meds:
        name = med["content"].get("medicationCodeableConcept", {}).get("text", "").lower()
        import re
        key = re.sub(r"\s+\d+.*$", "", name)
        by_drug.setdefault(key, []).append(med)

    for drug_name, drug_meds in by_drug.items():
        if len(drug_meds) < 2:
            continue
        sources = list({m["source_system"] for m in drug_meds})
        if len(sources) < 2:
            continue

        statuses = {m["content"].get("status", "unknown") for m in drug_meds}
        active = any(s == "active" for s in statuses)
        stopped = any(s in ("stopped", "cancelled") for s in statuses)

        if active and stopped:
            # STATUS_MISMATCH
            conflicts.append({
                "id": uid(), "patient_id": patient_id,
                "conflict_type": "STATUS_MISMATCH", "resource_type": "MedicationRequest",
                "resource_ids": [m["id"] for m in drug_meds],
                "severity": "HIGH",
                "description": f"Conflicting medication status for '{drug_name.title()}': active in {sources[0]} but discontinued in {sources[1]}.",
                "auto_resolved": False, "confidence_score": 0.93, "sources": sources,
            })
        elif active and len(sources) >= 2:
            # MEDICATION_DUPLICATE
            conflicts.append({
                "id": uid(), "patient_id": patient_id,
                "conflict_type": "MEDICATION_DUPLICATE", "resource_type": "MedicationRequest",
                "resource_ids": [m["id"] for m in drug_meds],
                "severity": "MEDIUM",
                "description": f"'{drug_name.title()}' appears as active in multiple sources: {', '.join(sources)}.",
                "auto_resolved": False, "confidence_score": 0.87, "sources": sources,
            })

    # Lab discrepancy
    by_loinc: dict[str, list] = {}
    for lab in labs:
        loinc = (lab["content"].get("code", {}).get("coding", [{}])[0]).get("code", "")
        if loinc:
            by_loinc.setdefault(loinc, []).append(lab)

    for loinc, obs_list in by_loinc.items():
        sources = list({o["source_system"] for o in obs_list})
        if len(sources) < 2:
            continue
        values = []
        for obs in obs_list:
            v = obs["content"].get("valueQuantity", {}).get("value")
            if v:
                values.append((float(v), obs["source_system"], obs["id"]))
        if len(values) >= 2:
            vals = [v for v, _, _ in values]
            pct_diff = (max(vals) - min(vals)) / max(vals) if max(vals) > 0 else 0
            if pct_diff > 0.15:
                test_name = obs_list[0]["content"].get("code", {}).get("text", loinc)
                conflicts.append({
                    "id": uid(), "patient_id": patient_id,
                    "conflict_type": "LAB_DISCREPANCY", "resource_type": "Observation",
                    "resource_ids": [o["id"] for o in obs_list],
                    "severity": "MEDIUM" if pct_diff < 0.3 else "HIGH",
                    "description": f"Lab discrepancy for {test_name}: {vals[0]} ({sources[0]}) vs {vals[1]} ({sources[1]}) — {pct_diff:.0%} difference.",
                    "auto_resolved": False, "confidence_score": round(0.80 + random.uniform(0, 0.12), 2),
                    "sources": sources,
                })

    return conflicts


def make_ai_summary(patient_id: str, summary_type: str, resources: list[dict], conflicts: list[dict]) -> dict:
    """Generate a realistic pre-computed AI summary for a patient."""
    conditions = [r for r in resources if r["resource_type"] == "Condition"]
    meds = [r for r in resources if r["resource_type"] in ("MedicationRequest", "MedicationStatement") and r["content"].get("status") == "active"]
    labs = [r for r in resources if r["resource_type"] == "Observation"]
    sources = list({r["source_system"] for r in resources})

    cond_names = [r["content"].get("code", {}).get("text", "") for r in conditions]
    active_med_names = [r["content"].get("medicationCodeableConcept", {}).get("text", "") for r in meds]
    conflict_count = len(conflicts)

    content: dict = {}

    if summary_type == "CLINICAL":
        content = {
            "patient_overview": (
                f"Patient presents with {len(cond_names)} active conditions including "
                f"{', '.join(cond_names[:2])}. "
                f"Currently on {len(active_med_names)} active medications. "
                f"{conflict_count} clinical conflict{'s' if conflict_count != 1 else ''} detected across source systems requiring reconciliation."
            ),
            "active_conditions": [
                {"condition": r["content"].get("code", {}).get("text", ""), "icd10": r["content"].get("code", {}).get("coding", [{}])[0].get("code", ""), "status": "active", "source": SOURCE_DISPLAY.get(r["source_system"], r["source_system"])}
                for r in conditions
            ],
            "care_gaps": _generate_care_gaps(cond_names),
            "risk_flags": _generate_risk_flags(conflicts, cond_names),
            "open_tasks": _generate_open_tasks(conflicts),
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        }
    elif summary_type == "MEDICATION_RECONCILIATION":
        med_conflicts = [c for c in conflicts if c["conflict_type"] in ("STATUS_MISMATCH", "MEDICATION_DUPLICATE")]
        content = {
            "reconciled_medications": [
                {
                    "drug_name": r["content"].get("medicationCodeableConcept", {}).get("text", ""),
                    "recommended_status": r["content"].get("status", "active"),
                    "recommended_dose": (r["content"].get("dosageInstruction") or [{}])[0].get("text", "As directed"),
                    "rationale": f"Consistent record in {SOURCE_DISPLAY.get(r['source_system'], r['source_system'])}. No conflicts detected.",
                    "sources_used": [r["source_system"]],
                    "confidence_score": round(0.90 + random.uniform(0, 0.08), 2),
                    "requires_clinician_review": False,
                }
                for r in meds[:6]
            ],
            "unresolved_conflicts": [
                {"conflict_description": c["description"], "severity": c["severity"], "recommended_action": "Verify with patient and reconcile across systems."}
                for c in med_conflicts[:3]
            ],
            "overall_confidence_score": round(0.85 + random.uniform(0, 0.10), 2),
            "reasoning_summary": f"Reconciliation across {len(sources)} source systems. {len(med_conflicts)} medication conflicts detected.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        }
    elif summary_type == "LAB_INTELLIGENCE":
        lab_conflicts = [c for c in conflicts if c["conflict_type"] == "LAB_DISCREPANCY"]
        critical_labs = [r for r in labs if r["content"].get("interpretation", [{}])[0].get("text", "") in ("HH", "LL", "H", "L")]
        content = {
            "critical_values": [
                {
                    "test_name": r["content"].get("code", {}).get("text", ""),
                    "value": str(r["content"].get("valueQuantity", {}).get("value", "")),
                    "unit": r["content"].get("valueQuantity", {}).get("unit", ""),
                    "interpretation": r["content"].get("interpretation", [{}])[0].get("text", ""),
                    "clinical_significance": f"Abnormal value requiring clinical review.",
                    "recommended_action": "Review and consider clinical intervention.",
                    "source": SOURCE_DISPLAY.get(r["source_system"], r["source_system"]),
                    "collected_at": r["valid_from"][:10] if r.get("valid_from") else "",
                }
                for r in critical_labs[:3]
            ],
            "trends": _generate_lab_trends(labs),
            "abnormal_values": [
                {"test_name": r["content"].get("code", {}).get("text", ""), "value": f"{r['content'].get('valueQuantity', {}).get('value', '')} {r['content'].get('valueQuantity', {}).get('unit', '')}", "expected_range": "See reference range", "significance": "Requires monitoring"}
                for r in critical_labs[:4]
            ],
            "summary_narrative": f"{len(critical_labs)} abnormal lab values detected. {len(lab_conflicts)} inter-source discrepancies identified.",
            "overall_confidence_score": round(0.85 + random.uniform(0, 0.10), 2),
            "reasoning_summary": f"Lab analysis across {len(sources)} sources. {len(lab_conflicts)} discrepancies flagged.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        }
    elif summary_type == "VISIT_PREP":
        high_conflicts = [c for c in conflicts if c["severity"] in ("CRITICAL", "HIGH")]
        content = {
            "visit_brief": (
                f"Patient presents with {len(cond_names)} active conditions. "
                f"Key agenda items: {len(high_conflicts)} high-priority conflicts require reconciliation. "
                f"Review recent labs and medication changes."
            ),
            "priority_issues": [
                {"issue": c["description"][:80], "priority": c["severity"], "background": f"Detected between {', '.join(c['sources'])}."}
                for c in conflicts[:3]
            ],
            "risk_alerts": [
                {"alert": c["description"][:100], "severity": c["severity"], "rationale": f"Conflict between {', '.join(c['sources'])}", "recommended_action": "Verify with patient and reconcile."}
                for c in high_conflicts[:3]
            ],
            "suggested_questions": _generate_suggested_questions(cond_names, conflicts),
            "follow_up_recommendations": _generate_followups(cond_names),
            "pending_labs_or_referrals": [f"Follow-up on {c['content'].get('code', {}).get('text', 'lab')} discrepancy" for c in labs[:2]],
            "overall_confidence_score": round(0.82 + random.uniform(0, 0.12), 2),
            "reasoning_summary": f"Visit prep for patient with {len(cond_names)} conditions and {len(conflicts)} open conflicts.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        }

    model = random.choice(["openai/gpt-4o", "claude/claude-sonnet-4-6"])
    return {
        "id": uid(),
        "patient_id": patient_id,
        "summary_type": summary_type,
        "model_used": model,
        "model_version": "2024-08-06",
        "confidence_score": content.pop("overall_confidence_score", round(0.85 + random.uniform(0, 0.10), 2)),
        "reasoning_summary": content.pop("reasoning_summary", "AI-generated summary."),
        "input_hash": h({"patient_id": patient_id, "summary_type": summary_type}),
        "content": content,
        "sources": [{"source_system": s} for s in sources],
    }


def _generate_care_gaps(cond_names: list[str]) -> list[dict]:
    gaps = []
    if any("diabetes" in c.lower() for c in cond_names):
        gaps.append({"gap": "HbA1c monitoring overdue (>3 months)", "priority": "HIGH", "recommendation": "Order HbA1c and review glycemic targets."})
        gaps.append({"gap": "Annual diabetic eye exam pending", "priority": "MEDIUM", "recommendation": "Refer to ophthalmology."})
    if any("hypertension" in c.lower() for c in cond_names):
        gaps.append({"gap": "Blood pressure follow-up needed", "priority": "MEDIUM", "recommendation": "Home BP monitoring and medication review."})
    if any("ckd" in c.lower() or "kidney" in c.lower() for c in cond_names):
        gaps.append({"gap": "Nephrology referral outstanding", "priority": "HIGH", "recommendation": "Refer to nephrology for CKD management."})
    if not gaps:
        gaps.append({"gap": "Preventive care review due", "priority": "LOW", "recommendation": "Schedule annual wellness visit."})
    return gaps[:4]


def _generate_risk_flags(conflicts: list[dict], cond_names: list[str]) -> list[dict]:
    flags = []
    for c in conflicts[:2]:
        flags.append({"flag": c["description"][:120], "severity": c["severity"], "rationale": f"Detected between {', '.join(c['sources'])}."})
    if any("cardiac" in c.lower() or "heart" in c.lower() or "fibrillation" in c.lower() for c in cond_names):
        flags.append({"flag": "Cardiac condition requires anticoagulation monitoring", "severity": "HIGH", "rationale": "INR/bleeding risk in atrial fibrillation."})
    return flags[:4]


def _generate_open_tasks(conflicts: list[dict]) -> list[dict]:
    tasks = [{"task": "Reconcile medication conflicts", "due_date": "This visit", "assigned_to": "APC"}] if conflicts else []
    tasks.append({"task": "Review lab discrepancies with patient", "due_date": "This visit", "assigned_to": "APC"})
    tasks.append({"task": "Update medication list in Athena", "due_date": "Today", "assigned_to": "APC"})
    return tasks[:3]


def _generate_lab_trends(labs: list[dict]) -> list[dict]:
    trends = []
    seen = set()
    for lab in labs:
        name = lab["content"].get("code", {}).get("text", "")
        if name and name not in seen:
            seen.add(name)
            val = lab["content"].get("valueQuantity", {}).get("value", 0)
            unit = lab["content"].get("valueQuantity", {}).get("unit", "")
            trends.append({
                "test_name": name,
                "trend_direction": random.choice(["INCREASING", "DECREASING", "STABLE"]),
                "values": [{"value": round(val * random.uniform(0.85, 1.0), 1), "date": rand_date(0, 1), "source": lab["source_system"]}],
                "clinical_implication": f"Monitor {name} at next visit.",
            })
        if len(trends) >= 4:
            break
    return trends


def _generate_suggested_questions(cond_names: list[str], conflicts: list[dict]) -> list[dict]:
    questions = []
    if conflicts:
        questions.append({"question": f"Can you describe your current medication routine?", "rationale": "Verify which medications patient is actually taking.", "related_condition": "Medication reconciliation"})
    if any("diabetes" in c.lower() for c in cond_names):
        questions.append({"question": "How have your blood sugar readings been at home?", "rationale": "Assess glycemic control between visits.", "related_condition": "Type 2 Diabetes"})
    if any("hypertension" in c.lower() for c in cond_names):
        questions.append({"question": "Have you been monitoring your blood pressure at home?", "rationale": "Assess BP control and medication adherence.", "related_condition": "Hypertension"})
    questions.append({"question": "Have you had any new symptoms or side effects from your medications?", "rationale": "Identify adverse effects.", "related_condition": "Medication safety"})
    return questions[:4]


def _generate_followups(cond_names: list[str]) -> list[dict]:
    followups = []
    followups.append({"recommendation": "Update medication list and reconcile across all source systems", "timeframe": "Today", "rationale": "Medication conflicts detected"})
    if any("diabetes" in c.lower() for c in cond_names):
        followups.append({"recommendation": "Order HbA1c in 3 months", "timeframe": "3 months", "rationale": "Glycemic monitoring"})
    if any("ckd" in c.lower() or "kidney" in c.lower() for c in cond_names):
        followups.append({"recommendation": "Nephrology referral", "timeframe": "Within 4 weeks", "rationale": "CKD progression monitoring"})
    followups.append({"recommendation": "Follow-up visit in 4–6 weeks", "timeframe": "4-6 weeks", "rationale": "Monitor treatment response"})
    return followups[:4]


# ── Database operations ────────────────────────────────────────────────────────

def insert_patient(cur, patient: dict) -> None:
    cur.execute("""
        INSERT INTO patients (id, external_ids, first_name, last_name, date_of_birth, gender, mrn)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name  = EXCLUDED.last_name,
            updated_at = NOW()
    """, (patient["id"], Json(patient["external_ids"]), patient["first_name"],
          patient["last_name"], patient["date_of_birth"], patient["gender"], patient["mrn"]))


def insert_fhir_resources(cur, resources: list[dict]) -> None:
    for r in resources:
        cur.execute("""
            INSERT INTO fhir_resources
                (id, patient_id, resource_type, resource_id, source_system,
                 fhir_version, content, content_hash, valid_from, ingested_at)
            VALUES (%s, %s, %s, %s, %s, 'R4', %s, %s, %s, NOW())
            ON CONFLICT (id) DO NOTHING
        """, (r["id"], r["content"]["subject"]["reference"].split("/")[1],
              r["resource_type"], r["resource_id"], r["source_system"],
              Json(r["content"]), h(r["content"]), r["valid_from"]))


def insert_conflicts(cur, conflicts: list[dict]) -> None:
    for c in conflicts:
        cur.execute("""
            INSERT INTO conflicts
                (id, patient_id, conflict_type, resource_type, resource_ids,
                 severity, description, auto_resolved, confidence_score, sources, detected_at)
            VALUES (%s, %s, %s, %s, %s::uuid[], %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO NOTHING
        """, (c["id"], c["patient_id"], c["conflict_type"], c["resource_type"],
              "{" + ",".join(c["resource_ids"]) + "}",
              c["severity"], c["description"], c["auto_resolved"],
              c["confidence_score"], Json(c["sources"])))


def insert_ai_summary(cur, s: dict) -> None:
    cur.execute("""
        UPDATE ai_summaries SET is_current = false
        WHERE patient_id = %s AND summary_type = %s AND is_current = true
    """, (s["patient_id"], s["summary_type"]))
    cur.execute("""
        INSERT INTO ai_summaries
            (id, patient_id, summary_type, model_used, content, sources,
             confidence_score, reasoning_summary, input_hash, is_current, expires_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW() + INTERVAL '1 year')
        ON CONFLICT (id) DO NOTHING
    """, (s["id"], s["patient_id"], s["summary_type"], s["model_used"],
          Json(s["content"]), Json(s["sources"]),
          s["confidence_score"], s["reasoning_summary"], s["input_hash"]))


# ── Main ────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Generate synthetic patient data")
    parser.add_argument("--count",    type=int, default=10, help="Number of patients to generate")
    parser.add_argument("--scenario", type=str, default="mixed", help="Clinical scenario (diabetic/cardiac/ckd/hypertensive/elderly/mixed)")
    parser.add_argument("--clear",    action="store_true",  help="Clear existing generated data first (keeps seeded demo patient)")
    parser.add_argument("--list-scenarios", action="store_true", help="List available scenarios")
    args = parser.parse_args()

    if args.list_scenarios:
        print("\nAvailable scenarios:")
        for name, sc in SCENARIOS.items():
            print(f"  {name:<15} — {len(sc['conditions'])} conditions, {len(sc['medications'])} medications, age {sc['age_range'][0]}-{sc['age_range'][1]}")
        return

    url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = psycopg2.connect(url)
    cur = conn.cursor()

    if args.clear:
        print("Clearing generated patient data (keeping demo patient)...")
        demo_id = "a1b2c3d4-0000-0000-0000-000000000001"
        cur.execute("DELETE FROM ai_summaries WHERE patient_id != %s", (demo_id,))
        cur.execute("DELETE FROM conflicts WHERE patient_id != %s", (demo_id,))
        cur.execute("DELETE FROM fhir_resources WHERE patient_id != %s", (demo_id,))
        cur.execute("DELETE FROM patients WHERE id != %s", (demo_id,))
        conn.commit()
        print("  Cleared existing generated data.")

    scenario_names = list(SCENARIOS.keys())
    total_conflicts = 0
    total_resources = 0

    print(f"\nGenerating {args.count} patient(s) — scenario: {args.scenario}\n")

    for i in range(args.count):
        sc = args.scenario if args.scenario != "mixed" else random.choice(scenario_names)
        patient = make_patient(sc)
        resources = make_fhir_resources(patient["id"], sc)
        conflicts = detect_conflicts(patient["id"], resources)

        # Fix resource patient_id reference
        for r in resources:
            r["content"]["subject"]["reference"] = f"Patient/{patient['id']}"

        summaries = [
            make_ai_summary(patient["id"], t, resources, conflicts)
            for t in ["CLINICAL", "MEDICATION_RECONCILIATION", "LAB_INTELLIGENCE", "VISIT_PREP"]
        ]

        insert_patient(cur, patient)
        insert_fhir_resources(cur, resources)
        insert_conflicts(cur, conflicts)
        for s in summaries:
            insert_ai_summary(cur, s)

        conn.commit()
        total_conflicts += len(conflicts)
        total_resources += len(resources)

        print(f"  [{i+1:>3}/{args.count}] {patient['first_name']:<12} {patient['last_name']:<15} "
              f"| {sc:<15} | {len(resources):>2} resources | {len(conflicts):>2} conflicts | ID: {patient['id'][:8]}...")

    cur.close()
    conn.close()

    print(f"""
Done! Generated:
  Patients   : {args.count}
  Resources  : {total_resources} FHIR resources
  Conflicts  : {total_conflicts} clinical conflicts
  Summaries  : {args.count * 4} AI summaries (4 per patient)

View in app  : http://localhost:3000/demo
API list     : http://localhost:8000/api/v1/patients (requires auth)
""")


if __name__ == "__main__":
    main()
