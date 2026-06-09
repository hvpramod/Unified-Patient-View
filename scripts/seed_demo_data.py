"""
Seed the UPV database with a realistic synthetic patient (Margaret Thompson)
including FHIR resources, conflicts, and pre-computed AI summaries.

Usage:
    python scripts/seed_demo_data.py

    # Or with custom DB URL:
    DATABASE_URL=postgresql://upv:upv@localhost:5432/upv python scripts/seed_demo_data.py
"""
import os, json, hashlib, sys
from datetime import datetime, date
from pathlib import Path

import psycopg2
from psycopg2.extras import Json

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://upv:upv@localhost:5432/upv")

# Fixed IDs so re-running the seed is idempotent
PATIENT_ID       = "a1b2c3d4-0000-0000-0000-000000000001"
DEMO_USER_ID     = "00000000-0000-0000-0000-000000000001"

def h(content: dict) -> str:
    return hashlib.sha256(json.dumps(content, sort_keys=True, default=str).encode()).hexdigest()

def connect():
    url = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    return psycopg2.connect(url)

# ── Seed data ─────────────────────────────────────────────────────────────────

PATIENT = {
    "id": PATIENT_ID,
    "external_ids": {"athena": "PT-294817", "healthgorilla": "HG-83729"},
    "first_name": "Margaret",
    "last_name": "Thompson",
    "date_of_birth": "1958-04-12",
    "gender": "Female",
    "mrn": "MRN-294817",
}

DEMO_USER = {
    "id": DEMO_USER_ID,
    "azure_oid": "demo-user-001",
    "email": "demo.apc@upv.local",
    "full_name": "Demo APC User",
    "role": "APC",
}

