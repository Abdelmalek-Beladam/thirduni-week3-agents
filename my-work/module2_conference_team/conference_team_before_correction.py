from __future__ import annotations

import json
import re
import sqlite3
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from dotenv import load_dotenv
from langchain.agents import AgentState, create_agent
from langchain.messages import HumanMessage, ToolMessage
from langchain.tools import ToolRuntime, tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command
from tavily import TavilyClient

from local_trace import LocalTraceHandler


PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")
MODEL_NAME = "gemini-3.1-flash-lite"


class ConferenceState(AgentState):
    user_name: str
    topic: str
    presentation_minutes: int
    audience: str
    experimental_results_supplied: bool
    brief_status: str
    evidence_status: str
    evidence_result: str
    evidence_searches_used: int
    structure_status: str
    structure_result: str
    structure_runs_used: int
    questions_status: str
    questions_result: str
    question_runs_used: int


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "svg"}:
            self.ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "svg"} and self.ignored_depth:
            self.ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self.ignored_depth:
            self.parts.append(data)

    def text(self) -> str:
        return re.sub(r"\s+", " ", " ".join(self.parts)).strip()


def _fetch_source(url: str) -> dict[str, Any]:
    if urlsplit(url).scheme != "https":
        return {"access_status": "blocked_by_policy", "access_limitation": "Only HTTPS URLs are fetched.", "excerpt": None}
    try:
        request = Request(url, headers={"User-Agent": "Mozilla/5.0 (conference-evidence-check/1.0)"})
        with urlopen(request, timeout=8) as response:
            if response.status != 200:
                return {"access_status": f"http_{response.status}", "access_limitation": f"HTTP {response.status}", "excerpt": None}
            raw = response.read(800_000).decode("utf-8", errors="replace")
        parser = VisibleText()
        parser.feed(raw)
        text = parser.text()
        candidates = [
            sentence.strip()
            for sentence in re.split(r"(?<=[.!?])\s+", text)
            if any(term in sentence.lower() for term in ("unseen data", "external validation", "generaliz", "overfit"))
        ]
        return {
            "access_status": "page_retrieved" if candidates else "page_retrieved_no_target_excerpt",
            "access_limitation": "Direct retrieval is preliminary and does not establish source credibility.",
            "excerpt": " ".join(candidates[:2])[:1200] if candidates else None,
        }
    except HTTPError as error:
        return {"access_status": f"http_{error.code}", "access_limitation": f"HTTP {error.code}", "excerpt": None}
    except (URLError, TimeoutError, OSError) as error:
        return {"access_status": "fetch_error", "access_limitation": f"{type(error).__name__}: {error}", "excerpt": None}


def _message_tool_result(content: str, runtime: ToolRuntime) -> ToolMessage:
    return ToolMessage(content=content, tool_call_id=runtime.tool_call_id)


