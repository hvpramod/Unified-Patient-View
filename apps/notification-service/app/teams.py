"""Microsoft Teams notification via Graph API / Incoming Webhooks."""
from __future__ import annotations
import httpx
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

log = structlog.get_logger()


def _build_critical_lab_card(patient_id: str, lab_data: dict) -> dict:
    critical_values = lab_data.get("content", {}).get("critical_values", [])
    items = "\n".join(
        f"• **{v['test_name']}**: {v['value']} {v.get('unit', '')} — {v.get('clinical_significance', '')}"
        for v in critical_values[:5]
    )
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "FF0000",
        "summary": f"Critical Lab Values — Patient {patient_id[:8]}",
        "sections": [
            {
                "activityTitle": f"⚠️ Critical Lab Values Detected",
                "activitySubtitle": f"Patient ID: {patient_id[:8]}... | UPV Clinical Alert",
                "activityText": items or "Critical values detected — review in UPV",
                "facts": [
                    {"name": "Model", "value": lab_data.get("model_used", "N/A")},
                    {"name": "Confidence", "value": f"{float(lab_data.get('confidence_score', 0)):.0%}"},
                    {"name": "Disclaimer", "value": "Clinical Decision Support — For Clinician Review Only"},
                ],
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View in UPV",
                "targets": [{"os": "default", "uri": f"{settings.upv_base_url}/patients/{patient_id}"}],
            }
        ],
    }


def _build_summary_card(patient_id: str, summary_type: str, summary_data: dict) -> dict:
    content = summary_data.get("content", {})
    narrative = (
        content.get("patient_overview")
        or content.get("visit_brief")
        or content.get("summary_narrative")
        or "Summary generated"
    )
    return {
        "@type": "MessageCard",
        "@context": "http://schema.org/extensions",
        "themeColor": "0076D7",
        "summary": f"UPV {summary_type} Summary",
        "sections": [
            {
                "activityTitle": f"📋 {summary_type.replace('_', ' ').title()} Summary",
                "activitySubtitle": f"Patient ID: {patient_id[:8]}...",
                "activityText": narrative[:500],
                "facts": [
                    {"name": "Confidence", "value": f"{float(summary_data.get('confidence_score', 0)):.0%}"},
                    {"name": "Disclaimer", "value": "Clinical Decision Support — For Clinician Review Only"},
                ],
            }
        ],
    }


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def send_teams_notification(webhook_url: str, card: dict) -> bool:
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(webhook_url, json=card)
        if resp.status_code not in (200, 202):
            log.error("teams_webhook_error", status=resp.status_code, body=resp.text[:200])
            return False
        return True


async def notify_critical_labs(patient_id: str, lab_summary: dict) -> bool:
    if not settings.teams_webhook_url:
        log.warning("teams_webhook_not_configured")
        return False
    card = _build_critical_lab_card(patient_id, lab_summary)
    return await send_teams_notification(settings.teams_webhook_url, card)


async def notify_summary(patient_id: str, summary_type: str, summary_data: dict) -> bool:
    if not settings.teams_webhook_url:
        return False
    card = _build_summary_card(patient_id, summary_type, summary_data)
    return await send_teams_notification(settings.teams_webhook_url, card)
