"""Clinical Summary Agent — LangGraph workflow."""
from __future__ import annotations
import json
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import structlog

from app.llm_router import get_llm, get_fallback_llm, LLMTask
from app.rag import retrieve_guidelines
from app.agents.base import build_system_prompt, format_rag_context, format_fhir_context, compute_input_hash, FDA_DISCLAIMER

log = structlog.get_logger()


class ClinicalSummaryState(TypedDict):
    patient_id: str
    fhir_resources: list[dict]
    rag_chunks: list[dict]
    llm_output: dict
    final_summary: dict
    input_hash: str
    model_used: str
    error: str | None


async def retrieve_rag_node(state: ClinicalSummaryState) -> ClinicalSummaryState:
    conditions = [
        r.get("content", {}).get("code", {}).get("text", "")
        for r in state["fhir_resources"]
        if r.get("resource_type") == "Condition"
    ]
    query = f"clinical care gaps and management guidelines for: {', '.join(set(conditions[:8]))}"
    state["rag_chunks"] = await retrieve_guidelines(query)
    state["input_hash"] = compute_input_hash({"patient_id": state["patient_id"], "resources": state["fhir_resources"]})
    return state


async def generate_summary_node(state: ClinicalSummaryState) -> ClinicalSummaryState:
    system_prompt = build_system_prompt("Clinical Summary Specialist")
    fhir_context = format_fhir_context(state["fhir_resources"])
    rag_context = format_rag_context(state["rag_chunks"])

    task_prompt = f"""
{fhir_context}

{rag_context}

TASK: Generate a comprehensive clinical summary for patient {state['patient_id']}.

Return JSON:
{{
  "patient_overview": "2-3 sentence narrative summary",
  "active_conditions": [
    {{"condition": "...", "icd10": "...", "status": "...", "source": "..."}}
  ],
  "active_medications_count": 0,
  "recent_events": [
    {{"event_type": "...", "description": "...", "date": "...", "source": "..."}}
  ],
  "care_gaps": [
    {{"gap": "...", "priority": "HIGH|MEDIUM|LOW", "recommendation": "...", "evidence_source": "..."}}
  ],
  "open_tasks": [
    {{"task": "...", "due_date": "...", "assigned_to": "..."}}
  ],
  "risk_flags": [
    {{"flag": "...", "severity": "...", "rationale": "..."}}
  ],
  "overall_confidence_score": 0.0-1.0,
  "reasoning_summary": "...",
  "fda_disclaimer": "{FDA_DISCLAIMER}"
}}
"""
    llm = get_llm(LLMTask.SUMMARIZATION)
    try:
        response = await llm.ainvoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=task_prompt),
        ])
        state["llm_output"] = json.loads(response.content)
        state["model_used"] = "openai/gpt-4o"
    except Exception as e:
        log.warning("primary_llm_failed_clinical", error=str(e))
        try:
            fallback = get_fallback_llm(LLMTask.SUMMARIZATION)
            response = await fallback.ainvoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=task_prompt),
            ])
            state["llm_output"] = json.loads(response.content)
            state["model_used"] = "anthropic/claude-fallback"
        except Exception as e2:
            state["error"] = str(e2)
            state["llm_output"] = {}
    return state


def format_output_node(state: ClinicalSummaryState) -> ClinicalSummaryState:
    llm_out = state.get("llm_output", {})
    sources = list({r.get("source_system") for r in state["fhir_resources"]})
    state["final_summary"] = {
        "patient_id": state["patient_id"],
        "summary_type": "CLINICAL",
        "model_used": state.get("model_used", "unknown"),
        "content": llm_out,
        "sources": [{"source_system": s} for s in sources],
        "confidence_score": llm_out.get("overall_confidence_score", 0.0),
        "reasoning_summary": llm_out.get("reasoning_summary", ""),
        "input_hash": state["input_hash"],
        "fda_disclaimer": FDA_DISCLAIMER,
    }
    return state


def build_clinical_summary_graph():
    graph = StateGraph(ClinicalSummaryState)
    graph.add_node("retrieve_rag", retrieve_rag_node)
    graph.add_node("generate_summary", generate_summary_node)
    graph.add_node("format_output", format_output_node)
    graph.set_entry_point("retrieve_rag")
    graph.add_edge("retrieve_rag", "generate_summary")
    graph.add_edge("generate_summary", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


clinical_summary_graph = build_clinical_summary_graph()


async def run_clinical_summary(patient_id: str, fhir_resources: list[dict]) -> dict:
    result = await clinical_summary_graph.ainvoke({
        "patient_id": patient_id,
        "fhir_resources": fhir_resources,
        "rag_chunks": [],
        "llm_output": {},
        "final_summary": {},
        "input_hash": "",
        "model_used": "",
        "error": None,
    })
    return result["final_summary"]
