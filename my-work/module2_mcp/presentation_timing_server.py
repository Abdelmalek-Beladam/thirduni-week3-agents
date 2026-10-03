from __future__ import annotations

import math
from typing import Any

from mcp.server.fastmcp import FastMCP


mcp = FastMCP("presentation-timing")


@mcp.tool()
def allocate_presentation_time(
    total_minutes: float,
    problem_percent: float,
    method_percent: float,
    results_percent: float,
    conclusion_percent: float,
) -> dict[str, Any]:
    """Allocate a presentation's total time across four named sections.

    The percentage inputs must be non-negative and sum to exactly 100. The
    response gives each section's percentage, whole minutes, remaining seconds,
    and total seconds. This tool is deterministic and makes no model or network
    calls.
    """
    inputs = {
        "problem": problem_percent,
        "method": method_percent,
        "results": results_percent,
        "conclusion": conclusion_percent,
    }
    if not math.isfinite(total_minutes) or total_minutes <= 0:
        return {
            "error": "validation_error",
            "message": "total_minutes must be a positive finite number.",
        }
    if any(not math.isfinite(value) or value < 0 for value in inputs.values()):
        return {
            "error": "validation_error",
            "message": "Each section percentage must be a non-negative finite number.",
        }
    percentage_total = sum(inputs.values())
    if not math.isclose(percentage_total, 100.0, rel_tol=0.0, abs_tol=1e-9):
        return {
            "error": "validation_error",
            "message": f"Section percentages must total 100; received {percentage_total:g}.",
            "received_percent_total": percentage_total,
        }

    total_seconds = round(total_minutes * 60)
    exact_seconds = {
        section: total_seconds * percentage / 100
        for section, percentage in inputs.items()
    }
    allocated_seconds = {
        section: math.floor(seconds)
        for section, seconds in exact_seconds.items()
    }
    remainder = total_seconds - sum(allocated_seconds.values())
    remainder_order = sorted(
        exact_seconds,
        key=lambda section: exact_seconds[section] - allocated_seconds[section],
        reverse=True,
    )
    for section in remainder_order[:remainder]:
        allocated_seconds[section] += 1

    sections = {
        section: {
            "percentage": percentage,
            "minutes": allocated_seconds[section] // 60,
            "seconds": allocated_seconds[section] % 60,
            "total_seconds": allocated_seconds[section],
        }
        for section, percentage in inputs.items()
    }
    return {
        "total_minutes": total_minutes,
        "total_seconds": total_seconds,
        "percentage_total": percentage_total,
        "sections": sections,
    }


if __name__ == "__main__":
    mcp.run(transport="stdio")
