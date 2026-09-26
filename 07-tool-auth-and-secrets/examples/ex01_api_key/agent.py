"""Module 07 · Example 1 — API-key auth on an OpenAPI toolset.

NASA's APOD API needs `?api_key=...` (403 without). `token_to_scheme_credential`
builds the AuthScheme + AuthCredential; OpenAPIToolset applies the key to every
generated request. The model never sees the key.

    adk run ex01_api_key
    python run.py

.env: NASA_API_KEY=DEMO_KEY   (DEMO_KEY works with no signup, low rate limit)
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.tools.openapi_tool.auth.auth_helpers import token_to_scheme_credential
from google.adk.tools.openapi_tool import OpenAPIToolset

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
NASA_API_KEY = os.environ.get("NASA_API_KEY", "DEMO_KEY")

SPEC = """
openapi: 3.0.3
info: { title: NASA APOD, version: "1.0" }
servers: [{ url: https://api.nasa.gov }]
paths:
  /planetary/apod:
    get:
      operationId: get_astronomy_picture_of_the_day
      summary: Astronomy Picture of the Day — metadata for a given date
      parameters:
        - name: date
          in: query
          required: false
          schema: { type: string }
          description: YYYY-MM-DD. Defaults to today.
      responses: { "200": { description: OK } }
"""

# ("apikey" type, in "query", param name "api_key", the value)
auth_scheme, auth_credential = token_to_scheme_credential(
    "apikey", "query", "api_key", NASA_API_KEY
)

nasa_tools = OpenAPIToolset(
    spec_str=SPEC,
    spec_str_type="yaml",
    auth_scheme=auth_scheme,
    auth_credential=auth_credential,
)

root_agent = Agent(
    name="apod_agent",
    model=MODEL,
    description="Tells you about NASA's Astronomy Picture of the Day.",
    instruction=(
        "Use `get_astronomy_picture_of_the_day` to fetch the picture metadata "
        "(optionally for a specific date), then give the title and a one-sentence "
        "summary of the explanation. Include the image URL."
    ),
    tools=[nasa_tools],
)
