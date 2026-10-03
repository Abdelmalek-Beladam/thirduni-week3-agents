from __future__ import annotations

import asyncio
import json
import re
import sys
import uuid
from pathlib import Path
from pprint import pprint

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from langchain.messages import AIMessage, HumanMessage, ToolMessage

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "my-work" / "module2_multi_agent"))

from local_trace import LocalTraceHandler, save_trace
from wedding_team import build_wedding_team, discover_kiwi, initial_state


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "wedding_demo_output.txt"
DISCOVERY_PATH = PROJECT_DIR / "kiwi_tool_discovery.json"
STATE_PATH = PROJECT_DIR / "wedding_state_snapshots.json"

BRIEF = (
    "Plan a destination wedding in Paris on 15 May 2027. Departure city is Algiers. "
    "Outbound flight date is 13 May 2027 and return date is 17 May 2027. There are 30 "
    "adult guests, but search flights for two adults only. Find venue candidates for 30 "
    "guests. Suggest up to eight Jazz tracks from the music database. Do not book anything. "
    "Clearly report unknown prices, capacity and availability."
)
FOLLOW_UP = "Change the music genre to Rock, keep the other details, and update only the playlist."


def text_of(message) -> str:
    content = getattr(message, "content", message)
    if isinstance(content, str):
        return content
    return str(content)


def show_messages(label: str, messages: list) -> None:
    print(f"\n===== {label} =====")
    for index, message in enumerate(messages, start=1):
        if isinstance(message, HumanMessage):
            role = "HUMAN MESSAGE"
        elif isinstance(message, AIMessage) and message.tool_calls:
            role = "AI TOOL CALL"
        elif isinstance(message, ToolMessage):
            role = "TOOL RESULT"
        elif isinstance(message, AIMessage):
            role = "AI ANSWER"
        else:
            role = type(message).__name__.upper()
        print(f"\n--- Message {index}: {role} ---")
        pprint(message)


def state_summary(values: dict) -> dict:
    keys = (
        "origin", "destination", "event_date", "outbound_date", "return_date",
        "guest_count", "flight_adults", "genre", "brief_status", "travel_status",
        "travel_searches_used", "venue_status", "venue_searches_used", "dj_status",
    )
    return {key: values.get(key) for key in keys}


async def main() -> None:
    discovery = None
    kiwi_error = None
    try:
        kiwi = await discover_kiwi()
        discovery = kiwi.discovery
    except Exception as error:
        kiwi = None
        kiwi_error = {"type": type(error).__name__, "message": str(error)}
        discovery = {
            "status": "error",
            "transport": "streamable_http",
            "endpoint": "https://mcp.kiwi.com",
            "error": kiwi_error,
        }
    DISCOVERY_PATH.write_text(json.dumps(discovery, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    print("Kiwi discovery:")
    print(json.dumps(discovery, indent=2, ensure_ascii=False, default=str))

    if kiwi is None:
        print("Kiwi unavailable; the full wedding demonstration is incomplete.")
        return

    trace_id = str(uuid.uuid4())
    trace = LocalTraceHandler(trace_id, "wedding_demo")
    coordinator = build_wedding_team(kiwi, trace_id, trace)
    config = {
        "configurable": {"thread_id": "wedding-demo-session-1"},
        "callbacks": [trace],
        "metadata": {"local_trace_id": trace_id, "stage": "wedding_demo"},
        "run_name": "wedding_coordinator",
        "recursion_limit": 35,
    }
    state_before = coordinator.get_state(config).values
    print("\nState before initial run:")
    pprint(state_summary(state_before))

    brief_fields = {
        **initial_state(),
        "origin": "Algiers",
        "destination": "Paris",
        "event_date": "15/05/2027",
        "outbound_date": "13/05/2027",
        "return_date": "17/05/2027",
        "guest_count": 30,
        "flight_adults": 2,
        "genre": "Jazz",
        "brief_status": "complete",
    }
    coordinator.update_state(config, brief_fields)
    state_after_brief = coordinator.get_state(config).values
    print("\nState after brief was saved before delegation:")
    pprint(state_summary(state_after_brief))

    initial_result = await coordinator.ainvoke(
        {"messages": [HumanMessage(content=BRIEF)]},
        config=config,
    )
    show_messages("Initial wedding plan", initial_result["messages"])
    state_after_initial = coordinator.get_state(config).values
    print("\nState after initial run:")
    pprint(state_summary(state_after_initial))

    coordinator.update_state(config, {"genre": "Rock"})
    follow_result = await coordinator.ainvoke(
        {"messages": [HumanMessage(content=FOLLOW_UP)]},
        config=config,
    )
    show_messages("Rock playlist follow-up", follow_result["messages"])
    state_after_follow_up = coordinator.get_state(config).values
    print("\nState after follow-up:")
    pprint(state_summary(state_after_follow_up))

    state_snapshots = {
        "before_initial": state_summary(state_before),
        "after_brief_saved_before_delegation": state_summary(state_after_brief),
        "after_initial": state_summary(state_after_initial),
        "after_follow_up": state_summary(state_after_follow_up),
        "travel_searches_repeated_on_follow_up": (
            state_after_follow_up.get("travel_searches_used", 0)
            > state_after_initial.get("travel_searches_used", 0)
        ),
        "venue_searches_repeated_on_follow_up": (
            state_after_follow_up.get("venue_searches_used", 0)
            > state_after_initial.get("venue_searches_used", 0)
        ),
    }
    STATE_PATH.write_text(json.dumps(state_snapshots, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")
    trace_json, trace_timeline = save_trace(trace, PROJECT_DIR / "traces", "wedding_demo")
    print(f"\nTrace JSON: {trace_json}")
    print(f"Trace timeline: {trace_timeline}")
    print(f"State snapshots: {STATE_PATH}")
    print("Travel searches repeated on follow-up:", state_snapshots["travel_searches_repeated_on_follow_up"])
    print("Venue searches repeated on follow-up:", state_snapshots["venue_searches_repeated_on_follow_up"])


if __name__ == "__main__":
    asyncio.run(main())
