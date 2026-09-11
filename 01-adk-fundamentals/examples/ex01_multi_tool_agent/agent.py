"""Module 01 · Example 1 — the canonical multi-tool agent.

Two tools, so the event loop has something to show: the model must pick the right
tool (or both), call it, read the result, and compose an answer.

Run (from …/01-adk-fundamentals/examples):
    adk run ex01_multi_tool_agent
    adk web
"""

from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

# A tiny fake dataset so the example is deterministic and offline-friendly.
_WEATHER = {
    "paris": ("18°C", "light rain"),
    "tokyo": ("24°C", "clear"),
    "new york": ("21°C", "partly cloudy"),
    "cairo": ("33°C", "sunny"),
}

_TZ = {
    "paris": "Europe/Paris",
    "tokyo": "Asia/Tokyo",
    "new york": "America/New_York",
    "cairo": "Africa/Cairo",
}


def get_weather(city: str) -> dict:
    """Get the current weather for a city.

    Args:
        city: City name, e.g. "Paris" or "New York".

    Returns:
        dict: {"status": "success", "city", "temperature", "conditions"}
              or {"status": "error", "error_message"} if the city is unknown.
    """
    key = city.strip().lower()
    if key not in _WEATHER:
        return {
            "status": "error",
            "error_message": f"No weather data for '{city}'. Known: {', '.join(_WEATHER)}.",
        }
    temp, conditions = _WEATHER[key]
    return {"status": "success", "city": city, "temperature": temp, "conditions": conditions}


def get_current_time(city: str) -> dict:
    """Get the current local time in a city.

    Args:
        city: City name, e.g. "Tokyo".

    Returns:
        dict: {"status": "success", "city", "local_time"} or an error dict.
    """
    key = city.strip().lower()
    if key not in _TZ:
        return {
            "status": "error",
            "error_message": f"No timezone for '{city}'. Known: {', '.join(_TZ)}.",
        }
    now = datetime.now(ZoneInfo(_TZ[key]))
    return {
        "status": "success",
        "city": city,
        "local_time": now.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


root_agent = Agent(
    name="multi_tool_agent",
    model=MODEL,
    description="Reports current weather and local time for a handful of major cities.",
    instruction=(
        "You are a concise travel-desk assistant.\n"
        "- For weather questions, call `get_weather`.\n"
        "- For time questions, call `get_current_time`.\n"
        "- If the user asks about both, call both tools before answering.\n"
        "- If a tool returns status 'error', tell the user plainly what went wrong "
        "and which cities are supported. Do not invent data.\n"
        "- Keep the final answer to one or two sentences."
    ),
    tools=[get_weather, get_current_time],
)
