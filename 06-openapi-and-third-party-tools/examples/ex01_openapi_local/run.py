"""Start the Bookstore API, run the agent against its generated tools, stop the API.

    python run.py
"""

from __future__ import annotations

import asyncio
import pathlib
import socket
import subprocess
import sys
import time

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

HERE = pathlib.Path(__file__).parent


def _wait_port(host: str, port: int, timeout: float = 15) -> bool:
    end = time.time() + timeout
    while time.time() < end:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return True
        time.sleep(0.3)
    return False


async def main() -> None:
    server = subprocess.Popen([sys.executable, str(HERE / "api_server.py")])
    try:
        if not _wait_port("127.0.0.1", 8001):
            raise RuntimeError("API server didn't start")
        print("Bookstore API up on :8001\n")

        # import AFTER the server is up so the spec loads
        from google.adk.runners import InMemoryRunner
        from google.genai import types
        import agent as agent_mod

        runner = InMemoryRunner(agent=agent_mod.root_agent, app_name="bookstore")
        s = await runner.session_service.create_session(app_name="bookstore", user_id="u1")

        for q in [
            "List the books by Kleppmann and how many are in stock.",
            "Please add 'The Mythical Man-Month' by Fred Brooks, published 1975. Yes, go ahead.",
            "Show me book id 99.",
        ]:
            print(f"user> {q}")
            try:
                async for ev in runner.run_async(
                    user_id="u1", session_id=s.id,
                    new_message=types.Content(role="user", parts=[types.Part(text=q)]),
                ):
                    for c in ev.get_function_calls():
                        print(f"  [api call] {c.name}({dict(c.args)})")
                    for r in ev.get_function_responses():
                        print(f"  [api resp] {str(r.response)[:160]}")
                    if ev.is_final_response() and ev.content:
                        print("agent>", "".join(p.text or "" for p in ev.content.parts).strip(), "\n")
            except Exception as e:  # noqa: BLE001
                print(f"  !! {type(e).__name__}: {str(e)[:160]}\n")
    finally:
        server.terminate()


if __name__ == "__main__":
    asyncio.run(main())
