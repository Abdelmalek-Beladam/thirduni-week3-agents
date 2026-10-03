from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path
from pprint import pprint

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "my-work" / "module2_multi_agent"))

from langchain.messages import AIMessage, HumanMessage, ToolMessage

from local_trace import LocalTraceHandler, save_trace
from conference_team import build_conference_team, initial_state


PROJECT_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = PROJECT_DIR / "conference_demo_output.txt"
STATE_PATH = PROJECT_DIR / "conference_state_snapshots.json"
BRIEF = (
    "My name is Abdelmalek. I am preparing an eight-minute presentation about vehicle "
    "tyre-pressure monitoring using machine learning for a mixed technical/non-technical "
    "audience. I have not supplied experimental results. Research why evaluation on unseen "
    "data matters, create an eight-minute presentation outline, and prepare five likely audience questions."
)
FOLLOW_UP = "Make the questions easier for non-technical attendees. Keep the outline and evidence unchanged."


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
        "user_name", "topic", "presentation_minutes", "audience", "experimental_results_supplied",
        "brief_status", "evidence_status", "evidence_searches_used", "structure_status",
        "structure_runs_used", "questions_status", "question_runs_used",
    )
    return {key: values.get(key) for key in keys}


async def main() -> None:
    trace_id = str(uuid.uuid4())
    trace = LocalTraceHandler(trace_id, "conference_demo")
    coordinator = build_conference_team(trace_id, trace)
    config = {
        "configurable": {"thread_id": "conference-team-session-1"},
        "callbacks": [trace],
        "metadata": {"local_trace_id": trace_id, "stage": "conference_demo"},
        "run_name": "conference_coordinator",
        "recursion_limit": 30,
    }
    state_before = coordinator.get_state(config).values
    print("State before initial brief:")
    pprint(state_summary(state_before))

    brief_fields = {
        **initial_state(),
        "user_name": "Abdelmalek",
        "topic": "vehicle tyre-pressure monitoring using machine learning",
        "presentation_minutes": 8,
        "audience": "mixed technical/non-technical",
        "experimental_results_supplied": False,
        "brief_status": "complete",
    }
    coordinator.update_state(config, brief_fields)
    state_after_brief = coordinator.get_state(config).values
    print("\nState after brief saved before delegation:")
    pprint(state_summary(state_after_brief))

    initial_result = await coordinator.ainvoke(
        {"messages": [HumanMessage(content=BRIEF)]},
        config=config,
    )
    show_messages("Initial conference preparation", initial_result["messages"])
    state_after_initial = coordinator.get_state(config).values
    print("\nState after initial delegation:")
    pprint(state_summary(state_after_initial))

    follow_result = await coordinator.ainvoke(
        {"messages": [HumanMessage(content=FOLLOW_UP)]},
        config=config,
    )
    show_messages("Question-only follow-up", follow_result["messages"])
    state_after_follow_up = coordinator.get_state(config).values
    print("\nState after follow-up:")
    pprint(state_summary(state_after_follow_up))

    snapshots = {
        "before_initial": state_summary(state_before),
        "after_brief_saved_before_delegation": state_summary(state_after_brief),
        "after_initial": state_summary(state_after_initial),
        "after_follow_up": state_summary(state_after_follow_up),
        "evidence_searches_repeated": state_after_follow_up.get("evidence_searches_used", 0) > state_after_initial.get("evidence_searches_used", 0),
        "outline_rebuilt": state_after_follow_up.get("structure_runs_used", 0) > state_after_initial.get("structure_runs_used", 0),
        "questions_repeated": state_after_follow_up.get("question_runs_used", 0) > state_after_initial.get("question_runs_used", 0),
    }
    STATE_PATH.write_text(json.dumps(snapshots, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    trace_json, trace_timeline = save_trace(trace, PROJECT_DIR / "traces", "conference_demo")
    print(f"\nTrace JSON: {trace_json}")
    print(f"Trace timeline: {trace_timeline}")
    print(f"State snapshots: {STATE_PATH}")
    pprint({key: snapshots[key] for key in ("evidence_searches_repeated", "outline_rebuilt", "questions_repeated")})


if __name__ == "__main__":
    asyncio.run(main())
