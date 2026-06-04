"""HealthGorilla adapter — uses mock server in all non-prod environments."""
from __future__ import annotations
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = structlog.get_logger()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_patient_resources(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    url = f"{settings.healthgorilla_base_url}/fhir/r4/Patient/{patient_id}/$everything"
    resp = await client.get(url, headers={"X-API-Key": settings.healthgorilla_api_key})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    bundle = resp.json()
    return [entry["resource"] for entry in bundle.get("entry", []) if "resource" in entry]
