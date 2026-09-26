"""Module 07 · Example 2 — a function tool that needs a secret.

Secret-resolution order (dev → prod):
  1. per-user override in state["user:chat_token"]   (multi-tenant: each user's own token)
  2. Secret Manager                                   (production)
  3. env var CHAT_BOT_TOKEN                            (local dev)
  4. -> return an error dict asking the user to connect

The tool never puts the secret in its return value or logs it.

    adk run ex02_function_tool_secret
    python run.py
"""

from __future__ import annotations

import os

from google.adk.agents import Agent
from google.adk.tools import ToolContext

MODEL = os.environ.get("MODEL", "gemini-2.5-flash")


def _from_secret_manager(name: str) -> str | None:
    """Production path. Returns None here unless google-cloud-secret-manager is set up."""
    try:
        from google.cloud import secretmanager  # type: ignore

        project = os.environ["GOOGLE_CLOUD_PROJECT"]
        client = secretmanager.SecretManagerServiceClient()
        path = f"projects/{project}/secrets/{name}/versions/latest"
        return client.access_secret_version(name=path).payload.data.decode()
    except Exception:  # noqa: BLE001 — not configured / not permitted
        return None


def _resolve_chat_token(tool_context: ToolContext) -> str | None:
    # 1. per-user override
    if tok := tool_context.state.get("user:chat_token"):
        return tok
    # 2. production secret store
    if tok := _from_secret_manager("chat-bot-token"):
        return tok
    # 3. local dev
    return os.environ.get("CHAT_BOT_TOKEN")


def post_to_team_chat(channel: str, message: str, tool_context: ToolContext) -> dict:
    """Post a message to a team chat channel.

    Args:
        channel: Channel name, e.g. "#eng".
        message: The message text.
    """
    token = _resolve_chat_token(tool_context)
    if not token:
        return {
            "status": "error",
            "error_message": (
                "No chat credential configured. Ask an admin to set CHAT_BOT_TOKEN "
                "(dev) / the 'chat-bot-token' secret (prod), or connect your own token."
            ),
        }
    # --- pretend to call the chat API with `token` ---
    masked = token[:3] + "…" + token[-2:]
    return {
        "status": "success",
        "channel": channel,
        "posted": message,
        "auth": f"used token {masked}",   # masked — never return the raw secret
    }


def connect_my_chat_token(token: str, tool_context: ToolContext) -> dict:
    """Save the caller's personal chat token for this session's user (multi-tenant)."""
    tool_context.state["user:chat_token"] = token
    return {"status": "success", "message": "Your chat token is saved."}


root_agent = Agent(
    name="chat_poster",
    model=MODEL,
    description="Posts messages to team chat; handles per-user credentials.",
    instruction=(
        "Use `post_to_team_chat` to post messages. If it returns an auth error, tell the "
        "user what's missing. If the user gives you their personal token, call "
        "`connect_my_chat_token` first, then retry the post. Never repeat a token back."
    ),
    tools=[post_to_team_chat, connect_my_chat_token],
)
