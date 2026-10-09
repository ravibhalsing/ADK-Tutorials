"""Artifacts: save / load / list / version, and session vs user: scope.

    python run.py

Tools write and read artifacts via tool_context; one turn drives a save+list,
then we inspect versions directly.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.artifacts import InMemoryArtifactService  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.adk.tools import ToolContext  
from google.genai import types  

APP, USER, MODEL = "artifacts_demo", "u1", "gemini-2.5-flash"


async def save_note(name: str, text: str, tool_context: ToolContext) -> dict:
    """Save a text note as an artifact. Use name 'user:<x>' to keep it across sessions."""
    part = types.Part.from_bytes(data=text.encode(), mime_type="text/plain")
    version = await tool_context.save_artifact(filename=name, artifact=part)
    return {"status": "success", "filename": name, "version": version}


async def list_notes(tool_context: ToolContext) -> dict:
    """List the artifact filenames available in this session (and user-scoped ones)."""
    return {"status": "success", "files": await tool_context.list_artifacts()}


agent = Agent(
    name="notekeeper", model=MODEL,
    instruction=(
        "Use save_note to store notes and list_notes to list them. "
        "If the user says the note is 'permanent' / 'for all my chats', prefix the name "
        "with 'user:'. Report the version number save_note returns."
    ),
    tools=[save_note, list_notes],
)


async def main() -> None:
    artifact_service = InMemoryArtifactService()
    session_service = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=session_service,
                    artifact_service=artifact_service)
    s = await session_service.create_session(app_name=APP, user_id=USER)

    for q in [
        "Save a note called meeting.txt that says 'sync at 3pm Tuesday'.",
        "Update meeting.txt to say 'sync moved to 4pm Tuesday'.",
        "Save a permanent note called prefs that says 'dark mode, metric units'.",
        "What notes do I have?",
    ]:
        print(f"\nuser> {q}")
        async for ev in runner.run_async(
            user_id=USER, session_id=s.id,
            new_message=types.Content(role="user", parts=[types.Part(text=q)]),
        ):
            for c in ev.get_function_calls():
                a = {k: (v[:30] if isinstance(v, str) else v) for k, v in c.args.items()}
                print(f"  [call] {c.name}({a})")
            if ev.is_final_response() and ev.content:
                print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    # --- inspect versions directly ---
    print("\n--- artifact store ---")
    keys = await artifact_service.list_artifact_keys(app_name=APP, user_id=USER, session_id=s.id)
    for k in keys:
        versions = await artifact_service.list_versions(
            app_name=APP, user_id=USER, session_id=s.id, filename=k)
        latest = await artifact_service.load_artifact(
            app_name=APP, user_id=USER, session_id=s.id, filename=k)
        body = latest.inline_data.data.decode() if latest and latest.inline_data else "?"
        print(f"  {k:16} versions={versions}  latest={body!r}")


if __name__ == "__main__":
    asyncio.run(main())
