"""VertexAiMemoryBankService - managed, semantic, cross-session memory.

NEEDS an Agent Engine instance. Create one (one-time):

    from vertexai import agent_engines           # pip install "google-cloud-aiplatform[adk,agent_engines]"
    import vertexai
    vertexai.init(project="gcp-learning-469104", location="us-central1")
    ae = agent_engines.create()                  # empty engine, just for memory + sessions
    print(ae.resource_name)                       # projects/.../locations/.../reasoningEngines/NNNN

Then set in .env:
    AGENT_ENGINE_ID=NNNN         (just the trailing number, or the full resource name)

Run:
    python run.py

Without AGENT_ENGINE_ID this prints the setup steps and exits.
"""

from __future__ import annotations

import asyncio
import os
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
LOCATION = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
ENGINE = os.environ.get("AGENT_ENGINE_ID", "").strip()


async def main() -> None:
    if not ENGINE:
        print(__doc__)
        return

    from google.adk.agents import Agent
    from google.adk.memory import VertexAiMemoryBankService
    from google.adk.runners import Runner
    from google.adk.sessions import VertexAiSessionService
    from google.adk.tools import preload_memory
    from google.genai import types

    memory_service = VertexAiMemoryBankService(
        project=PROJECT, location=LOCATION, agent_engine_id=ENGINE
    )
    session_service = VertexAiSessionService(project=PROJECT, location=LOCATION)

    async def auto_save(cb) -> None:
        await cb.add_session_to_memory()

    agent = Agent(
        name="assistant", model="gemini-2.5-flash",
        instruction="Personal assistant. Use what you remember about the user.",
        tools=[preload_memory],
        after_agent_callback=auto_save,
    )
    runner = Runner(agent=agent, app_name=ENGINE, session_service=session_service,
                    memory_service=memory_service)

    s1 = await session_service.create_session(app_name=ENGINE, user_id="u1")
    async for _ in runner.run_async(
        user_id="u1", session_id=s1.id,
        new_message=types.Content(role="user", parts=[types.Part(text="I'm vegetarian and I live in Pune.")]),
    ):
        pass
    print("captured turn 1 (auto-saved + consolidated by Memory Bank)")

    s2 = await session_service.create_session(app_name=ENGINE, user_id="u1")
    async for ev in runner.run_async(
        user_id="u1", session_id=s2.id,
        new_message=types.Content(role="user", parts=[types.Part(text="Suggest a lunch spot for me.")]),
    ):
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())


if __name__ == "__main__":
    asyncio.run(main())
