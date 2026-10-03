"""Shared helpers for the Module 3 middleware exercises."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

HERE = Path(__file__).resolve().parent
PROJECT_ROOT = HERE.parents[1]
load_dotenv(PROJECT_ROOT / ".env")

STANDARD_MODEL = os.getenv("MODULE3_STANDARD_MODEL", "gemini-3.1-flash-lite")
LARGE_MODEL = os.getenv("MODULE3_LARGE_MODEL", "gemini-2.5-flash")
CHINOOK = PROJECT_ROOT / "notebooks" / "module-3" / "resources" / "Chinook.db"


def make_model(name: str = STANDARD_MODEL) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model=name, temperature=0)


class Tee:
    """Write everything printed to the terminal and to a UTF-8 text file."""

    def __init__(self, filename: str):
        self.file = open(HERE / filename, "w", encoding="utf-8")
        self.stdout = sys.stdout

    def write(self, text):
        self.stdout.write(text)
        self.file.write(text)

    def flush(self):
        self.stdout.flush()
        self.file.flush()


def start_log(filename: str) -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.stdout = Tee(filename)


def text_of(message) -> str:
    try:
        return message.text
    except Exception:
        return str(message.content)


def last_ai(messages):
    for m in reversed(messages):
        if m.type == "ai":
            return m
    return None


def usage(message) -> dict:
    meta = getattr(message, "usage_metadata", None) or {}
    return {
        "input_tokens": meta.get("input_tokens"),
        "output_tokens": meta.get("output_tokens"),
        "total_tokens": meta.get("total_tokens"),
    }


def total_usage(messages) -> dict:
    totals = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for m in messages:
        if m.type == "ai":
            for key, value in usage(m).items():
                totals[key] += value or 0
    return totals


def header(title: str) -> None:
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)
