"""Client side of the interactive OAuth2 flow.

    python run.py

Needs OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET in .env (see agent.py header).
This does what `adk web` does automatically: detect the `adk_request_credential`
call, open the browser, catch the redirect, send the response back to the agent.
"""

from __future__ import annotations

import asyncio
import pathlib
import threading
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.auth import AuthConfig  
from google.adk.runners import InMemoryRunner  
from google.genai import types  

from agent import root_agent  

APP = "calendar"
REDIRECT_URI = "http://localhost:8765/callback"
_callback_url: dict[str, str] = {}


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        _callback_url["url"] = f"http://localhost:8765{self.path}"
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Auth complete. You can close this tab.")

    def log_message(self, *_):  # silence
        pass


def _catch_redirect() -> str:
    server = HTTPServer(("localhost", 8765), _Handler)
    while "url" not in _callback_url:
        server.handle_request()
    return _callback_url["url"]


def _auth_request_call(event):
    for p in (event.content.parts if event.content and event.content.parts else []):
        fc = getattr(p, "function_call", None)
        if fc and fc.name == "adk_request_credential" and event.long_running_tool_ids \
                and fc.id in event.long_running_tool_ids:
            return fc
    return None


async def main() -> None:
    if not root_agent.tools:
        return
    import os
    if not os.environ.get("OAUTH_CLIENT_ID"):
        print("Set OAUTH_CLIENT_ID / OAUTH_CLIENT_SECRET in .env first (see agent.py).")
        return

    runner = InMemoryRunner(agent=root_agent, app_name=APP)
    s = await runner.session_service.create_session(app_name=APP, user_id="u1")
    msg = types.Content(role="user", parts=[types.Part(text="What are my next 3 events?")])

    call_id, auth_config = None, None
    async for ev in runner.run_async(user_id="u1", session_id=s.id, new_message=msg):
        if (fc := _auth_request_call(ev)):
            call_id = fc.id
            auth_config = AuthConfig.model_validate(fc.args["auth_config"])
            break
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    if not call_id:
        return

    # open the consent screen
    auth_uri = auth_config.exchanged_auth_credential.oauth2.auth_uri + \
        f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    print("Opening browser for Google sign-in...")
    threading.Thread(target=lambda: webbrowser.open(auth_uri), daemon=True).start()
    response_url = _catch_redirect()

    # feed the callback back to the agent
    auth_config.exchanged_auth_credential.oauth2.auth_response_uri = response_url
    auth_config.exchanged_auth_credential.oauth2.redirect_uri = REDIRECT_URI
    resume = types.Content(role="user", parts=[types.Part(
        function_response=types.FunctionResponse(
            id=call_id, name="adk_request_credential", response=auth_config.model_dump()
        )
    )])
    async for ev in runner.run_async(user_id="u1", session_id=s.id, new_message=resume):
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
