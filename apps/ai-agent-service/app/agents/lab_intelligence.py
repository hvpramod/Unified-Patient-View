"""Lab Intelligence Agent — LangGraph workflow."""
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

CRITICAL_LAB_FLAGS = {"HH", "LL", "A"}
CRITICAL_LOINC_THRESHOLDS = {
    "2345-7": {"name": "Glucose", "critical_high": 500, "critical_low": 50},
    "17856-6": {"name": "HbA1c", "critical_high": 14.0, "critical_low": None},
    "2160-0": {"name": "Creatinine", "critical_high": 10.0, "critical_low": None},
    "6598-7": {"name": "Troponin T", "critical_high": 0.1, "critical_low": None},
    "2823-3": {"name": "Potassium", "critical_high": 6.5, "critical_low": 2.5},
    "2951-2": {"name": "Sodium", "critical_high": 155, "critical_low": 120},
}


class LabIntelState(TypedDict):
    patient_id: str
    fhir_resources: list[dict]
    critical_labs: list[dict]
    rag_chunks: list[dict]
    llm_output: dict
    final_summary: dict
    input_hash: str
    model_used: str
    has_critical: bool
    error: str | None


def flag_critical_values_node(state: LabIntelState) -> LabIntelState:
    obs = [r for r in state["fhir_resources"] if r.get("resource_type") == "Observation"]
    critical = []
    for obs_resource in obs:
        content = obs_resource.get("content", {})
        flag = content.get("interpretation", [{}])[0].get("text", "") if content.get("interpretation") else ""
        value = None
        try:
            value = float(content.get("valueQuantity", {}).get("value", 0) or 0)
        except (ValueError, TypeError):
            pass
        loinc = ""
        coding = content.get("code", {}).get("coding", [])
        if coding:
            loinc = coding[0].get("code", "")

        is_critical = flag in CRITICAL_LAB_FLAGS
        if not is_critical and loinc in CRITICAL_LOINC_THRESHOLDS and value:
            thresholds = CRITICAL_LOINC_THRESHOLDS[loinc]
            if thresholds.get("critical_high") and value >= thresholds["critical_high"]:
                is_critical = True
            if thresholds.get("critical_low") and value <= thresholds["critical_low"]:
                is_critical = True

        if is_critical:
            critical.append({**obs_resource, "_is_critical": True, "_flag": flag, "_value": value})

    state["critical_labs"] = critical
    state["has_critical"] = len(critical) > 0
    state["input_hash"] = compute_input_hash({"patient_id": state["patient_id"], "obs": obs})
    return state


async def retrieve_rag_node(state: LabIntelState) -> LabIntelState:
    test_names = []
    for r in state["fhir_resources"]:
        if r.get("resource_type") == "Observation":
            name = r.get("content", {}).get("code", {}).get("text", "")
            if name:
                test_names.append(name)
    query = f"lab result interpretation and clinical significance: {', '.join(set(test_names[:8]))}"
    state["rag_chunks"] = await retrieve_guidelines(query)
    return state


async def generate_lab_intel_node(state: LabIntelState) -> LabIntelState:
    system_prompt = build_system_prompt("Laboratory Intelligence Specialist")
    fhir_context = format_fhir_context(state["fhir_resources"], ["Observation", "DiagnosticReport"])
    rag_context = format_rag_context(state["rag_chunks"])

    task_prompt = f"""
{fhir_context}

{rag_context}

TASK: Analyze all lab results for patient {state['patient_id']}.

Return JSON:
{{
  "critical_values": [
    {{
      "test_name": "...",
      "value": "...",
      "unit": "...",
      "reference_range": "...",
      "interpretation": "...",
      "clinical_significance": "...",
      "recommended_action": "...",
      "source": "...",
      "collected_at": "..."
    }}
  ],
  "trends": [
    {{
      "test_name": "...",
      "trend_direction": "INCREASING|DECREASING|STABLE",
      "values": [{{"value": 0, "date": "...", "source": "..."}}],
      "clinical_implication": "..."
    }}
  ],
  "abnormal_values": [
    {{
      "test_name": "...",
      "value": "...",
      "expected_range": "...",
      "significance": "..."
    }}
  ],
  "summary_narrative": "...",
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
        log.warning("lab_intel_llm_error", error=str(e))
        state["error"] = str(e)
        state["llm_output"] = {}
    return state


def format_output_node(state: LabIntelState) -> LabIntelState:
    llm_out = state.get("llm_output", {})
    sources = list({r.get("source_system") for r in state["fhir_resources"]})
    state["final_summary"] = {
        "patient_id": state["patient_id"],
        "summary_type": "LAB_INTELLIGENCE",
        "model_used": state.get("model_used", "unknown"),
        "content": llm_out,
        "sources": [{"source_system": s} for s in sources],
        "confidence_score": llm_out.get("overall_confidence_score", 0.0),
        "reasoning_summary": llm_out.get("reasoning_summary", ""),
        "input_hash": state["input_hash"],
        "has_critical_values": state["has_critical"],
        "fda_disclaimer": FDA_DISCLAIMER,
    }
    return state


def build_lab_intel_graph():
    graph = StateGraph(LabIntelState)
    graph.add_node("flag_critical", flag_critical_values_node)
    graph.add_node("retrieve_rag", retrieve_rag_node)
    graph.add_node("generate_lab_intel", generate_lab_intel_node)
    graph.add_node("format_output", format_output_node)
    graph.set_entry_point("flag_critical")
    graph.add_edge("flag_critical", "retrieve_rag")
    graph.add_edge("retrieve_rag", "generate_lab_intel")
    graph.add_edge("generate_lab_intel", "format_output")
    graph.add_edge("format_output", END)
    return graph.compile()


lab_intel_graph = build_lab_intel_graph()


async def run_lab_intelligence(patient_id: str, fhir_resources: list[dict]) -> dict:
    result = await lab_intel_graph.ainvoke({
        "patient_id": patient_id,
        "fhir_resources": fhir_resources,
        "critical_labs": [],
        "rag_chunks": [],
        "llm_output": {},
        "final_summary": {},
        "input_hash": "",
        "model_used": "",
        "has_critical": False,
        "error": None,
    })
    return result["final_summary"]
