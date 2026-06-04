"""HealthGorilla mock server — returns synthetic FHIR R4 bundles."""
from fastapi import FastAPI
import uuid

app = FastAPI(title="HealthGorilla Mock")

MOCK_PATIENTS = {
    "default": [
        {
            "resourceType": "MedicationStatement",
            "id": str(uuid.uuid4()),
            "status": "active",
            "medicationCodeableConcept": {"text": "Lisinopril 10mg"},
            "subject": {"reference": "Patient/default"},
            "effectiveDateTime": "2024-01-10",
        },
        {
            "resourceType": "Observation",
            "id": str(uuid.uuid4()),
            "status": "final",
            "code": {"text": "HbA1c", "coding": [{"system": "http://loinc.org", "code": "17856-6"}]},
            "valueQuantity": {"value": 8.2, "unit": "%"},
            "interpretation": [{"text": "H"}],
            "effectiveDateTime": "2024-02-15T09:00:00",
        },
    ]
}


@app.get("/fhir/r4/Patient/{patient_id}/$everything")
async def get_patient_everything(patient_id: str):
    resources = MOCK_PATIENTS.get(patient_id, MOCK_PATIENTS["default"])
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "entry": [{"resource": r} for r in resources],
    }


@app.get("/health")
async def health():
    return {"status": "ok", "mock": "healthgorilla"}
