"""Integration tests for gateway API."""
import pytest
import sys
import os
from httpx import AsyncClient, ASGITransport

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../apps/gateway-api"))

# Patch auth for testing
os.environ.setdefault("AZURE_TENANT_ID", "test")
os.environ.setdefault("AZURE_CLIENT_ID", "test")


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_health_endpoint():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.anyio
async def test_openapi_available():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/openapi.json")
        assert resp.status_code == 200
        schema = resp.json()
        assert "paths" in schema


@pytest.mark.anyio
async def test_patient_endpoint_requires_auth():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/v1/patients/test-patient-id")
        assert resp.status_code == 403  # No bearer token
