"""Module 06 · Example 2 — OpenAPIToolset from a hand-written spec for a public API.

Frankfurter (https://frankfurter.dev) is a free, no-auth currency API. It has no
published OpenAPI doc, so we write a minimal one. Two operations -> two tools.

    adk run ex02_openapi_public
    python run.py
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.tools.openapi_tool import OpenAPIToolset

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")

SPEC = """
openapi: 3.0.3
info:
  title: Frankfurter FX API
  version: "1.0"
servers:
  - url: https://api.frankfurter.dev/v1
paths:
  /latest:
    get:
      operationId: get_latest_rates
      summary: Latest exchange rates for a base currency
      parameters:
        - name: base
          in: query
          required: false
          schema: { type: string }
          description: Base currency ISO code, e.g. USD. Defaults to EUR.
        - name: symbols
          in: query
          required: false
          schema: { type: string }
          description: Comma-separated target currency codes, e.g. "USD,GBP".
      responses:
        "200": { description: OK }
  /{date}:
    get:
      operationId: get_historical_rates
      summary: Exchange rates on a specific past date (YYYY-MM-DD)
      parameters:
        - name: date
          in: path
          required: true
          schema: { type: string }
          description: Date in YYYY-MM-DD format.
        - name: base
          in: query
          required: false
          schema: { type: string }
        - name: symbols
          in: query
          required: false
          schema: { type: string }
      responses:
        "200": { description: OK }
"""

fx_tools = OpenAPIToolset(spec_str=SPEC, spec_str_type="yaml")

root_agent = Agent(
    name="fx_agent",
    model=MODEL,
    description="Answers currency exchange-rate questions using the Frankfurter API.",
    instruction=(
        "Use `get_latest_rates` for current rates and `get_historical_rates` for a past "
        "date. Always pass explicit `base` and `symbols` currency codes. "
        "Do the final arithmetic yourself and show the rate you used."
    ),
    tools=[fx_tools],
)
