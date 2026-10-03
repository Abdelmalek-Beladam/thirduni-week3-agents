from __future__ import annotations

import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler


_SECRET_PATTERN = re.compile(
    r"(?i)(AIza[0-9A-Za-z_-]{30,}|tvly-[0-9A-Za-z_-]{20,}|sk-[A-Za-z0-9]{20,})"
)


def _name(serialized: dict[str, Any] | None, fallback: str) -> str:
    if not serialized:
        return fallback
    name = serialized.get("name")
    if name:
        return str(name)
    identifier = serialized.get("id")
    if isinstance(identifier, list):
        return str(identifier[-1]) if identifier else fallback
    return str(identifier or fallback)


def _summary(value: Any, limit: int = 1800) -> str:
    if isinstance(value, str):
        text = value
    else:
        try:
            text = json.dumps(value, ensure_ascii=False, default=str)
        except Exception:
            text = repr(value)
    text = _SECRET_PATTERN.sub("[REDACTED]", text)
    if len(text) > limit:
        text = text[:limit] + "…[truncated]"
    return text


class LocalTraceHandler(BaseCallbackHandler):
    """Collect real LangChain callback events locally, without cloud tracing."""

    def __init__(self, trace_id: str, stage: str):
        self.trace_id = trace_id
        self.stage = stage
        self.events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def _record(
        self,
        event: str,
        run_id: UUID,
        parent_run_id: UUID | None,
        name: str,
        metadata: dict[str, Any] | None = None,
        **details: Any,
    ) -> None:
        trace_group = (metadata or {}).get("local_trace_id", self.trace_id)
        record = {
            "sequence": len(self.events) + 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "trace_id": str(trace_group),
            "stage": self.stage,
            "event": event,
            "name": name,
            "run_id": str(run_id),
            "parent_run_id": str(parent_run_id) if parent_run_id else None,
        }
        for key, value in details.items():
            record[key] = _summary(value) if value is not None else None
        with self._lock:
            record["sequence"] = len(self.events) + 1
            self.events.append(record)

    def on_chain_start(
        self,
        serialized: dict[str, Any],
        inputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._record(
            "chain_start", run_id, parent_run_id, _name(serialized, "chain"),
            metadata, input_summary=inputs, tags=tags,
        )

    def on_chain_end(
        self,
        outputs: dict[str, Any],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("chain_end", run_id, parent_run_id, "chain", output_summary=outputs)

    def on_chain_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("chain_error", run_id, parent_run_id, "chain", error=str(error))

    def on_tool_start(
        self,
        serialized: dict[str, Any],
        input_str: str,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        inputs: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._record(
            "tool_start", run_id, parent_run_id, _name(serialized, "tool"),
            metadata, input_summary=inputs if inputs is not None else input_str, tags=tags,
        )

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("tool_end", run_id, parent_run_id, "tool", output_summary=output)

    def on_tool_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("tool_error", run_id, parent_run_id, "tool", error=str(error))

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._record(
            "chat_model_start", run_id, parent_run_id,
            _name(serialized, "chat_model"), metadata,
            message_count=sum(len(batch) for batch in messages), tags=tags,
        )

    def on_llm_start(
        self,
        serialized: dict[str, Any],
        prompts: list[str],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        self._record(
            "llm_start", run_id, parent_run_id, _name(serialized, "llm"),
            metadata, prompt_count=len(prompts), tags=tags,
        )

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("llm_end", run_id, parent_run_id, "llm", output_summary=response)

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        **kwargs: Any,
    ) -> None:
        self._record("llm_error", run_id, parent_run_id, "llm", error=str(error))


def format_timeline(events: list[dict[str, Any]]) -> str:
    parent_by_run: dict[str, str | None] = {}
    for event in events:
        parent_by_run.setdefault(event["run_id"], event["parent_run_id"])

    def depth_for(parent_id: str | None) -> int:
        depth = 0
        seen: set[str] = set()
        while parent_id and parent_id in parent_by_run and parent_id not in seen:
            seen.add(parent_id)
            depth += 1
            parent_id = parent_by_run[parent_id]
        return depth

    lines = []
    for event in events:
        depth = depth_for(event["parent_run_id"])
        parent = event["parent_run_id"] or "root"
        lines.append(
            f"{event['sequence']:03d} {'  ' * depth}{event['event']} "
            f"{event['name']} run={event['run_id']} parent={parent}"
        )
    return "\n".join(lines) + "\n"


def save_trace(handler: LocalTraceHandler, output_dir: Path, stage: str) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / f"{stage}_trace.json"
    timeline_path = output_dir / f"{stage}_trace_timeline.txt"
    payload = {
        "trace_id": handler.trace_id,
        "stage": stage,
        "trace_kind": "local_langchain_callback_trace",
        "cloud_tracing_enabled": False,
        "events": handler.events,
    }
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    timeline_path.write_text(format_timeline(handler.events), encoding="utf-8")
    return json_path, timeline_path