def build_conference_team(trace_id: str, trace: LocalTraceHandler):
    model = ChatGoogleGenerativeAI(model=MODEL_NAME)
    tavily_client = TavilyClient()
    search_counter = {"count": 0}

    @tool
    def search_unseen_data_evidence(query: str) -> dict[str, Any]:
        """Search Tavily for evidence about evaluation on unseen or independent data.

        Maximum two searches are enforced in code. Returned snippets are
        preliminary; direct access status and excerpts are reported separately.
        """
        if search_counter["count"] >= 2:
            return {"error": "Tavily search limit reached after two searches.", "results": []}
        search_counter["count"] += 1
        try:
            result = tavily_client.search(query, search_depth="advanced", max_results=5, include_raw_content="markdown")
        except Exception as error:
            return {"error": f"Tavily {type(error).__name__}: {error}", "results": []}
        records = []
        for item in result.get("results", [])[:5]:
            url = item.get("url", "")
            access = _fetch_source(url) if url else {
                "access_status": "missing_url",
                "access_limitation": "No URL returned.",
                "excerpt": None,
            }
            records.append({
                "title": item.get("title"),
                "url": url,
                "snippet": item.get("content"),
                "retrieved_excerpt": access["excerpt"],
                "access_status": access["access_status"],
                "access_limitation": access["access_limitation"],
                "support_status": "partially_supported" if access["excerpt"] else "unverified",
                "date_limitation": item.get("published_date") or "No publication date returned.",
            })
        return {"searches_used": search_counter["count"], "results": records}

    evidence_specialist = create_agent(
        model=model,
        tools=[search_unseen_data_evidence],
        system_prompt=(
            "You are an evidence-review specialist. Use the search tool at most twice. "
            "Return exact URLs from tool results, distinguish snippets from retrieved excerpts, "
            "preserve support_status/access_status/date_limitation, and never call a source verified "
            "merely because a URL exists. Do not invent results, accuracy figures, citations, or claims "
            "about the user's model."
        ),
    )

    structure_specialist = create_agent(
        model=model,
        system_prompt=(
            "You are a presentation-structure specialist. Build an eight-minute outline from the explicit "
            "topic, audience, and evidence report supplied in the user message. Make section times total "
            "exactly eight minutes. Do not invent experimental results or claim external validation."
        ),
    )

    questions_specialist = create_agent(
        model=model,
        system_prompt=(
            "You are a rehearsal-question specialist. Create five likely audience questions from the explicit "
            "topic and audience. Do not assume experimental results, accuracy, validation, or conclusions "
            "that the user did not supply. When asked, make questions accessible to non-technical attendees."
        ),
    )

    @tool
    def review_evidence(runtime: ToolRuntime) -> Command:
        """Run evidence review using the explicit saved topic and eight-minute brief."""
        state = runtime.state
        if state.get("evidence_status") == "completed":
            report = state.get("evidence_result", "Evidence review already completed.")
            return Command(update={"evidence_result": report, "messages": [_message_tool_result(report, runtime)]})
        prompt = (
            f"Topic: {state['topic']}\nAudience: {state['audience']}\n"
            f"Presentation minutes: {state['presentation_minutes']}\n"
            "Research why evaluation on unseen data matters. Return a structured evidence review "
            "with exact URLs, supporting excerpts, support status, and access/date limitations."
        )
        result = evidence_specialist.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"callbacks": [trace], "metadata": {"local_trace_id": trace_id, "component": "evidence_specialist"}},
        )
        report = json.dumps({"searches_used": search_counter["count"], "specialist_report": result["messages"][-1].content}, ensure_ascii=False)
        return Command(update={
            "evidence_status": "completed",
            "evidence_result": report,
            "evidence_searches_used": search_counter["count"],
            "messages": [_message_tool_result(report, runtime)],
        })

    @tool
    def build_presentation_structure(runtime: ToolRuntime) -> Command:
        """Build the outline from explicit coordinator fields and saved evidence."""
        state = runtime.state
        if state.get("structure_status") == "completed":
            report = state.get("structure_result", "Presentation outline already completed.")
            return Command(update={"structure_result": report, "messages": [_message_tool_result(report, runtime)]})
        prompt = (
            f"Topic: {state['topic']}\nAudience: {state['audience']}\n"
            f"Presentation minutes: {state['presentation_minutes']}\n"
            f"Evidence report: {state.get('evidence_result', '')}\n"
            "Create a practical outline whose times total exactly eight minutes. "
            "Do not invent results or claim validation."
        )
        result = structure_specialist.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"callbacks": [trace], "metadata": {"local_trace_id": trace_id, "component": "structure_specialist"}},
        )
        report = str(result["messages"][-1].content)
        return Command(update={
            "structure_status": "completed",
            "structure_result": report,
            "structure_runs_used": state.get("structure_runs_used", 0) + 1,
            "messages": [_message_tool_result(report, runtime)],
        })

    @tool
    def prepare_rehearsal_questions(runtime: ToolRuntime) -> Command:
        """Prepare questions using explicit topic, audience, and optional style request."""
        state = runtime.state
        prompt = (
            f"Topic: {state['topic']}\nAudience: {state['audience']}\n"
            f"Presentation minutes: {state['presentation_minutes']}\n"
            f"Current outline: {state.get('structure_result', '')}\n"
            f"Current evidence: {state.get('evidence_result', '')}\n"
            "Prepare exactly five likely audience questions. Do not assume results."
        )
        result = questions_specialist.invoke(
            {"messages": [HumanMessage(content=prompt)]},
            config={"callbacks": [trace], "metadata": {"local_trace_id": trace_id, "component": "questions_specialist"}},
        )
        report = str(result["messages"][-1].content)
        return Command(update={
            "questions_status": "completed",
            "questions_result": report,
            "question_runs_used": state.get("question_runs_used", 0) + 1,
            "messages": [_message_tool_result(report, runtime)],
        })

    coordinator = create_agent(
        model=model,
        tools=[review_evidence, build_presentation_structure, prepare_rehearsal_questions],
        state_schema=ConferenceState,
        checkpointer=InMemorySaver(),
        system_prompt=(
            "You are the conference-preparation coordinator. The brief is saved before delegation. "
            "On the first request, delegate sequentially to review_evidence, build_presentation_structure, "
            "and prepare_rehearsal_questions. On a follow-up that changes only question accessibility, "
            "reuse saved evidence and outline and delegate only to prepare_rehearsal_questions. Preserve "
            "source URLs, support/access/date limitations, exact eight-minute timing, and the fact that "
            "no experimental results were supplied. Never invent performance figures or claim validation."
        ),
    )
    return coordinator


def initial_state() -> dict[str, Any]:
    return {
        "messages": [], "user_name": "", "topic": "", "presentation_minutes": 0,
        "audience": "", "experimental_results_supplied": False, "brief_status": "not_started",
        "evidence_status": "not_started", "evidence_result": "", "evidence_searches_used": 0,
        "structure_status": "not_started", "structure_result": "", "structure_runs_used": 0,
        "questions_status": "not_started", "questions_result": "", "question_runs_used": 0,
    }
