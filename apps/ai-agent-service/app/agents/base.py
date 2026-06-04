"""Base agent utilities shared across all LangGraph agents."""
from __future__ import annotations
import hashlib
import json
from datetime import datetime
from typing import Any, TypedDict
import structlog

log = structlog.get_logger()

FDA_DISCLAIMER = "Clinical Decision Support — For Clinician Review Only"


def compute_input_hash(data: dict) -> str:
    serialized = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode()).hexdigest()


def build_system_prompt(agent_role: str) -> str:
    return f"""You are a clinical decision support AI assisting Advanced Practice Clinicians (APCs).
Role: {agent_role}

CRITICAL RULES:
1. You are NOT a diagnosing system. Your outputs are decision support only.
2. Every output MUST include cited source systems and timestamps.
3. Every output MUST include a confidence_score between 0.0 and 1.0.
4. Label all outputs: "{FDA_DISCLAIMER}"
5. Set requires_clinician_review=true for all HIGH or CRITICAL severity items.
6. If data is insufficient, state that explicitly rather than guessing.
7. Do not fabricate clinical values. Use only data provided in context.

OUTPUT FORMAT: Return valid JSON matching the schema provided in each task prompt.
"""


def format_rag_context(chunks: list[dict]) -> str:
    if not chunks:
        return "No relevant clinical guidelines retrieved."
    lines = ["RELEVANT CLINICAL GUIDELINES:"]
    for chunk in chunks:
        lines.append(f"[{chunk['source_doc']}] {chunk['chunk_text']}")
    return "\n".join(lines)


def format_fhir_context(resources: list[dict], resource_types: list[str] | None = None) -> str:
    filtered = resources
    if resource_types:
        filtered = [r for r in resources if r.get("resource_type") in resource_types]
    if not filtered:
        return "No relevant clinical data available."
    lines = ["PATIENT CLINICAL DATA (FHIR R4):"]
    for r in filtered:
        content = r.get("content", {})
        lines.append(
            f"[{r['source_system'].upper()} | {r['resource_type']}] "
            f"{json.dumps(content, default=str)[:500]}"
        )
    return "\n".join(lines)
