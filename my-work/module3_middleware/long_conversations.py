"""Module 3 - Managing Long Conversations.

Part A: summarisation middleware on a deliberately long conversation.
Part B: a before_agent hook that removes a sensor tool result, proved by asking
        a question only the removed content can answer.
Both parts print token usage with and without the middleware.
"""
from __future__ import annotations

from typing import Any

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import SummarizationMiddleware, before_agent
from langchain.messages import AIMessage, HumanMessage, RemoveMessage, ToolMessage
from langchain.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.runtime import Runtime

from common import header, last_ai, make_model, start_log, text_of, usage

start_log("long_conversations_output.txt")

# ---------------------------------------------------------------- Part A
LONG_CONVERSATION = [
    HumanMessage("I am rehearsing a talk about an imaginary drone delivery town called Sidi Rotor."),
    AIMessage("Sidi Rotor sounds fun. What do you want to cover first?"),
    HumanMessage("Sidi Rotor has 40 delivery drones and one charging hub near the market."),
    AIMessage("Noted: 40 drones and a single charging hub near the market."),
    HumanMessage("The drones avoid the old mosque square because of the minaret height."),
    AIMessage("So the routing has a no-fly zone around the mosque square."),
    HumanMessage("The mayor wants night deliveries, but residents complain about noise."),
    AIMessage("That is a classic trade-off between service hours and noise."),
    HumanMessage("The hub can only charge 12 drones at the same time."),
    AIMessage("Then charging capacity limits how many drones can fly at peak hours."),
    HumanMessage("Summarise the main operational constraint I should mention in one sentence."),
]


def run_part_a() -> None:
    header("PART A - Summarisation middleware")
    model = make_model()

    baseline = create_agent(model=model, checkpointer=InMemorySaver())
    base = baseline.invoke({"messages": list(LONG_CONVERSATION)}, {"configurable": {"thread_id": "a-baseline"}})
    print("Baseline messages in state:", len(base["messages"]))
    print("Baseline answer:", text_of(last_ai(base["messages"])))
    print("Baseline token usage:", usage(last_ai(base["messages"])))

    summarising = create_agent(
        model=model,
        checkpointer=InMemorySaver(),
        middleware=[
            SummarizationMiddleware(
                model=make_model(),
                trigger=("tokens", 150),
                keep=("messages", 1),
            )
        ],
    )
    summ = summarising.invoke({"messages": list(LONG_CONVERSATION)}, {"configurable": {"thread_id": "a-summary"}})
    print("\nSummarised messages in state:", len(summ["messages"]))
    print("First message after summarisation (where it cut):")
    print(text_of(summ["messages"][0]))
    print("\nSummarised answer:", text_of(last_ai(summ["messages"])))
    print("Main-agent token usage after summarisation:", usage(last_ai(summ["messages"])))
    print("Note: the summariser model call has its own cost, which is not included in the line above.")


# ---------------------------------------------------------------- Part B
@tool
def read_tyre_sensor() -> str:
    """Read the current tyre sensor values."""
    return "Sensor offline. No new reading available."


def sensor_conversation():
    return [
        HumanMessage("My car shows a tyre-pressure warning."),
        AIMessage(content="", tool_calls=[{"name": "read_tyre_sensor", "args": {}, "id": "sensor_call_1"}]),
        ToolMessage("sensor_id=TPMS-7 front_left=1.6 bar temperature=41C", tool_call_id="sensor_call_1"),
        AIMessage("The front-left tyre looks low. Have you checked it?"),
        HumanMessage("Yes, I checked it."),
        HumanMessage("From the earlier sensor reading only, what exact temperature did it report? If you do not have it, say so."),
    ]


@before_agent
def remove_old_tool_results(state: AgentState, runtime: Runtime) -> dict[str, Any] | None:
    """Remove tool results and the AI messages that requested them.

    Gemini expects every function call to be followed by its result, so the
    requesting AI message is removed together with its ToolMessage.
    """
    to_remove = [
        m for m in state["messages"]
        if isinstance(m, ToolMessage) or (isinstance(m, AIMessage) and m.tool_calls)
    ]
    print(f"[before_agent] removing {len(to_remove)} messages:", [type(m).__name__ for m in to_remove])
    return {"messages": [RemoveMessage(id=m.id) for m in to_remove]}


def run_part_b() -> None:
    header("PART B - before_agent hook removes the sensor tool result")
    model = make_model()

    baseline = create_agent(model=model, tools=[read_tyre_sensor], checkpointer=InMemorySaver())
    base = baseline.invoke({"messages": sensor_conversation()}, {"configurable": {"thread_id": "b-baseline"}})
    base_answer = text_of(last_ai(base["messages"]))
    print("Without hook - answer:", base_answer)
    print("Without hook - mentions 41:", "41" in base_answer)
    print("Without hook - token usage:", usage(last_ai(base["messages"])))

    trimmed = create_agent(
        model=model, tools=[read_tyre_sensor], checkpointer=InMemorySaver(), middleware=[remove_old_tool_results]
    )
    trim = trimmed.invoke({"messages": sensor_conversation()}, {"configurable": {"thread_id": "b-trimmed"}})
    trim_answer = text_of(last_ai(trim["messages"]))
    print("\nWith hook - message types in final state:", [type(m).__name__ for m in trim["messages"]])
    print("With hook - answer:", trim_answer)
    print("With hook - mentions 41:", "41" in trim_answer)
    print("With hook - token usage:", usage(last_ai(trim["messages"])))
    print("Proof check: the hook worked if the answer without the hook mentions 41 and the answer with the hook does not.")


if __name__ == "__main__":
    run_part_a()
    run_part_b()
