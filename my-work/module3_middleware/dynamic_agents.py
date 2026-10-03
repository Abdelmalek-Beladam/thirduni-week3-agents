"""Module 3 - Dynamic Agents.

Part A: dynamic prompt switched by the user's language in runtime context.
Part B: the read-only Chinook SQL tool is hidden from external users.
Part C: model switch after more than 10 messages, with token counts.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, ModelResponse, dynamic_prompt, wrap_model_call
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import tool
from langchain_community.utilities import SQLDatabase
from tavily import TavilyClient

from common import CHINOOK, LARGE_MODEL, STANDARD_MODEL, header, last_ai, make_model, start_log, text_of, usage

start_log("dynamic_agents_output.txt")


# ---------------------------------------------------------------- Part A
@dataclass
class LanguageContext:
    user_language: str = "English"


@dynamic_prompt
def language_prompt(request: ModelRequest) -> str:
    base = "You are a helpful conference rehearsal assistant. Answer in two sentences."
    language = request.runtime.context.user_language
    return base if language == "English" else f"{base} Only respond in {language}."


def run_part_a() -> None:
    header("PART A - dynamic prompt by language")
    agent = create_agent(model=make_model(), context_schema=LanguageContext, middleware=[language_prompt])
    for language in ["English", "French", "Arabic"]:
        response = agent.invoke(
            {"messages": [HumanMessage("Give me one tip for presenting to a mixed audience.")]},
            context=LanguageContext(user_language=language),
        )
        print(f"\n[{language}]", text_of(last_ai(response["messages"])))


# ---------------------------------------------------------------- Part B
tavily_client = TavilyClient()
db = SQLDatabase.from_uri(f"sqlite:///file:{CHINOOK.as_posix()}?mode=ro&uri=true")
TAVILY_CALLS = {"count": 0}


@tool
def web_search(query: str) -> dict[str, Any]:
    """Search the web for information."""
    TAVILY_CALLS["count"] += 1
    return tavily_client.search(query, max_results=2)


@tool
def sql_query(query: str) -> str:
    """Obtain information from the music store database using read-only SQL queries."""
    try:
        return db.run(query)
    except Exception as error:
        return f"Error: {error}"


@dataclass
class UserRole:
    user_role: str = "external"


@wrap_model_call
def role_based_tools(request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ModelResponse:
    if request.runtime.context.user_role != "internal":
        request = request.override(tools=[web_search])
    print("  [wrap_model_call] tools offered to model:", [t.name for t in request.tools])
    return handler(request)


def run_part_b() -> None:
    header("PART B - hide the database tool from external users")
    agent = create_agent(
        model=make_model(), tools=[web_search, sql_query], middleware=[role_based_tools], context_schema=UserRole
    )
    question = "How many artists are in the Chinook music store database? Use the database if you can."
    for role in ["external", "internal"]:
        print(f"\n[{role} user]")
        response = agent.invoke({"messages": [HumanMessage(question)]}, context=UserRole(user_role=role))
        called = [c["name"] for m in response["messages"] if m.type == "ai" for c in m.tool_calls]
        print("  tools actually called:", called)
        print("  answer:", text_of(last_ai(response["messages"])))
    print("\nTavily searches used:", TAVILY_CALLS["count"])
    print("Reference count from the database:", db.run("SELECT COUNT(*) FROM Artist"))


# ---------------------------------------------------------------- Part C
def run_part_c() -> None:
    header(f"PART C - model switch: {STANDARD_MODEL} -> {LARGE_MODEL} after 10 messages")
    standard_model = make_model(STANDARD_MODEL)
    large_model = make_model(LARGE_MODEL)
    try:
        large_model.invoke("Reply with OK.")
    except Exception as error:
        print(f"Large model '{LARGE_MODEL}' is not available with this key: {type(error).__name__}: {error}")
        print("Set MODULE3_LARGE_MODEL in .env to a Gemini model your key can use, then rerun.")
        return

    @wrap_model_call
    def state_based_model(request: ModelRequest, handler: Callable[[ModelRequest], ModelResponse]) -> ModelResponse:
        count = len(request.messages)
        chosen = large_model if count > 10 else standard_model
        print(f"  [wrap_model_call] {count} messages -> {chosen.model}")
        return handler(request.override(model=chosen))

    agent = create_agent(
        model=standard_model, middleware=[state_based_model],
        system_prompt="You are roleplaying a helpful office intern. Answer in one sentence.",
    )
    short = [HumanMessage("Did you water the office plant today?")]
    long = [
        HumanMessage("Did you water the office plant today?"), AIMessage("Yes, a light watering this morning."),
        HumanMessage("Has it grown much this week?"), AIMessage("Two new leaves since Monday."),
        HumanMessage("Are the leaves still yellow on the edges?"), AIMessage("A little, but it looks healthier."),
        HumanMessage("Did you rotate the pot toward the window?"), AIMessage("A quarter turn for even light."),
        HumanMessage("How often should we fertilise it?"), AIMessage("About every two weeks, diluted."),
        HumanMessage("When should we expect to replace the pot?"),
    ]
    rows = []
    for label, messages in [("short (1 message)", short), ("long (11 messages)", long)]:
        response = agent.invoke({"messages": messages})
        final = last_ai(response["messages"])
        rows.append((label, final.response_metadata.get("model_name"), usage(final)))
        print(f"\n{label}:", text_of(final))
    print("\nSide by side:")
    for label, model_name, tokens in rows:
        print(f"  {label:20} model={model_name}  tokens={tokens}")


if __name__ == "__main__":
    run_part_a()
    run_part_b()
    run_part_c()
