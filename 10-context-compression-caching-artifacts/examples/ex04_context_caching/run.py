"""Model context caching — reuse a big static prefix across requests.

    python run.py

A large static instruction (a fake policy manual) is cached after the first call.
Subsequent turns reuse it: watch `cached_content_token_count` in usage_metadata
and the per-event cache_metadata.
"""

from __future__ import annotations

import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.agents.context_cache_config import ContextCacheConfig  
from google.adk.apps.app import App  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.genai import types  

APP, USER, MODEL = "cache_demo", "u1", "gemini-2.5-flash"

# ~2-3k tokens of static content so it clears the cache minimum.
POLICY = "COMPANY TRAVEL & EXPENSE POLICY\n\n" + "\n".join(
    f"Section {i}. " + ("Employees must submit receipts within 30 days. "
                        "Meals are capped at 60 USD/day domestic, 90 USD international. "
                        "Economy class for flights under 6 hours. Pre-approval required "
                        "for spend over 500 USD. Personal travel days are unpaid. ") * 3
    for i in range(1, 40)
)

agent = Agent(
    name="policy_bot", model=MODEL,
    # static_instruction is the part ADK will cache (stable across turns)
    instruction="Answer strictly from the policy above. Quote the relevant rule. Be brief.\n\n" + POLICY,
)

app = App(
    name=APP,
    root_agent=agent,
    context_cache_config=ContextCacheConfig(
        min_tokens=1024,      # only cache requests above this size
        ttl_seconds=600,      # keep the cache 10 minutes
        cache_intervals=10,   # reuse the same cache up to 10 times
    ),
)


async def main() -> None:
    ss = InMemorySessionService()
    runner = Runner(app=app, session_service=ss)
    s = await ss.create_session(app_name=APP, user_id=USER)

    for q in [
        "What's the domestic meal cap?",       # turn 1: cache is created
        "How long do I have to submit receipts?",  # turn 2: cache is REUSED
    ]:
        print(f"\nuser> {q}")
        try:
            async for ev in runner.run_async(
                user_id=USER, session_id=s.id,
                new_message=types.Content(role="user", parts=[types.Part(text=q)]),
            ):
                if ev.usage_metadata:
                    u = ev.usage_metadata
                    cached = getattr(u, "cached_content_token_count", None)
                    print(f"  usage: prompt={u.prompt_token_count} cached={cached} "
                          f"output={u.candidates_token_count}")
                cm = getattr(ev, "cache_metadata", None)
                if cm:
                    print(f"  cache_metadata: {cm}")
                if ev.is_final_response() and ev.content:
                    print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())
        except Exception as e:  # noqa: BLE001 — Vertex quota, not a caching bug
            print(f"  !! {type(e).__name__}: {str(e)[:90]}")


if __name__ == "__main__":
    asyncio.run(main())
