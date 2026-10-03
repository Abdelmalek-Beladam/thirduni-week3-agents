from __future__ import annotations

import asyncio
import json
import sqlite3
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_mcp_adapters.client import MultiServerMCPClient
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from tavily import TavilyClient

from local_trace import LocalTraceHandler, save_trace


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
RESOURCE_DB = PROJECT_ROOT / "notebooks" / "module-2" / "resources" / "Chinook.db"
MODEL_NAME = "gemini-3.1-flash-lite"


class WeddingState(AgentState):
    origin: str
    destination: str
    event_date: str
    outbound_date: str
    return_date: str
    guest_count: int
    flight_adults: int
    genre: str
    brief_status: str
    travel_status: str
    travel_result: str
    travel_searches_used: int
    venue_status: str
    venue_result: str
    venue_searches_used: int
    dj_status: str
    dj_result: str


@dataclass
class KiwiConnection:
    client: MultiServerMCPClient
    tools: list[Any]
    search_tool: Any | None
    discovery: dict[str, Any]


async def discover_kiwi() -> KiwiConnection:
    client = MultiServerMCPClient(
        {
            "travel_server": {
                "transport": "streamable_http",
                "url": "https://mcp.kiwi.com",
            }
        }
    )
    tools = await asyncio.wait_for(client.get_tools(), timeout=25)
    discovery = {
        "status": "ok",
        "transport": "streamable_http",
        "endpoint": "https://mcp.kiwi.com",
        "allowed_travel_tools": ["search-flight"],
        "rejected_tools": [
            tool_item.name for tool_item in tools if tool_item.name != "search-flight"
        ],
        "tools": [
            {
                "name": tool_item.name,
                "description": tool_item.description,
                "args": tool_item.args,
            }
            for tool_item in tools
        ],
    }
    search_tool = next((item for item in tools if item.name == "search-flight"), None)
    return KiwiConnection(client, tools, search_tool, discovery)


def _tool_message(content: str, runtime: ToolRuntime) -> ToolMessage:
    return ToolMessage(content=content, tool_call_id=runtime.tool_call_id)


def _state_text(state: dict[str, Any], keys: tuple[str, ...]) -> dict[str, Any]:
    return {key: state.get(key) for key in keys}