FHIR_RESOURCES = [
    # ── Medications ──────────────────────────────────────────────────────────
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000001",
        "resource_type": "MedicationRequest",
        "resource_id": "med-athena-001",
        "source_system": "athena",
        "content": {
            "resourceType": "MedicationRequest",
            "id": "med-athena-001",
            "status": "active",
            "medicationCodeableConcept": {
                "text": "Lisinopril 10mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"}],
            },
            "dosageInstruction": [{"text": "10mg once daily", "route": {"text": "oral"}}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "authoredOn": "2024-01-10",
            "_source": {"system": "athena", "id": "med-athena-001"},
        },
        "valid_from": "2024-01-10T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000002",
        "resource_type": "MedicationStatement",
        "resource_id": "med-pathway-001",
        "source_system": "pathway",
        "content": {
            "resourceType": "MedicationStatement",
            "id": "med-pathway-001",
            "status": "stopped",
            "medicationCodeableConcept": {
                "text": "Lisinopril 10mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "314076"}],
            },
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "effectivePeriod": {"start": "2024-01-10", "end": "2024-01-23"},
            "note": [{"text": "Discontinued at hospital discharge due to eGFR decline"}],
            "_source": {"system": "pathway", "id": "med-pathway-001"},
        },
        "valid_from": "2024-01-23T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000003",
        "resource_type": "MedicationRequest",
        "resource_id": "med-athena-002",
        "source_system": "athena",
        "content": {
            "resourceType": "MedicationRequest",
            "id": "med-athena-002",
            "status": "active",
            "medicationCodeableConcept": {
                "text": "Metformin 500mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "861007"}],
            },
            "dosageInstruction": [{"text": "500mg twice daily", "route": {"text": "oral"}}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "authoredOn": "2022-06-15",
            "_source": {"system": "athena", "id": "med-athena-002"},
        },
        "valid_from": "2022-06-15T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000004",
        "resource_type": "MedicationStatement",
        "resource_id": "med-hg-002",
        "source_system": "healthgorilla",
        "content": {
            "resourceType": "MedicationStatement",
            "id": "med-hg-002",
            "status": "active",
            "medicationCodeableConcept": {
                "text": "Metformin 500mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "861007"}],
            },
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "effectiveDateTime": "2022-06-15",
            "_source": {"system": "healthgorilla", "id": "med-hg-002"},
        },
        "valid_from": "2022-06-15T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000005",
        "resource_type": "MedicationRequest",
        "resource_id": "med-athena-003",
        "source_system": "athena",
        "content": {
            "resourceType": "MedicationRequest",
            "id": "med-athena-003",
            "status": "active",
            "medicationCodeableConcept": {
                "text": "Amlodipine 5mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "197361"}],
            },
            "dosageInstruction": [{"text": "5mg once daily", "route": {"text": "oral"}}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "authoredOn": "2023-03-01",
            "_source": {"system": "athena", "id": "med-athena-003"},
        },
        "valid_from": "2023-03-01T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0001-0000-0000-000000000006",
        "resource_type": "MedicationRequest",
        "resource_id": "med-athena-004",
        "source_system": "athena",
        "content": {
            "resourceType": "MedicationRequest",
            "id": "med-athena-004",
            "status": "active",
            "medicationCodeableConcept": {
                "text": "Atorvastatin 40mg",
                "coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "code": "617312"}],
            },
            "dosageInstruction": [{"text": "40mg at bedtime", "route": {"text": "oral"}}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "authoredOn": "2021-09-10",
            "_source": {"system": "athena", "id": "med-athena-004"},
        },
        "valid_from": "2021-09-10T00:00:00Z",
    },
    # ── Labs ─────────────────────────────────────────────────────────────────
    {
        "id": "a1b2c3d4-0002-0000-0000-000000000001",
        "resource_type": "Observation",
        "resource_id": "lab-athena-egfr-001",
        "source_system": "athena",
        "content": {
            "resourceType": "Observation",
            "id": "lab-athena-egfr-001",
            "status": "final",
            "code": {"text": "eGFR (CKD-EPI)", "coding": [{"system": "http://loinc.org", "code": "62238-1"}]},
            "valueQuantity": {"value": 38, "unit": "mL/min/1.73m²"},
            "interpretation": [{"text": "L"}],
            "referenceRange": [{"text": ">60 mL/min/1.73m²"}],
            "effectiveDateTime": "2024-09-01T09:00:00Z",
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "_source": {"system": "athena", "id": "lab-athena-egfr-001"},
        },
        "valid_from": "2024-09-01T09:00:00Z",
    },
    {
        "id": "a1b2c3d4-0002-0000-0000-000000000002",
        "resource_type": "Observation",
        "resource_id": "lab-athena-hba1c-001",
        "source_system": "athena",
        "content": {
            "resourceType": "Observation",
            "id": "lab-athena-hba1c-001",
            "status": "final",
            "code": {"text": "HbA1c", "coding": [{"system": "http://loinc.org", "code": "17856-6"}]},
            "valueQuantity": {"value": 7.4, "unit": "%"},
            "interpretation": [{"text": "H"}],
            "referenceRange": [{"text": "<5.7%"}],
            "effectiveDateTime": "2024-02-14T10:00:00Z",
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "_source": {"system": "athena", "id": "lab-athena-hba1c-001"},
        },
        "valid_from": "2024-02-14T10:00:00Z",
    },
    {
        "id": "a1b2c3d4-0002-0000-0000-000000000003",
        "resource_type": "Observation",
        "resource_id": "lab-hg-hba1c-001",
        "source_system": "healthgorilla",
        "content": {
            "resourceType": "Observation",
            "id": "lab-hg-hba1c-001",
            "status": "final",
            "code": {"text": "HbA1c", "coding": [{"system": "http://loinc.org", "code": "17856-6"}]},
            "valueQuantity": {"value": 8.2, "unit": "%"},
            "interpretation": [{"text": "H"}],
            "referenceRange": [{"text": "<5.7%"}],
            "effectiveDateTime": "2024-02-15T11:00:00Z",
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "_source": {"system": "healthgorilla", "id": "lab-hg-hba1c-001"},
        },
        "valid_from": "2024-02-15T11:00:00Z",
    },
    {
        "id": "a1b2c3d4-0002-0000-0000-000000000004",
        "resource_type": "Observation",
        "resource_id": "lab-athena-k-001",
        "source_system": "athena",
        "content": {
            "resourceType": "Observation",
            "id": "lab-athena-k-001",
            "status": "final",
            "code": {"text": "Potassium", "coding": [{"system": "http://loinc.org", "code": "2823-3"}]},
            "valueQuantity": {"value": 4.4, "unit": "mEq/L"},
            "interpretation": [{"text": "N"}],
            "referenceRange": [{"text": "3.5-5.0 mEq/L"}],
            "effectiveDateTime": "2024-09-01T09:00:00Z",
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "_source": {"system": "athena", "id": "lab-athena-k-001"},
        },
        "valid_from": "2024-09-01T09:00:00Z",
    },
    # ── Conditions ───────────────────────────────────────────────────────────
    {
        "id": "a1b2c3d4-0003-0000-0000-000000000001",
        "resource_type": "Condition",
        "resource_id": "cond-athena-t2dm",
        "source_system": "athena",
        "content": {
            "resourceType": "Condition",
            "id": "cond-athena-t2dm",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {"text": "Type 2 Diabetes Mellitus", "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E11.9"}]},
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "onsetDateTime": "2019-03-15",
            "_source": {"system": "athena"},
        },
        "valid_from": "2019-03-15T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0003-0000-0000-000000000002",
        "resource_type": "Condition",
        "resource_id": "cond-athena-htn",
        "source_system": "athena",
        "content": {
            "resourceType": "Condition",
            "id": "cond-athena-htn",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {"text": "Hypertension", "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "I10"}]},
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "onsetDateTime": "2017-08-20",
            "_source": {"system": "athena"},
        },
        "valid_from": "2017-08-20T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0003-0000-0000-000000000003",
        "resource_type": "Condition",
        "resource_id": "cond-hg-ckd",
        "source_system": "healthgorilla",
        "content": {
            "resourceType": "Condition",
            "id": "cond-hg-ckd",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {"text": "Chronic Kidney Disease Stage 3", "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "N18.3"}]},
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "onsetDateTime": "2023-01-10",
            "_source": {"system": "healthgorilla"},
        },
        "valid_from": "2023-01-10T00:00:00Z",
    },
    {
        "id": "a1b2c3d4-0003-0000-0000-000000000004",
        "resource_type": "Condition",
        "resource_id": "cond-athena-hld",
        "source_system": "athena",
        "content": {
            "resourceType": "Condition",
            "id": "cond-athena-hld",
            "clinicalStatus": {"coding": [{"code": "active"}]},
            "code": {"text": "Hyperlipidemia", "coding": [{"system": "http://hl7.org/fhir/sid/icd-10", "code": "E78.5"}]},
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "onsetDateTime": "2020-05-01",
            "_source": {"system": "athena"},
        },
        "valid_from": "2020-05-01T00:00:00Z",
    },
    # ── Encounters ───────────────────────────────────────────────────────────
    {
        "id": "a1b2c3d4-0004-0000-0000-000000000001",
        "resource_type": "Encounter",
        "resource_id": "enc-pathway-hosp-001",
        "source_system": "pathway",
        "content": {
            "resourceType": "Encounter",
            "id": "enc-pathway-hosp-001",
            "status": "finished",
            "class": {"code": "IMP", "display": "inpatient encounter"},
            "type": [{"text": "Hospital admission — Hypertensive urgency"}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "period": {"start": "2024-01-20T08:00:00Z", "end": "2024-01-23T14:00:00Z"},
            "reasonCode": [{"text": "Hypertensive urgency — BP 210/118 on presentation"}],
            "_source": {"system": "pathway"},
        },
        "valid_from": "2024-01-20T08:00:00Z",
    },
    {
        "id": "a1b2c3d4-0004-0000-0000-000000000002",
        "resource_type": "Encounter",
        "resource_id": "enc-athena-office-001",
        "source_system": "athena",
        "content": {
            "resourceType": "Encounter",
            "id": "enc-athena-office-001",
            "status": "finished",
            "class": {"code": "AMB", "display": "ambulatory"},
            "type": [{"text": "Office visit — Diabetes follow-up"}],
            "subject": {"reference": f"Patient/{PATIENT_ID}"},
            "period": {"start": "2024-03-01T09:00:00Z", "end": "2024-03-01T09:45:00Z"},
            "_source": {"system": "athena"},
        },
        "valid_from": "2024-03-01T09:00:00Z",
    },
]

CONFLICTS = [
    {
        "id": "c0000001-0000-4000-0000-000000000001",
        "conflict_type": "STATUS_MISMATCH",
        "resource_type": "MedicationRequest",
        "resource_ids": [
            "a1b2c3d4-0001-0000-0000-000000000001",
            "a1b2c3d4-0001-0000-0000-000000000002",
        ],
        "severity": "CRITICAL",
        "description": "Lisinopril 10mg: Listed as ACTIVE in Athena (last updated 2024-01-10) but DISCONTINUED in Pathway hospital discharge summary (2024-01-23). Patient may not be taking a critical antihypertensive.",
        "auto_resolved": False,
        "confidence_score": 0.97,
        "sources": ["athena", "pathway"],
    },
    {
        "id": "c0000001-0000-4000-0000-000000000002",
        "conflict_type": "LAB_DISCREPANCY",
        "resource_type": "Observation",
        "resource_ids": [
            "a1b2c3d4-0002-0000-0000-000000000002",
            "a1b2c3d4-0002-0000-0000-000000000003",
        ],
        "severity": "MEDIUM",
        "description": "HbA1c result discrepancy within 3-day window: Athena reports 7.4% (Feb 14), Health Gorilla reports 8.2% (Feb 15). 10.8% difference exceeds 15% threshold. Lab source calibration may differ.",
        "auto_resolved": False,
        "confidence_score": 0.84,
        "sources": ["athena", "healthgorilla"],
    },
    {
        "id": "c0000001-0000-4000-0000-000000000003",
        "conflict_type": "MEDICATION_DUPLICATE",
        "resource_type": "MedicationRequest",
        "resource_ids": [
            "a1b2c3d4-0001-0000-0000-000000000003",
            "a1b2c3d4-0001-0000-0000-000000000004",
        ],
        "severity": "MEDIUM",
        "description": "Metformin 500mg active in both Athena and Health Gorilla as separate active prescriptions. Possible duplicate entry from EHR migration.",
        "auto_resolved": False,
        "confidence_score": 0.89,
        "sources": ["athena", "healthgorilla"],
    },
]

AI_SUMMARIES = [
    {
        "id": "50000001-0000-0000-0000-000000000001",
        "summary_type": "CLINICAL",
        "model_used": "openai/gpt-4o",
        "model_version": "gpt-4o-2024-08-06",
        "confidence_score": 0.91,
        "reasoning_summary": "Summary generated from 3 source systems (Athena, Health Gorilla, Pathway). Two active conflicts detected by rule engine. RAG retrieved 4 relevant clinical guideline chunks including ADA Standards of Diabetes Care 2024 and KDIGO CKD guidelines.",
        "input_hash": "demo-hash-clinical",
        "content": {
            "patient_overview": "Margaret Thompson is a 66-year-old female with a complex medical history including Type 2 Diabetes Mellitus (HbA1c 8.2%), Hypertension, and Chronic Kidney Disease Stage 3. She was recently discharged from Regional Medical Center following a 3-day inpatient stay for hypertensive urgency. Her current medication regimen shows a critical conflict between Athena and the hospital discharge summary regarding Lisinopril.",
            "active_conditions": [
                {"condition": "Type 2 Diabetes Mellitus", "icd10": "E11.9", "status": "active", "source": "Athena"},
                {"condition": "Hypertension", "icd10": "I10", "status": "active", "source": "Athena"},
                {"condition": "Chronic Kidney Disease Stage 3", "icd10": "N18.3", "status": "active", "source": "Health Gorilla"},
                {"condition": "Hyperlipidemia", "icd10": "E78.5", "status": "active", "source": "Athena"},
            ],
            "care_gaps": [
                {"gap": "HbA1c above target (8.2% — goal <7.5%)", "priority": "HIGH", "recommendation": "Consider adjusting Metformin dose or adding GLP-1 agonist. Referral to Endocrinology pending."},
                {"gap": "Annual diabetic eye exam overdue (last: 18 months ago)", "priority": "MEDIUM", "recommendation": "Schedule ophthalmology referral"},
                {"gap": "Nephrology follow-up not completed", "priority": "HIGH", "recommendation": "CKD Stage 3 requires nephrology consultation within 3 months"},
            ],
            "risk_flags": [
                {"flag": "Medication conflict: Lisinopril active in Athena, discontinued in hospital discharge", "severity": "CRITICAL", "rationale": "Active in Athena as of 2024-01-10. Hospital discharge 2024-01-23 lists Lisinopril as Discontinued due to renal function decline."},
                {"flag": "HbA1c trending upward (+0.8% over 6 months)", "severity": "HIGH", "rationale": "Feb 2024: 7.4%, Aug 2024: 8.2% — pattern suggests inadequate glycemic control"},
            ],
            "open_tasks": [
                {"task": "Reconcile Lisinopril medication status", "due_date": "Today", "assigned_to": "APC"},
                {"task": "Expedite nephrology referral", "due_date": "Within 2 weeks", "assigned_to": "APC"},
                {"task": "Review glycemic management plan", "due_date": "This visit", "assigned_to": "APC"},
            ],
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        },
        "sources": [
            {"source_system": "athena", "resource_type": "MedicationRequest"},
            {"source_system": "healthgorilla", "resource_type": "Observation"},
            {"source_system": "pathway", "resource_type": "Encounter"},
        ],
    },
    {
        "id": "50000001-0000-0000-0000-000000000002",
        "summary_type": "MEDICATION_RECONCILIATION",
        "model_used": "claude/claude-sonnet-4-6",
        "model_version": "claude-sonnet-4-6-20241022",
        "confidence_score": 0.93,
        "reasoning_summary": "Reconciliation based on 6 active medication records across Athena, Health Gorilla, and Pathway. Hospital discharge documents identified as authoritative for Lisinopril status change.",
        "input_hash": "demo-hash-medrec",
        "content": {
            "reconciled_medications": [
                {
                    "drug_name": "Lisinopril 10mg",
                    "recommended_status": "discontinued",
                    "recommended_dose": "Discontinue — per hospital discharge 2024-01-23",
                    "rationale": "Hospital discharge documentation explicitly discontinues Lisinopril due to eGFR decline (eGFR 38). CKD Stage 3 with declining function warrants ACE inhibitor reassessment. Recommend clinical review before reinstatement.",
                    "sources_used": ["athena", "pathway"],
                    "confidence_score": 0.94,
                    "requires_clinician_review": True,
                },
                {
                    "drug_name": "Metformin 500mg",
                    "recommended_status": "active",
                    "recommended_dose": "500mg twice daily (reduce if eGFR <30)",
                    "rationale": "Consistent across Athena and Health Gorilla. Safe at current eGFR 38. Monitor quarterly.",
                    "sources_used": ["athena", "healthgorilla"],
                    "confidence_score": 0.96,
                    "requires_clinician_review": False,
                },
                {
                    "drug_name": "Amlodipine 5mg",
                    "recommended_status": "active",
                    "recommended_dose": "5mg daily",
                    "rationale": "Consistent status. Calcium channel blocker appropriate for hypertension in CKD. No conflicts detected.",
                    "sources_used": ["athena"],
                    "confidence_score": 0.98,
                    "requires_clinician_review": False,
                },
                {
                    "drug_name": "Atorvastatin 40mg",
                    "recommended_status": "active",
                    "recommended_dose": "40mg at bedtime",
                    "rationale": "Consistent. Statin therapy appropriate for cardiovascular risk reduction in T2DM.",
                    "sources_used": ["athena", "healthgorilla"],
                    "confidence_score": 0.97,
                    "requires_clinician_review": False,
                },
            ],
            "unresolved_conflicts": [
                {"conflict_description": "Lisinopril status mismatch between Athena and Pathway", "severity": "CRITICAL", "recommended_action": "Verify with patient current medication adherence"},
            ],
            "overall_confidence_score": 0.93,
            "reasoning_summary": "Reconciliation based on 6 active medication records across 3 sources.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        },
        "sources": [
            {"source_system": "athena"},
            {"source_system": "healthgorilla"},
            {"source_system": "pathway"},
        ],
    },
    {
        "id": "50000001-0000-0000-0000-000000000003",
        "summary_type": "LAB_INTELLIGENCE",
        "model_used": "openai/gpt-4o",
        "model_version": "gpt-4o-2024-08-06",
        "confidence_score": 0.92,
        "reasoning_summary": "Lab analysis covers 4 result sets across 2 sources. Critical value identified: eGFR 38 with declining trend. HbA1c discrepancy between sources flagged as conflict.",
        "input_hash": "demo-hash-labs",
        "content": {
            "critical_values": [
                {
                    "test_name": "eGFR (CKD-EPI)",
                    "value": "38",
                    "unit": "mL/min/1.73m²",
                    "reference_range": ">60",
                    "interpretation": "L",
                    "clinical_significance": "CKD Stage 3b. Significant renal impairment. Requires nephrology referral and medication dose adjustments. Monitor potassium closely.",
                    "recommended_action": "Urgent nephrology referral. Review all renally-dosed medications.",
                    "source": "athena",
                    "collected_at": "2024-09-01",
                },
            ],
            "trends": [
                {
                    "test_name": "HbA1c",
                    "trend_direction": "INCREASING",
                    "values": [
                        {"value": 7.1, "date": "2024-03-01", "source": "athena"},
                        {"value": 7.4, "date": "2024-06-01", "source": "athena"},
                        {"value": 8.2, "date": "2024-09-01", "source": "healthgorilla"},
                    ],
                    "clinical_implication": "Upward trend (+1.1% over 6 months) suggests worsening glycemic control. ADA 2024 guidelines recommend medication intensification at HbA1c >8.0%.",
                },
                {
                    "test_name": "eGFR",
                    "trend_direction": "DECREASING",
                    "values": [
                        {"value": 52, "date": "2024-01-01", "source": "athena"},
                        {"value": 44, "date": "2024-05-01", "source": "athena"},
                        {"value": 38, "date": "2024-09-01", "source": "athena"},
                    ],
                    "clinical_implication": "Declining renal function (-14 mL/min over 8 months). At current rate, Stage 4 CKD within 12–18 months. Nephrology urgent.",
                },
                {
                    "test_name": "Potassium",
                    "trend_direction": "STABLE",
                    "values": [
                        {"value": 4.2, "date": "2024-06-01", "source": "athena"},
                        {"value": 4.4, "date": "2024-09-01", "source": "athena"},
                    ],
                    "clinical_implication": "Within normal limits. Monitor quarterly given CKD and ACE inhibitor use.",
                },
            ],
            "abnormal_values": [
                {"test_name": "HbA1c", "value": "8.2%", "expected_range": "<5.7%", "significance": "Above therapeutic target for T2DM management"},
            ],
            "summary_narrative": "Critical: eGFR 38 (Stage 3b CKD) with declining trend. HbA1c 8.2% trending upward — glycemic target not met. Potassium stable. No acute electrolyte abnormalities.",
            "overall_confidence_score": 0.92,
            "reasoning_summary": "Analysis of 4 lab results across 2 source systems.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        },
        "sources": [
            {"source_system": "athena"},
            {"source_system": "healthgorilla"},
        ],
    },
    {
        "id": "50000001-0000-0000-0000-000000000004",
        "summary_type": "VISIT_PREP",
        "model_used": "openai/gpt-4o",
        "model_version": "gpt-4o-2024-08-06",
        "confidence_score": 0.89,
        "reasoning_summary": "Visit prep generated 6 weeks post-discharge. Primary agenda: Lisinopril reconciliation, eGFR trajectory, glycemic control.",
        "input_hash": "demo-hash-visitprep",
        "content": {
            "visit_brief": "Ms. Thompson presents for a scheduled follow-up 6 weeks post-discharge from Regional Medical Center (Jan 20–23 admission for hypertensive urgency). Critical agenda items include: (1) Resolving the Lisinopril medication conflict — the drug appears active in Athena but was discontinued at discharge; (2) Addressing accelerating eGFR decline now at 38; (3) Reviewing worsening glycemic control (HbA1c 8.2%). Patient has a pending Endocrinology referral.",
            "priority_issues": [
                {"issue": "Lisinopril medication conflict", "priority": "HIGH", "background": "Active in Athena, discontinued at hospital discharge. Patient may be incorrectly taking or omitting."},
                {"issue": "eGFR decline trajectory", "priority": "HIGH", "background": "38 mL/min — Stage 3b CKD. Declining 14 points over 8 months."},
            ],
            "risk_alerts": [
                {"alert": "Unresolved Lisinopril conflict — patient may be incorrectly taking or omitting a critical antihypertensive", "severity": "CRITICAL", "rationale": "Status mismatch between Athena and hospital discharge", "recommended_action": "Confirm current medication use. Reconcile Athena record with discharge summary."},
                {"alert": "eGFR decline trajectory — approaching CKD Stage 4", "severity": "HIGH", "rationale": "Current trajectory: Stage 4 within 12–18 months", "recommended_action": "Initiate nephrology referral if not yet completed. Review Metformin continuation."},
            ],
            "suggested_questions": [
                {"question": "Are you currently taking Lisinopril? When did you last take it?", "rationale": "Resolves the medication conflict — determines actual patient behaviour", "related_condition": "Hypertension / CKD"},
                {"question": "How are your blood sugars running at home? Any readings above 250?", "rationale": "Contextualises HbA1c 8.2% — identifies post-prandial vs fasting pattern", "related_condition": "Type 2 Diabetes"},
                {"question": "Have you noticed any changes in your urine output or ankle swelling since discharge?", "rationale": "Screens for fluid retention / acute decompensation related to eGFR decline", "related_condition": "CKD Stage 3b"},
                {"question": "Have you followed up with the Endocrinology referral from your last visit?", "rationale": "Tracks care coordination for uncontrolled diabetes", "related_condition": "Type 2 Diabetes"},
            ],
            "follow_up_recommendations": [
                {"recommendation": "Order repeat BMP in 4 weeks to monitor eGFR and potassium trend", "timeframe": "4 weeks", "rationale": "Monitor CKD progression"},
                {"recommendation": "Expedite Nephrology referral — eGFR 38 with declining trend", "timeframe": "Within 2 weeks", "rationale": "Stage 3b CKD progression risk"},
                {"recommendation": "Intensify diabetes management: consider adding GLP-1 agonist (also renoprotective)", "timeframe": "This visit", "rationale": "HbA1c 8.2% above target"},
                {"recommendation": "Update Athena medication record to reflect hospital discharge changes", "timeframe": "Today", "rationale": "Medication reconciliation"},
            ],
            "pending_labs_or_referrals": ["Endocrinology referral (pending)", "Nephrology referral (needed)", "BMP in 4 weeks"],
            "overall_confidence_score": 0.89,
            "reasoning_summary": "Visit prep generated 6 weeks post-discharge.",
            "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
        },
        "sources": [
            {"source_system": "athena"},
            {"source_system": "healthgorilla"},
            {"source_system": "pathway"},
        ],
    },
]


# ── DB insertion ──────────────────────────────────────────────────────────────

def seed(conn):
    cur = conn.cursor()

    print("Seeding demo user...")
    cur.execute("""
        INSERT INTO users (id, azure_oid, email, full_name, role, is_active)
        VALUES (%s, %s, %s, %s, %s, true)
        ON CONFLICT (azure_oid) DO NOTHING
    """, (DEMO_USER["id"], DEMO_USER["azure_oid"], DEMO_USER["email"], DEMO_USER["full_name"], DEMO_USER["role"]))

    print("Seeding patient Margaret Thompson...")
    cur.execute("""
        INSERT INTO patients (id, external_ids, first_name, last_name, date_of_birth, gender, mrn)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            external_ids = EXCLUDED.external_ids,
            first_name   = EXCLUDED.first_name,
            last_name    = EXCLUDED.last_name,
            updated_at   = NOW()
    """, (
        PATIENT["id"], Json(PATIENT["external_ids"]),
        PATIENT["first_name"], PATIENT["last_name"],
        PATIENT["date_of_birth"], PATIENT["gender"], PATIENT["mrn"],
    ))

    print(f"Seeding {len(FHIR_RESOURCES)} FHIR resources...")
    for r in FHIR_RESOURCES:
        content_hash = h(r["content"])
        cur.execute("""
            INSERT INTO fhir_resources
                (id, patient_id, resource_type, resource_id, source_system, fhir_version,
                 content, content_hash, valid_from, ingested_at)
            VALUES (%s, %s, %s, %s, %s, 'R4', %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                content      = EXCLUDED.content,
                content_hash = EXCLUDED.content_hash
        """, (
            r["id"], PATIENT_ID, r["resource_type"], r["resource_id"],
            r["source_system"], Json(r["content"]), content_hash, r["valid_from"],
        ))

    print(f"Seeding {len(CONFLICTS)} conflicts...")
    for c in CONFLICTS:
        cur.execute("""
            INSERT INTO conflicts
                (id, patient_id, conflict_type, resource_type, resource_ids,
                 severity, description, auto_resolved, confidence_score, sources, detected_at)
            VALUES (%s, %s, %s, %s, %s::uuid[], %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (id) DO UPDATE SET
                description = EXCLUDED.description,
                severity    = EXCLUDED.severity
        """, (
            c["id"], PATIENT_ID, c["conflict_type"], c["resource_type"],
            "{" + ",".join(c["resource_ids"]) + "}",
            c["severity"], c["description"], c["auto_resolved"],
            c["confidence_score"], Json(c["sources"]),
        ))

    print(f"Seeding {len(AI_SUMMARIES)} AI summaries...")
    for s in AI_SUMMARIES:
        cur.execute("""
            INSERT INTO ai_summaries
                (id, patient_id, summary_type, model_used, content, sources,
                 confidence_score, reasoning_summary, input_hash, is_current, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, true, NOW() + INTERVAL '1 year')
            ON CONFLICT (id) DO UPDATE SET
                content    = EXCLUDED.content,
                is_current = true
        """, (
            s["id"], PATIENT_ID, s["summary_type"], s["model_used"],
            Json(s["content"]), Json(s["sources"]),
            s["confidence_score"], s["reasoning_summary"], s["input_hash"],
        ))

    # Cache summaries in Redis too (optional — nice to have)
    try:
        import redis
        r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"), decode_responses=True)
        import json as _json
        for s in AI_SUMMARIES:
            key = f"summary:{PATIENT_ID}:{s['summary_type']}"
            payload = {
                "patient_id": PATIENT_ID,
                "summary_id": s["id"],
                "summary_type": s["summary_type"],
                "model_used": s["model_used"],
                "content": s["content"],
                "sources": s["sources"],
                "confidence_score": s["confidence_score"],
                "reasoning_summary": s["reasoning_summary"],
                "generated_at": datetime.utcnow().isoformat(),
                "fda_disclaimer": "Clinical Decision Support — For Clinician Review Only",
            }
            r.setex(key, 86400, _json.dumps(payload))
        print("Summaries cached in Redis ✓")
    except Exception as e:
        print(f"Redis cache skipped ({e})")

    conn.commit()
    cur.close()


def main():
    print(f"\nConnecting to: {DATABASE_URL.replace(DATABASE_URL.split('@')[0].split('//')[1], '***')}")
    try:
        conn = connect()
    except Exception as e:
        print(f"ERROR: Cannot connect to database — {e}")
        print("Make sure PostgreSQL is running and the 'upv' database exists.")
        sys.exit(1)

    try:
        seed(conn)
        print(f"""
Demo data seeded successfully!

Patient ID : {PATIENT_ID}
Patient    : Margaret Thompson (MRN-294817)
Records    : {len(FHIR_RESOURCES)} FHIR resources, {len(CONFLICTS)} conflicts, {len(AI_SUMMARIES)} AI summaries

Open the app:
  http://localhost:3000/patients/{PATIENT_ID}
  http://localhost:3000/demo  (still works with synthetic data)
""")
    except Exception as e:
        conn.rollback()
        print(f"ERROR during seed: {e}")
        import traceback; traceback.print_exc()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
