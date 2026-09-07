"""Run the hello agent WITHOUT the `adk` CLI — using the Runner API directly.

This is the same machinery `adk run` / `adk web` / `adk api_server` use under the hood.
You'll build on this pattern throughout the course (and it's how you embed an agent in
your own app in Module 21).

Run it:
    # from THIS folder (…/ex01_hello_agent), with the venv active and .env filled in:
    python run_programmatic.py

Auth: uses whatever your .env selects. This course uses the Vertex AI path, so you also
need a one-time `gcloud auth application-default login` on this machine.
"""

from __future__ import annotations

import asyncio
import pathlib

# Load .env FIRST — before importing agent.py, which reads os.environ["MODEL"] at import.
# (The `adk` CLI does this for you; a plain script must do it itself.)
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from agent import root_agent  # noqa: E402

APP_NAME = "hello_app"
USER_ID = "learner-001"


async def ask(runner: InMemoryRunner, session_id: str, text: str) -> None:
    """Send one user message and print the agent's response + any tool calls."""
    print(f"\n\033[1muser>\033[0m {text}")
    message = types.Content(role="user", parts=[types.Part(text=text)])

    async for event in runner.run_async(
        user_id=USER_ID, session_id=session_id, new_message=message
    ):
        # Surface tool calls / responses so you can see the agent "thinking".
        for call in event.get_function_calls():
            print(f"  \033[33m[tool call]\033[0m {call.name}({dict(call.args)})")
        for resp in event.get_function_responses():
            print(f"  \033[32m[tool result]\033[0m {resp.response}")

        # The final natural-language answer.
        if event.is_final_response() and event.content and event.content.parts:
            answer = "".join(p.text or "" for p in event.content.parts)
            print(f"\033[1magent>\033[0m {answer.strip()}")


async def main() -> None:
    print(f"(model: {root_agent.model})")

    # InMemoryRunner wires up InMemory session/artifact/memory services for you.
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)

    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID
    )

    # A short multi-turn conversation over one session (so history is retained).
    await ask(runner, session.id, "Hi there!")
    await ask(runner, session.id, "What's the time right now?")
    await ask(runner, session.id, "Thanks — remind me what you just told me.")


if __name__ == "__main__":
    asyncio.run(main())
