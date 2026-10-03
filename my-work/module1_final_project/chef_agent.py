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
SYSTEM_PROMPT = """You are a practical personal chef assistant.

Work primarily with the ingredients the user says they have. Ask concise follow-up questions about dietary restrictions, available equipment, and preparation time when those details are missing and needed to recommend a suitable meal.

Use the web_search tool to find actual recipe options. Do not invent a recipe source. When search is used, include the source name and URL for each recipe option. Clearly distinguish information supported by a recipe source from your own practical suggestions or substitutions.

Never claim a recipe satisfies an allergy unless you have checked the recipe's ingredients. If ingredients or cross-contamination details are unavailable, say so and ask the user to verify.

Keep responses practical and concise. Remember ingredients, preferences, restrictions, equipment, and time constraints within the current conversation thread."""

tavily_client = TavilyClient()


@tool
def web_search(query: str) -> dict[str, Any]:
    """Find real web recipes relevant to the user's ingredients and constraints.

    Use this when the user asks for recipe ideas or recipe instructions. Return
    search result titles, URLs, and snippets so the assistant can cite the actual
    recipe source. Never treat a result snippet as proof of allergy safety.
    """
    return tavily_client.search(query)


def create_chef_agent(checkpointer: Any | None = None):
    """Create the Gemini personal-chef agent with an in-memory default saver."""
    return _build_chef_agent(checkpointer if checkpointer is not None else InMemorySaver())


def _build_chef_agent(checkpointer: Any | None):
    options = {
        "model": ChatGoogleGenerativeAI(model=MODEL_NAME),
        "tools": [web_search],
        "system_prompt": SYSTEM_PROMPT,
    }
    if checkpointer is not None:
        options["checkpointer"] = checkpointer
    return create_agent(**options)


def create_chef_studio_agent():
    """Create a graph that uses LangGraph API-managed thread persistence."""
    return _build_chef_agent(None)


def thread_config(thread_id: str) -> dict[str, dict[str, str]]:
    """Return LangGraph configuration for the requested conversation thread."""
    return {"configurable": {"thread_id": thread_id}}


agent = create_chef_studio_agent()
