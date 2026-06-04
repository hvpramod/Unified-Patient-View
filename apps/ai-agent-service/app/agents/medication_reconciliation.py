"""Medication Reconciliation Agent — LangGraph workflow."""
from __future__ import annotations
import json
from typing import Any, TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import structlog

from app.llm_router import get_llm, get_fallback_llm, LLMTask
from app.rag import retrieve_guidelines
from app.agents.base import build_system_prompt, format_rag_context, format_fhir_context, compute_input_hash, FDA_DISCLAIMER

log = structlog.get_logger()


class MedReconState(TypedDict):
    patient_id: str
    fhir_resources: list[dict]
    conflicts: list[dict]
    rag_chunks: list[dict]
    llm_output: dict
    final_summary: dict
    input_hash: str
    model_used: str
    error: str | None


def fetch_medications_node(state: MedReconState) -> MedReconState:
    meds = [
        r for r in state["fhir_resources"]
        if r.get("resource_type") in ("MedicationRequest", "MedicationStatement")
    ]
    state["fhir_resources"] = meds
    state["input_hash"] = compute_input_hash({"patient_id": state["patient_id"], "meds": meds})
    return state


async def retrieve_rag_node(state: MedReconState) -> MedReconState:
    drug_names = []
    for r in state["fhir_resources"]:
        content = r.get("content", {})
        name = content.get("medicationCodeableConcept", {}).get("text", "")
        if name:
            drug_names.append(name)
    query = f"medication reconciliation guidelines for: {', '.join(set(drug_names[:10]))}"
    chunks = await retrieve_guidelines(query)
    state["rag_chunks"] = chunks
    return state


async def run_llm_reconciliation_node(state: MedReconState) -> MedReconState:
    system_prompt = build_system_prompt("Medication Reconciliation Specialist")
    fhir_context = format_fhir_context(
        state["fhir_resources"],
        ["MedicationRequest", "MedicationStatement"]
    )
    rag_context = format_rag_context(state["rag_chunks"])
    conflicts_context = json.dumps(state.get("conflicts", []), default=str)

    task_prompt = f"""
{fhir_context}

{rag_context}

DETECTED CONFLICTS (rule-based):
{conflicts_context}

TASK: Perform medication reconciliation for patient {state['patient_id']}.

Return JSON:
{{
  "reconciled_medications": [
    {{
      "drug_name": "...",
      "recommended_status": "active|discontinued|on-hold",
      "recommended_dose": "...",
      "confidence_score": 0.0-1.0,
      "rationale": "...",
      "sources_used": ["athena", "healthgorilla"],
      "conflicts_resolved": ["conflict_id"],
      "requires_clinician_review": true/false
    }}
  ],
  "unresolved_conflicts": [
    {{
      "conflict_description": "...",
      "severity": "HIGH|MEDIUM|LOW",
      "recommended_action": "..."
    }}
  ],
  "overall_confidence_score": 0.0-1.0,
  "reasoning_summary": "...",
  "fda_disclaimer": "{FDA_DISCLAIMER}"
}}
"""
    llm = get_llm(LLMTask.REASONING)
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_prompt),
        ])
        output = json.loads(response.content)
        state["llm_output"] = output
        state["model_used"] = f"claude/{state.get('_anthropic_model', 'claude-sonnet-4-6')}"
    except Exception as e:
        log.warning("primary_llm_failed_med_recon", error=str(e))
        try:
            fallback = get_fallback_llm(LLMTask.REASONING)
            response = await fallback.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt),
            ])
            output = json.loads(response.content)
            state["llm_output"] = output
            state["model_used"] = "openai/gpt-4o-fallback"
        except Exception as e2:
            state["error"] = str(e2)
            state["llm_output"] = {}
    return state


def format_output_node(state: MedReconState) -> MedReconState:
    llm_out = state.get("llm_output", {})
    sources = list({r.get("source_system") for r in state["fhir_resources"]})
    state["final_summary"] = {
        "patient_id": state["patient_id"],
        "summary_type": "MEDICATION_RECONCILIATION",
        "model_used": state.get("model_used", "unknown"),
        "content": llm_out,
        "sources": [{"source_system": s} for s in sources],
        "confidence_score": llm_out.get("overall_confidence_score", 0.0),
        "reasoning_summary": llm_out.get("reasoning_summary", ""),
        "input_hash": state["input_hash"],
        "fda_disclaimer": FDA_DISCLAIMER,
    }
    return state


def build_med_recon_graph():
    graph = StateGraph(MedReconState)
    graph.add_node("fetch_medications", fetch_medications_node)
    graph.add_node("retrieve_rag", retrieve_rag_node)
    graph.add_node("run_llm_reconciliation", run_llm_reconciliation_node)
    graph.add_node("format_output", format_output_node)

    graph.set_entry_point("fetch_medications")
    graph.add_edge("fetch_medications", "retrieve_rag")
    graph.add_edge("retrieve_rag", "run_llm_reconciliation")
    graph.add_edge("run_llm_reconciliation", "format_output")
    graph.add_edge("format_output", END)

    return graph.compile()


med_recon_graph = build_med_recon_graph()


async def run_medication_reconciliation(patient_id: str, fhir_resources: list[dict], conflicts: list[dict]) -> dict:
    initial_state: MedReconState = {
        "patient_id": patient_id,
        "fhir_resources": fhir_resources,
        "conflicts": conflicts,
        "rag_chunks": [],
        "llm_output": {},
        "final_summary": {},
        "input_hash": "",
        "model_used": "",
        "error": None,
    }
    result = await med_recon_graph.ainvoke(initial_state)
    return result["final_summary"]
