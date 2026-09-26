"""Module 07 · Example 3 — interactive OAuth2 (authorization code) for a function tool.

⚠️ Needs a Google OAuth 2.0 **Web application** client:
   Cloud Console → APIs & Services → Credentials → Create OAuth client ID → Web application
   Authorized redirect URI: http://localhost:8765/callback
   Then in .env:
     OAUTH_CLIENT_ID=...apps.googleusercontent.com
     OAUTH_CLIENT_SECRET=...
   Enable the Google Calendar API on the project.

Run:
    python run.py          # opens a browser, you consent, it lists your next events

The tool implements the ADK auth handshake:
  check cached creds -> check for an auth response -> else request_credential() + pending
`run.py` catches the redirect on a tiny local server and feeds the response back.
"""

from __future__ import annotations

import datetime as dt
import json
import os

from fastapi.openapi.models import OAuth2, OAuthFlowAuthorizationCode, OAuthFlows
from google.adk.agents import Agent
from google.adk.auth import AuthConfig, AuthCredential, AuthCredentialTypes, OAuth2Auth
from google.adk.tools import ToolContext

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")
CLIENT_ID = os.environ.get("OAUTH_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("OAUTH_CLIENT_SECRET", "")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
TOKEN_CACHE_KEY = "user:google_calendar_token"

AUTH_SCHEME = OAuth2(
    flows=OAuthFlows(
        authorizationCode=OAuthFlowAuthorizationCode(
            authorizationUrl="https://accounts.google.com/o/oauth2/auth",
            tokenUrl="https://oauth2.googleapis.com/token",
            scopes={s: s for s in SCOPES},
        )
    )
)
AUTH_CREDENTIAL = AuthCredential(
    auth_type=AuthCredentialTypes.OAUTH2,
    oauth2=OAuth2Auth(client_id=CLIENT_ID, client_secret=CLIENT_SECRET),
)


def list_upcoming_events(max_results: int, tool_context: ToolContext) -> dict:
    """List the user's upcoming Google Calendar events.

    Args:
        max_results: How many events to return (1-10).
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    creds: Credentials | None = None

    # 1. cached credentials
    cached = tool_context.state.get(TOKEN_CACHE_KEY)
    if cached:
        creds = Credentials.from_authorized_user_info(json.loads(cached), SCOPES)
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            tool_context.state[TOKEN_CACHE_KEY] = creds.to_json()

    # 2. an auth response came back from the client
    if not creds or not creds.valid:
        exchanged = tool_context.get_auth_response(
            AuthConfig(auth_scheme=AUTH_SCHEME, raw_auth_credential=AUTH_CREDENTIAL)
        )
        if exchanged and exchanged.oauth2 and exchanged.oauth2.access_token:
            creds = Credentials(
                token=exchanged.oauth2.access_token,
                refresh_token=exchanged.oauth2.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                scopes=SCOPES,
            )
            tool_context.state[TOKEN_CACHE_KEY] = creds.to_json()

    # 3. still nothing -> ask the client to run the OAuth flow
    if not creds or not creds.valid:
        tool_context.request_credential(
            AuthConfig(auth_scheme=AUTH_SCHEME, raw_auth_credential=AUTH_CREDENTIAL)
        )
        return {"status": "pending", "message": "Awaiting Google sign-in."}

    # 4. we have creds — call the API
    try:
        service = build("calendar", "v3", credentials=creds)
        now = dt.datetime.now(dt.timezone.utc).isoformat()
        events = (
            service.events()
            .list(calendarId="primary", timeMin=now, maxResults=max(1, min(max_results, 10)),
                  singleEvents=True, orderBy="startTime")
            .execute()
            .get("items", [])
        )
        return {
            "status": "success",
            "events": [
                {"summary": e.get("summary", "(no title)"),
                 "start": e["start"].get("dateTime", e["start"].get("date"))}
                for e in events
            ],
        }
    except Exception as e:  # noqa: BLE001
        return {"status": "error", "error_message": f"Calendar API failed: {e}"}


root_agent = Agent(
    name="calendar_agent",
    model=MODEL,
    description="Reads the user's Google Calendar (OAuth2).",
    instruction=(
        "Use `list_upcoming_events` to answer questions about the user's schedule. "
        "If it returns status 'pending', tell the user to complete the sign-in in "
        "their browser."
    ),
    tools=[list_upcoming_events],
)
