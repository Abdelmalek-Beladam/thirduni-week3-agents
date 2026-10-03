"""Module 3 - Human-in-the-Loop.

The wedding project discovered a Kiwi tool that sends feedback externally.
Here a dummy version of that action is gated with HumanInTheLoopMiddleware.
Reading flight options stays automatic. Nothing is sent anywhere real.

Thread 1: approve.
Thread 2: reject with a reason, then edit the new draft.
"""
from __future__ import annotations

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langchain.messages import HumanMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from common import header, last_ai, make_model, start_log, text_of, total_usage

start_log("hitl_output.txt")

SENT_LOG: list[str] = []  # stands in for a real external send


class FlightState(AgentState):
    flight_options: str


@tool
def read_flight_options(runtime: ToolRuntime) -> str:
    """Read the saved flight options for the wedding trip."""
    return runtime.state["flight_options"]


@tool
def send_feedback_to_flight_provider(message: str) -> str:
    """Send a feedback message to the flight provider."""
    SENT_LOG.append(message)
    return "Feedback sent (dummy, nothing left this computer)."


def build_agent():
    return create_agent(
        model=make_model(),
        tools=[read_flight_options, send_feedback_to_flight_provider],
        state_schema=FlightState,
        checkpointer=InMemorySaver(),
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={
                    "read_flight_options": False,
                    "send_feedback_to_flight_provider": True,
                },
                description_prefix="Sending feedback requires approval",
            )
        ],
    )


START = {
    "messages": [HumanMessage(
        "Read my saved flight options, then send the flight provider short feedback that the return "
        "flight times are inconvenient for a wedding. Send it now."
    )],
    "flight_options": "Algiers to Paris, 13-17 May 2027, 2 adults. Cheapest return departs 05:40.",
}


def show_interrupt(response) -> bool:
    interrupts = response.get("__interrupt__")
    if not interrupts:
        print("No interrupt. Final answer:", text_of(last_ai(response["messages"])))
        return False
    request = interrupts[0].value["action_requests"][0]
    print("INTERRUPT - tool:", request["name"])
    print("Drafted message:", request["args"].get("message"))
    return True


def approve_thread(agent) -> None:
    header("THREAD 1 - approve")
    config = {"configurable": {"thread_id": "hitl-approve"}}
    response = agent.invoke(dict(START), config=config)
    print("Sent so far:", len(SENT_LOG))
    if show_interrupt(response):
        response = agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config=config)
        print("After approve - sent so far:", len(SENT_LOG))
        print("Final answer:", text_of(last_ai(response["messages"])))
    print("Thread token usage:", total_usage(response["messages"]))


def reject_then_edit_thread(agent) -> None:
    header("THREAD 2 - reject with a reason, then edit")
    config = {"configurable": {"thread_id": "hitl-reject-edit"}}
    before = len(SENT_LOG)
    response = agent.invoke(dict(START), config=config)
    if not show_interrupt(response):
        return

    response = agent.invoke(
        Command(resume={"decisions": [{
            "type": "reject",
            "message": "Too blunt. Make it polite and mention the 05:40 departure explicitly.",
        }]}),
        config=config,
    )
    print("After reject - sent in this thread:", len(SENT_LOG) - before)
    if not show_interrupt(response):
        return

    edited = ("Hello, thank you for the options. The 05:40 return is difficult for wedding guests. "
              "Could later return times be shown? Best regards, Abdelmalek.")
    response = agent.invoke(
        Command(resume={"decisions": [{
            "type": "edit",
            "edited_action": {"name": "send_feedback_to_flight_provider", "args": {"message": edited}},
        }]}),
        config=config,
    )
    print("After edit - sent in this thread:", len(SENT_LOG) - before)
    print("Message actually sent:", SENT_LOG[-1] if SENT_LOG else None)
    print("Sent text equals my edit:", bool(SENT_LOG) and SENT_LOG[-1] == edited)
    print("Final answer:", text_of(last_ai(response["messages"])))
    print("Thread token usage:", total_usage(response["messages"]))


if __name__ == "__main__":
    agent = build_agent()
    approve_thread(agent)
    reject_then_edit_thread(agent)
    print("\nTotal dummy sends:", len(SENT_LOG))
