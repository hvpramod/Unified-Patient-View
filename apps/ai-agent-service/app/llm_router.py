"""LLM routing strategy — Claude for reasoning, GPT-4o for summarization."""
from __future__ import annotations
from enum import Enum
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
import structlog

from app.config import settings

log = structlog.get_logger()


class LLMTask(str, Enum):
    REASONING = "reasoning"        # Conflict explanation, reconciliation → Claude
    SUMMARIZATION = "summarization"  # Clinical summary, visit prep → GPT-4o


def get_llm(task: LLMTask):
    """Return the appropriate LLM for the given task type."""
    if task == LLMTask.REASONING:
        return ChatAnthropic(
            model=settings.anthropic_model_reasoning,
            api_key=settings.anthropic_api_key,
            temperature=0.1,
            max_tokens=4096,
        )
    return ChatOpenAI(
        model=settings.openai_model_summarization,
        api_key=settings.openai_api_key,
        temperature=0.1,
        max_tokens=4096,
    )


def get_fallback_llm(task: LLMTask):
    """Fallback: swap primary for secondary."""
    if task == LLMTask.REASONING:
        return ChatOpenAI(
            model=settings.openai_model_summarization,
            api_key=settings.openai_api_key,
            temperature=0.1,
        )
    return ChatAnthropic(
        model=settings.anthropic_model_reasoning,
        api_key=settings.anthropic_api_key,
        temperature=0.1,
    )
