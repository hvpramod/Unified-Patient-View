"""Pathway mock server — returns synthetic encounter and referral data."""
from fastapi import FastAPI
import uuid
from datetime import datetime

app = FastAPI(title="Pathway Mock")


@app.get("/api/v1/patients/{patient_id}/encounters")
async def get_encounters(patient_id: str):
    return {
        "encounters": [
            {
                "resourceType": "Encounter",
                "id": str(uuid.uuid4()),
                "status": "finished",
                "class": {"code": "AMB", "display": "ambulatory"},
                "type": [{"text": "Office visit"}],
                "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": "2024-03-01T09:00:00", "end": "2024-03-01T09:45:00"},
                "reasonCode": [{"text": "Diabetes follow-up"}],
            },
            {
                "resourceType": "Encounter",
                "id": str(uuid.uuid4()),
                "status": "finished",
                "class": {"code": "IMP", "display": "inpatient encounter"},
                "type": [{"text": "Hospital discharge"}],
                "subject": {"reference": f"Patient/{patient_id}"},
                "period": {"start": "2024-01-20T08:00:00", "end": "2024-01-23T14:00:00"},
                "reasonCode": [{"text": "Hypertension management"}],
                "extension": [
                    {
                        "url": "discharge-medications",
                        "extension": [
                            {"url": "medication", "valueString": "Lisinopril Discontinued"},
                            {"url": "status", "valueCode": "stopped"},
                        ],
                    }
                ],
            },
        ]
    }


@app.get("/api/v1/patients/{patient_id}/referrals")
async def get_referrals(patient_id: str):
    return {
        "referrals": [
            {
                "id": str(uuid.uuid4()),
                "referral_type": "Endocrinology",
                "status": "pending",
                "created_at": "2024-02-28",
                "reason": "Uncontrolled diabetes",
            }
        ]
    }


@app.get("/health")
async def health():
    return {"status": "ok", "mock": "pathway"}
