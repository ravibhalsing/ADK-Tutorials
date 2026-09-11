"""Dump every field of every Event in one turn. The learning tool for Module 01.

Run from THIS folder:
    python inspect_events.py
    python inspect_events.py --sse      # same turn, StreamingMode.SSE (watch partials)

Read the output next to README.md §3 (the Event table).
"""

from __future__ import annotations

import argparse
import asyncio
import pathlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents.run_config import RunConfig, StreamingMode  # noqa: E402
from google.adk.runners import InMemoryRunner  # noqa: E402
from google.genai import types  # noqa: E402

from agent import root_agent  # noqa: E402

APP_NAME = "inspect"
PROMPT = "How many words are in the sentence: the quick brown fox jumps over the lazy dog"


def describe(event, i: int) -> None:
    parts = event.content.parts if (event.content and event.content.parts) else []
    kinds = []
    for p in parts:
        if getattr(p, "text", None):
            kinds.append(f"text[{len(p.text)} chars]")
        if getattr(p, "function_call", None):
            kinds.append(f"call {p.function_call.name}({dict(p.function_call.args)})")
        if getattr(p, "function_response", None):
            kinds.append(f"response {p.function_response.name}={p.function_response.response}")

    actions = event.actions
    act_summary = {
        "state_delta": dict(actions.state_delta) if actions.state_delta else {},
        "artifact_delta": dict(actions.artifact_delta) if actions.artifact_delta else {},
        "transfer_to_agent": actions.transfer_to_agent,
        "escalate": actions.escalate,
        "skip_summarization": actions.skip_summarization,
    }

    usage = ""
    if event.usage_metadata:
        u = event.usage_metadata
        usage = (
            f" tokens(prompt={u.prompt_token_count}, "
            f"candidates={u.candidates_token_count}, total={u.total_token_count})"
        )

    print(f"\n── event #{i} ─────────────────────────────────────────────")
    print(f"  author            : {event.author}")
    print(f"  id / invocation   : {event.id} / {event.invocation_id}")
    print(f"  partial           : {event.partial}")
    print(f"  turn_complete     : {event.turn_complete}")
    print(f"  is_final_response : {event.is_final_response()}")
    print(f"  content parts     : {kinds or '(none)'}")
    print(f"  actions           : { {k: v for k, v in act_summary.items() if v} or '(none)'}")
    print(f"  error             : {event.error_code} {event.error_message or ''}".rstrip())
    if usage:
        print(f"  usage            :{usage}")


async def main(streaming: bool) -> None:
    runner = InMemoryRunner(agent=root_agent, app_name=APP_NAME)
    session = await runner.session_service.create_session(
        app_name=APP_NAME, user_id="u1"
    )

    cfg = RunConfig(
        streaming_mode=StreamingMode.SSE if streaming else StreamingMode.NONE
    )
    print(f"PROMPT: {PROMPT}")
    print(f"StreamingMode: {'SSE' if streaming else 'NONE'}")

    i = 0
    async for event in runner.run_async(
        user_id="u1",
        session_id=session.id,
        new_message=types.Content(role="user", parts=[types.Part(text=PROMPT)]),
        run_config=cfg,
    ):
        i += 1
        describe(event, i)

    print(f"\nTotal events this turn: {i}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--sse", action="store_true", help="use StreamingMode.SSE")
    args = ap.parse_args()
    asyncio.run(main(args.sse))
