"""Visit Preparation Agent — LangGraph workflow."""
from __future__ import annotations
import json
from datetime import datetime, timedelta
from typing import TypedDict
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
import structlog

from app.llm_router import get_llm, LLMTask
from app.rag import retrieve_guidelines
from app.agents.base import build_system_prompt, format_rag_context, format_fhir_context, compute_input_hash, FDA_DISCLAIMER

log = structlog.get_logger()


class VisitPrepState(TypedDict):
    patient_id: str
    appointment_id: str | None
    appointment_date: str | None
    fhir_resources: list[dict]
    rag_chunks: list[dict]
    llm_output: dict
    final_summary: dict
    input_hash: str
    model_used: str
    error: str | None


def filter_recent_events_node(state: VisitPrepState) -> VisitPrepState:
    """Keep only events from the last 30 days for visit prep context."""
    cutoff = datetime.utcnow() - timedelta(days=30)
    recent = []
    for r in state["fhir_resources"]:
        content = r.get("content", {})
        date_str = (
            content.get("effectiveDateTime")
            or content.get("authoredOn")
            or content.get("onsetDateTime")
            or content.get("period", {}).get("start")
        )
        if date_str:
            try:
                from dateutil import parser
                if parser.parse(date_str).replace(tzinfo=None) >= cutoff:
                    recent.append(r)
            except Exception:
                recent.append(r)
        else:
            recent.append(r)

    state["fhir_resources"] = recent
    state["input_hash"] = compute_input_hash({
        "patient_id": state["patient_id"],
        "appointment_id": state.get("appointment_id"),
        "resources": recent,
    })
    return state


async def retrieve_rag_node(state: VisitPrepState) -> VisitPrepState:
    conditions = [
        r.get("content", {}).get("code", {}).get("text", "")
        for r in state["fhir_resources"]
        if r.get("resource_type") == "Condition"
    ]
    query = f"visit preparation, preventive care guidelines, follow-up recommendations: {', '.join(set(conditions[:6]))}"
    state["rag_chunks"] = await retrieve_guidelines(query)
    return state


async def generate_visit_brief_node(state: VisitPrepState) -> VisitPrepState:
    system_prompt = build_system_prompt("Visit Preparation Specialist")
    fhir_context = format_fhir_context(state["fhir_resources"])
    rag_context = format_rag_context(state["rag_chunks"])

    task_prompt = f"""
{fhir_context}

{rag_context}

APPOINTMENT: {state.get('appointment_date', 'Upcoming')} (ID: {state.get('appointment_id', 'N/A')})

TASK: Generate a visit preparation brief for patient {state['patient_id']}.

Return JSON:
{{
  "visit_brief": "Concise 3-4 sentence pre-visit narrative",
  "priority_issues": [
    {{"issue": "...", "priority": "HIGH|MEDIUM|LOW", "background": "..."}}
  ],
  "suggested_questions": [
    {{"question": "...", "rationale": "...", "related_condition": "..."}}
  ],
  "risk_alerts": [
    {{
      "alert": "...",
      "severity": "CRITICAL|HIGH|MEDIUM|LOW",
      "rationale": "...",
      "recommended_action": "..."
    }}
  ],
  "follow_up_recommendations": [
    {{
      "recommendation": "...",
      "timeframe": "...",
      "rationale": "...",
      "evidence_source": "..."
    }}
  ],
  "pending_labs_or_referrals": ["..."],
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
        log.error("visit_prep_llm_error", error=str(e))
        state["error"] = str(e)
        state["llm_output"] = {}
    return state


def format_output_node(state: VisitPrepState) -> VisitPrepState:
    llm_out = state.get("llm_output", {})
    sources = list({r.get("source_system") for r in state["fhir_resources"]})
    state["final_summary"] = {
        "patient_id": state["patient_id"],
        "summary_type": "VISIT_PREP",
        "appointment_id": state.get("appointment_id"),
        "model_used": state.get("model_used", "unknown"),
        "content": llm_out,
        "sources": [{"source_system": s} for s in sources],
        "confidence_score": llm_out.get("overall_confidence_score", 0.0),
        "reasoning_summary": llm_out.get("reasoning_summary", ""),
        "input_hash": state["input_hash"],
        "fda_disclaimer": FDA_DISCLAIMER,
    }
    return state


def build_visit_prep_graph():
    graph = StateGraph(VisitPrepState)
    graph.add_node("filter_recent", filter_recent_events_node)
    graph.add_node("retrieve_rag", retrieve_rag_node)
    graph.add_node("generate_visit_brief", generate_visit_brief_node)
    graph.add_node("format_output", format_output_node)
    graph.set_entry_point("filter_recent")
    graph.add_edge("filter_recent", "retrieve_rag")
    graph.add_edge("retrieve_rag", "generate_visit_brief")
    graph.add_edge("generate_visit_brief", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


visit_prep_graph = build_visit_prep_graph()


async def run_visit_prep(patient_id: str, fhir_resources: list[dict], appointment_id: str | None = None, appointment_date: str | None = None) -> dict:
    result = await visit_prep_graph.ainvoke({
        "patient_id": patient_id,
        "appointment_id": appointment_id,
        "appointment_date": appointment_date,
        "fhir_resources": fhir_resources,
        "rag_chunks": [],
        "llm_output": {},
        "final_summary": {},
        "input_hash": "",
        "model_used": "",
        "error": None,
    })
    return result["final_summary"]