def build_wedding_team(kiwi: KiwiConnection, trace_id: str, trace: LocalTraceHandler):
    model = ChatGoogleGenerativeAI(model=MODEL_NAME)
    tavily_client = TavilyClient()
    venue_search_count = {"count": 0}

    @tool
    async def search_flights_from_brief(
        origin: str,
        destination: str,
        outbound_date: str,
        return_date: str,
        flight_adults: int,
    ) -> dict[str, Any]:
        """Search Kiwi with explicit brief fields; never book or submit data."""
        if kiwi.search_tool is None:
            return {"status": "error", "message": "Kiwi MCP did not expose search-flight."}
        args = {
            "flyFrom": origin,
            "flyTo": destination,
            "departureDate": outbound_date,
            "returnDate": return_date,
            "adults": flight_adults,
        }
        try:
            result = await kiwi.search_tool.ainvoke(args)
            return {"status": "completed_search_only", "search_args": args, "result": result}
        except Exception as error:
            return {"status": "error", "search_args": args, "message": f"{type(error).__name__}: {error}"}

    async def travel_agent_tool(runtime: ToolRuntime) -> Command:
        """Delegate search-only travel work with explicit saved brief fields."""
        state = runtime.state
        if state.get("travel_status") == "completed_search_only":
            report = state.get("travel_result", "Travel search already completed for this thread.")
            return Command(update={"travel_result": report, "messages": [_tool_message(report, runtime)]})
        specialist = create_agent(
            model=model,
            tools=[search_flights_from_brief],
            system_prompt=(
                "You are a travel search specialist. Use search_flights_from_brief exactly once "
                "with the explicit fields in the user request. Search only. Never book, reserve, "
                "purchase, submit passenger details, or follow booking links. Preserve currency, "
                "dates, passenger count, price basis, and limitations."
            ),
        )
        config = {
            "callbacks": [trace],
            "metadata": {"local_trace_id": trace_id, "component": "travel_specialist"},
        }
        result = await specialist.ainvoke(
            {"messages": [HumanMessage(content=(
                "Search flights using these saved brief fields: "
                f"origin={state['origin']}; destination={state['destination']}; "
                f"outbound_date={state['outbound_date']}; return_date={state['return_date']}; "
                f"flight_adults={state['flight_adults']}."
            ))]},
            config=config,
        )
        report = result["messages"][-1].content
        return Command(update={
            "travel_status": "completed_search_only" if "error" not in str(report).lower() else "error",
            "travel_result": str(report),
            "travel_searches_used": state.get("travel_searches_used", 0) + 1,
            "messages": [_tool_message(str(report), runtime)],
        })

    @tool
    async def search_flights(runtime: ToolRuntime) -> Command:
        """Run the model-backed travel specialist using the saved brief."""
        return await travel_agent_tool(runtime)

    @tool
    def search_venues(runtime: ToolRuntime) -> Command:
        """Delegate venue research with explicit destination and guest count."""
        state = runtime.state
        if state.get("venue_status") == "completed_candidates":
            report = state.get("venue_result", "Venue search already completed for this thread.")
            return Command(update={"venue_result": report, "messages": [_tool_message(report, runtime)]})
        specialist = create_agent(
            model=model,
            tools=[],
            system_prompt=(
                "You are a venue specialist. Use the supplied Tavily candidate records only. "
                "Do not claim price, capacity, or availability unless the records explicitly support it. "
                "Preserve exact URLs and label every candidate as unconfirmed."
            ),
        )
        reports: list[dict[str, Any]] = []
        for query in (
            f"wedding venues in {state['destination']} for {state['guest_count']} guests",
            f"wedding venue {state['destination']} capacity {state['guest_count']} price availability",
        ):
            if venue_search_count["count"] >= 2:
                break
            venue_search_count["count"] += 1
            try:
                result = tavily_client.search(query)
                for item in result.get("results", [])[:3]:
                    reports.append({
                        "title": item.get("title"),
                        "url": item.get("url"),
                        "snippet": item.get("content"),
                        "capacity": "unknown unless explicitly supported by snippet",
                        "price": "unknown unless explicitly supported by snippet",
                        "availability": "unknown",
                        "candidate_only": True,
                    })
            except Exception as error:
                reports.append({"error": f"Tavily error: {type(error).__name__}: {error}"})
        evidence = json.dumps({"searches_used": venue_search_count["count"], "candidates": reports}, ensure_ascii=False)
        response = specialist.invoke({"messages": [HumanMessage(content=(
            f"For destination={state['destination']} and guest_count={state['guest_count']}, "
            f"summarize these unverified search candidates without adding facts: {evidence}"
        ))]})
        payload = json.dumps({"evidence": reports, "specialist_summary": response["messages"][-1].content}, ensure_ascii=False)
        return Command(update={
            "venue_status": "completed_candidates" if reports else "error",
            "venue_result": payload,
            "venue_searches_used": venue_search_count["count"],
            "messages": [_tool_message(payload, runtime)],
        })

    @tool
    def suggest_playlist(runtime: ToolRuntime) -> Command:
        """Delegate a database-backed playlist request with an explicit genre."""
        genre = str(runtime.state["genre"])
        specialist = create_agent(
            model=model,
            tools=[],
            system_prompt=(
                "You are a DJ specialist. Summarize only the supplied database rows. "
                "Do not invent tempo, suitability, licensing, availability, or fees."
            ),
        )
        connection = sqlite3.connect(f"file:{RESOURCE_DB}?mode=ro", uri=True)
        try:
            query = """
                SELECT Track.Name, Artist.Name, Genre.Name, Track.Milliseconds
                FROM Track
                JOIN Album ON Album.AlbumId = Track.AlbumId
                JOIN Artist ON Artist.ArtistId = Album.ArtistId
                JOIN Genre ON Genre.GenreId = Track.GenreId
                WHERE lower(Genre.Name) = lower(?)
                ORDER BY Track.Name
                LIMIT 8
            """
            rows = connection.execute(query, (genre,)).fetchall()
            items = [
                {
                    "track_name": row[0],
                    "artist": row[1],
                    "genre": row[2],
                    "duration_seconds": round(row[3] / 1000, 2),
                    "note": "Track.UnitPrice is not a DJ fee or licensing cost.",
                }
                for row in rows
            ]
            evidence = {"genre": genre, "tracks": items}
            response = specialist.invoke({"messages": [HumanMessage(content=(
                f"Summarize this read-only playlist data for genre {genre}; do not add facts: "
                f"{json.dumps(evidence, ensure_ascii=False)}"
            ))]})
            payload = json.dumps({**evidence, "specialist_summary": response["messages"][-1].content}, ensure_ascii=False)
        except Exception as error:
            payload = json.dumps({"genre": genre, "error": f"SQLite error: {type(error).__name__}: {error}"})
        finally:
            connection.close()
        return Command(update={
            "dj_status": "completed_database_query",
            "dj_result": payload,
            "messages": [_tool_message(payload, runtime)],
        })

    @tool
    def update_brief(
        origin: str,
        destination: str,
        event_date: str,
        outbound_date: str,
        return_date: str,
        guest_count: int,
        flight_adults: int,
        genre: str,
        runtime: ToolRuntime,
    ) -> Command:
        """Save the complete planning brief before delegating to specialists."""
        return Command(update={
            "origin": origin,
            "destination": destination,
            "event_date": event_date,
            "outbound_date": outbound_date,
            "return_date": return_date,
            "guest_count": guest_count,
            "flight_adults": flight_adults,
            "genre": genre,
            "brief_status": "complete",
            "messages": [_tool_message("Planning brief saved.", runtime)],
        })

    coordinator = create_agent(
        model=model,
        tools=[update_brief, search_flights, search_venues, suggest_playlist],
        state_schema=WeddingState,
        checkpointer=InMemorySaver(),
        system_prompt=(
            "You are a wedding coordinator. First save a complete planning brief with update_brief. "
            "Do not delegate until that update has returned. Then delegate sequentially to all three "
            "specialists exactly once: search_flights, search_venues, and suggest_playlist. On a follow-up "
            "that changes only the genre, update the brief genre and call only suggest_playlist. Preserve "
            "missing data, source URLs, price basis, errors, and unknown venue fields. Never book or reserve "
            "anything. Never claim venue capacity, price, availability, licensing, or flight booking unless "
            "the tool result explicitly supports it."
        ),
    )
    return coordinator


def initial_state() -> dict[str, Any]:
    return {
        "messages": [],
        "origin": "",
        "destination": "",
        "event_date": "",
        "outbound_date": "",
        "return_date": "",
        "guest_count": 0,
        "flight_adults": 0,
        "genre": "",
        "brief_status": "not_started",
        "travel_status": "not_started",
        "travel_result": "",
        "travel_searches_used": 0,
        "venue_status": "not_started",
        "venue_result": "",
        "venue_searches_used": 0,
        "dj_status": "not_started",
        "dj_result": "",
    }
