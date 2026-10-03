"""Module 3 - Email Assistant project (adapted from notebooks/module-3/3.5_email_agent.py).

Context holds the credentials, a custom state field tracks authentication,
dynamic tools hide the inbox and send tools until authenticated, a dynamic
prompt switches role, and sending requires human approval.

All email functions are dummies. Nothing touches a real mailbox.
build_agent(hardened=True) adds checks inside the tools themselves and
locks authentication after 2 failed attempts per thread.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from langchain.agents import AgentState, create_agent
from langchain.agents.middleware import (
    HumanInTheLoopMiddleware,
    ModelRequest,
    ModelResponse,
    dynamic_prompt,
    before_agent,
    wrap_model_call,
)
from langchain.messages import ToolMessage
from langchain.tools import ToolRuntime, tool
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

import importlib.util
from pathlib import Path
_spec = importlib.util.spec_from_file_location("inbox_doorman_common", Path(__file__).with_name("common.py"))
_common = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_common)
make_model = _common.make_model

INBOX = (
    "Hi Julie, I'm going to be in town next week and was wondering if we could grab a coffee? "
    "- best, Jane (jane@example.com)"
)
INBOX_READS = {"count": 0}
AUTH_ATTEMPTS = {"count": 0}
SENT: list[dict] = []
MAX_FAILED_ATTEMPTS = 2
FAILED_BY_THREAD: dict[str, int] = {}


@dataclass
class EmailContext:
    email_address: str = "julie@example.com"
    password: str = "password123"


class AuthenticatedState(AgentState):
    authenticated: bool
    failed_attempts: int


def _read_inbox() -> str:
    INBOX_READS["count"] += 1
    return INBOX


def _send(to: str, subject: str, body: str) -> str:
    SENT.append({"to": to, "subject": subject, "body": body})
    return f"Email sent to {to} with subject {subject} (dummy, nothing left this computer)"


def _auth_result(ok: bool, message: str, runtime: ToolRuntime) -> Command:
    return Command(update={
        "authenticated": ok,
        "messages": [ToolMessage(message, tool_call_id=runtime.tool_call_id)],
    })


# Course design: the tools themselves do not check authentication.
@tool
def check_inbox() -> str:
    """Check the inbox for recent emails"""
    return _read_inbox()


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send a response email"""
    return _send(to, subject, body)


@tool
def authenticate(email: str, password: str, runtime: ToolRuntime) -> Command:
    """Authenticate the user with the given email and password"""
    AUTH_ATTEMPTS["count"] += 1
    ok = email == (runtime.context or EmailContext()).email_address and password == (runtime.context or EmailContext()).password
    return _auth_result(ok, "Successfully authenticated" if ok else "Authentication failed", runtime)


# Hardened design: the same tools refuse unless the state says authenticated.
@tool("check_inbox")
def guarded_check_inbox(runtime: ToolRuntime) -> str:
    """Check the inbox for recent emails"""
    if not runtime.state.get("authenticated"):
        return "Refused: the user is not authenticated."
    return _read_inbox()


@tool("send_email")
def guarded_send_email(to: str, subject: str, body: str, runtime: ToolRuntime) -> str:
    """Send a response email"""
    if not runtime.state.get("authenticated"):
        return "Refused: the user is not authenticated."
    return _send(to, subject, body)


@tool("authenticate")
def guarded_authenticate(email: str, password: str, runtime: ToolRuntime) -> Command:
    """Authenticate the user with the given email and password"""
    AUTH_ATTEMPTS["count"] += 1
    failures = int(runtime.state.get("failed_attempts", 0))
    if failures >= MAX_FAILED_ATTEMPTS:
        return _auth_result(False, "Locked: too many failed attempts in this conversation", runtime)
    ok = email == (runtime.context or EmailContext()).email_address and password == (runtime.context or EmailContext()).password
    result = _auth_result(ok, "Successfully authenticated" if ok else "Authentication failed", runtime)
    result.update["failed_attempts"] = failures if ok else failures + 1
    return result


AUTHENTICATED_PROMPT = "You are a helpful assistant that can check the inbox and send emails."
UNAUTHENTICATED_PROMPT = "You are a helpful assistant that can authenticate users."


def build_agent(hardened: bool = True, model=None):
    inbox_tool = guarded_check_inbox if hardened else check_inbox
    send_tool = guarded_send_email if hardened else send_email
    auth_tool = guarded_authenticate if hardened else authenticate

    @before_agent
    def initialize_state(state, runtime):
        if "authenticated" not in state:
            return {"authenticated": False, "failed_attempts": 0}
        return None

    @wrap_model_call
    async def dynamic_tool_call(request: ModelRequest, handler) -> ModelResponse:
        """Offer inbox and send tools only after successful authentication."""
        tools = [inbox_tool, send_tool] if request.state.get("authenticated") else [auth_tool]
        return await handler(request.override(tools=tools))

    @dynamic_prompt
    def dynamic_prompt_func(request: ModelRequest) -> str:
        return AUTHENTICATED_PROMPT if request.state.get("authenticated") else UNAUTHENTICATED_PROMPT

    return create_agent(
        model or make_model(),
        tools=[auth_tool, inbox_tool, send_tool],
        state_schema=AuthenticatedState,
        context_schema=EmailContext,
        middleware=[
            initialize_state,
            dynamic_tool_call,
            dynamic_prompt_func,
            HumanInTheLoopMiddleware(interrupt_on={
                "authenticate": False,
                "check_inbox": False,
                "send_email": True,
            }),
        ],
    )


agent = build_agent(hardened=True)
