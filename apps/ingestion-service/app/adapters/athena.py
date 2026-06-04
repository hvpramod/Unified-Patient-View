"""Athena Health REST API adapter."""
from __future__ import annotations
import asyncio
from typing import Any, AsyncGenerator
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = structlog.get_logger()

_token_cache: dict[str, Any] = {}


async def _get_access_token(client: httpx.AsyncClient) -> str:
    """OAuth2 client credentials flow for Athena API."""
    import time
    if _token_cache.get("expires_at", 0) > time.time() + 60:
        return _token_cache["access_token"]

    resp = await client.post(
        "https://api.platform.athenahealth.com/oauth2/v1/token",
        data={
            "grant_type": "client_credentials",
            "client_id": settings.athena_client_id,
            "client_secret": settings.athena_client_secret,
        },
    )
    resp.raise_for_status()
    data = resp.json()
    import time as _time
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = _time.time() + data.get("expires_in", 3600)
    return _token_cache["access_token"]


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_patients(client: httpx.AsyncClient, limit: int = 100, offset: int = 0) -> list[dict]:
    token = await _get_access_token(client)
    url = f"{settings.athena_base_url}/{settings.athena_practice_id}/patients"
    resp = await client.get(
        url,
        params={"limit": limit, "offset": offset},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json().get("patients", [])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_medications(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    token = await _get_access_token(client)
    url = f"{settings.athena_base_url}/{settings.athena_practice_id}/chart/{patient_id}/medications"
    resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("medications", [])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_labs(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    token = await _get_access_token(client)
    url = f"{settings.athena_base_url}/{settings.athena_practice_id}/chart/{patient_id}/labs/results"
    resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("labs", [])


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def fetch_conditions(client: httpx.AsyncClient, patient_id: str) -> list[dict]:
    token = await _get_access_token(client)
    url = f"{settings.athena_base_url}/{settings.athena_practice_id}/chart/{patient_id}/problems"
    resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
    if resp.status_code == 404:
        return []
    resp.raise_for_status()
    return resp.json().get("problems", [])


async def write_back_medications(client: httpx.AsyncClient, patient_id: str, medications: list[dict]) -> bool:
    """Write reconciled medication list back to Athena."""
    token = await _get_access_token(client)
    url = f"{settings.athena_base_url}/{settings.athena_practice_id}/chart/{patient_id}/medications"
    errors = []
    for med in medications:
        try:
            resp = await client.put(
                f"{url}/{med['medicationid']}",
                json=med,
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
        except Exception as e:
            errors.append(str(e))
            log.error("athena_writeback_error", medication_id=med.get("medicationid"), error=str(e))
    return len(errors) == 0
