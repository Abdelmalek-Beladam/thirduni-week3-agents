from __future__ import annotations

from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from tavily import TavilyClient


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(REPOSITORY_ROOT / ".env")

MODEL_NAME = "gemini-3.1-flash-lite"
SYSTEM_PROMPT = """You are a technical conference rehearsal assistant for researchers. Help the user organise and rehearse a clear presentation while preserving the accuracy of their work. Never invent experimental results, citations or claims. Use web search only when current external information is requested, cite the returned sources and clearly distinguish sourced facts from presentation advice. Remember the user’s topic, time limit and audience within the current thread. Keep suggestions realistic for the available presentation time."""

tavily_client = TavilyClient()


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for current, external evidence or presentation guidance.

    Use this only when the user asks for current information, recent evidence,
    or external guidance. Return titles, URLs, and result snippets for citation.
    Do not use search snippets as a substitute for checking what a source says,
    and do not invent findings, paper results, or citations.
    """
    return tavily_client.search(query)


def create_conference_rehearsal_agent(checkpointer: Any | None = None):
    """Create the Gemini rehearsal agent with an in-memory default saver."""
    return _build_conference_agent(checkpointer if checkpointer is not None else InMemorySaver())


def _build_conference_agent(checkpointer: Any | None):
    options = {
        "model": ChatGoogleGenerativeAI(model=MODEL_NAME),
        "tools": [web_search],
        "system_prompt": SYSTEM_PROMPT,
    }
    if checkpointer is not None:
        options["checkpointer"] = checkpointer
    return create_agent(**options)


def create_conference_rehearsal_studio_agent():
    """Create a graph that uses LangGraph API-managed thread persistence."""
    return _build_conference_agent(None)


def thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """Return LangGraph configuration for the requested conversation thread."""
    return {"configurable": {"thread_id": thread_id}}


agent = create_conference_rehearsal_studio_agent()
