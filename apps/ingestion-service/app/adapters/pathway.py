"""Pathway adapter — uses mock server."""
from __future__ import annotations
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = structlog.get_logger()


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_encounters(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    url = f"{settings.pathway_base_url}/api/v1/patients/{patient_id}/encounters"
    resp = await client.get(url, headers={"Authorization": f"Bearer {settings.pathway_api_key}"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("encounters", [])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_referrals(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    url = f"{settings.pathway_base_url}/api/v1/patients/{patient_id}/referrals"
    resp = await client.get(url, headers={"Authorization": f"Bearer {settings.pathway_api_key}"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("referrals", [])
