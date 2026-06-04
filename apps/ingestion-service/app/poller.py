"""Background polling loop — polls all source systems and publishes change events."""
from __future__ import annotations
import asyncio
import hashlib
import json
from typing import Any
import httpx
import structlog

from app.config import settings
from app.adapters import athena, healthgorilla, pathway
from app.normalizer import (
    normalize_athena_medication,
    normalize_athena_lab,
    normalize_healthgorilla_resource,
    normalize_pathway_resource,
)
from app.publisher import publish_patient_updated, publish_labs_new, publish_medications_changed
from app.db import upsert_fhir_resource, get_all_patient_ids

log = structlog.get_logger()


async def poll_patient(client: httpx.AsyncClient, patient_id: str, athena_patient_id: str) -> None:
    changed_types: list[str] = []
    new_lab_ids: list[str] = []
    changed_med_ids: list[str] = []

    try:
        # Athena medications
        raw_meds = await athena.fetch_medications(client, athena_patient_id)
        for raw in raw_meds:
            resource = normalize_athena_medication(raw, patient_id)
            changed = await upsert_fhir_resource(resource)
            if changed:
                changed_types.append("MedicationRequest")
                changed_med_ids.append(resource.id)

        # Athena labs
        raw_labs = await athena.fetch_labs(client, athena_patient_id)
        for raw in raw_labs:
            resource = normalize_athena_lab(raw, patient_id)
            changed = await upsert_fhir_resource(resource)
            if changed:
                changed_types.append("Observation")
                new_lab_ids.append(resource.id)

        # HealthGorilla resources
        hg_resources = await healthgorilla.fetch_patient_resources(client, patient_id)
        for raw in hg_resources:
            resource = normalize_healthgorilla_resource(raw, patient_id)
            changed = await upsert_fhir_resource(resource)
            if changed:
                changed_types.append(resource.resource_type.value)

        # Pathway encounters
        pw_encounters = await pathway.fetch_encounters(client, patient_id)
        for raw in pw_encounters:
            resource = normalize_pathway_resource({**raw, "resourceType": "Encounter"}, patient_id)
            changed = await upsert_fhir_resource(resource)
            if changed:
                changed_types.append("Encounter")

        # Publish events
        if changed_types:
            await publish_patient_updated(patient_id, list(set(changed_types)))
        if new_lab_ids:
            await publish_labs_new(patient_id, new_lab_ids)
        if changed_med_ids:
            await publish_medications_changed(patient_id, changed_med_ids)

    except Exception as e:
        log.error("poll_patient_error", patient_id=patient_id, error=str(e))


async def run_poll_loop() -> None:
    log.info("poller_starting", interval=settings.athena_poll_interval_seconds)
    async with httpx.AsyncClient(timeout=30.0) as client:
        while True:
            try:
                patients = await get_all_patient_ids()
                log.info("polling_patients", count=len(patients))
                tasks = [
                    poll_patient(client, p["id"], p["external_ids"].get("athena", p["id"]))
                    for p in patients
                ]
                await asyncio.gather(*tasks, return_exceptions=True)
            except Exception as e:
                log.error("poll_loop_error", error=str(e))
            await asyncio.sleep(settings.athena_poll_interval_seconds)
