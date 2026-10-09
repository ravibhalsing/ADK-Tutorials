"""Files in and out: upload an image, agent describes it, saves the description
as an artifact, then LoadArtifactsTool recalls it in a later turn.

    python run.py
"""

from __future__ import annotations

import asyncio
import pathlib
import struct
import zlib

from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).parent / ".env")

from google.adk.agents import Agent  
from google.adk.artifacts import InMemoryArtifactService  
from google.adk.runners import Runner  
from google.adk.sessions import InMemorySessionService  
from google.adk.tools import ToolContext  
from google.adk.tools.load_artifacts_tool import LoadArtifactsTool  
from google.genai import types  

APP, USER, MODEL = "files_demo", "u1", "gemini-2.5-flash"


def _solid_png(w: int, h: int, rgb: tuple[int, int, int]) -> bytes:
    """Minimal PNG encoder — a solid colour rectangle."""
    def chunk(tag: bytes, data: bytes) -> bytes:
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))


async def save_caption(caption: str, tool_context: ToolContext) -> dict:
    """Save a one-line caption for the uploaded image as an artifact."""
    part = types.Part.from_bytes(data=caption.encode(), mime_type="text/plain")
    v = await tool_context.save_artifact(filename="caption.txt", artifact=part)
    return {"status": "success", "version": v}


agent = Agent(
    name="vision", model=MODEL,
    instruction=(
        "Turn 1: describe the uploaded image in one sentence, then call save_caption "
        "with that sentence.\n"
        "Later turns: if asked what the image showed, use load_artifacts to read "
        "caption.txt and answer from it."
    ),
    tools=[save_caption, LoadArtifactsTool()],
)


async def main() -> None:
    art = InMemoryArtifactService()
    ss = InMemorySessionService()
    runner = Runner(agent=agent, app_name=APP, session_service=ss, artifact_service=art)
    s = await ss.create_session(app_name=APP, user_id=USER)

    png = _solid_png(24, 16, (30, 144, 255))     # a dodger-blue rectangle
    print(f"(uploading a {len(png)}-byte PNG)\n")

    turn1 = types.Content(role="user", parts=[
        types.Part(text="What's in this image?"),
        types.Part.from_bytes(data=png, mime_type="image/png"),
    ])
    print("user> What's in this image?  [+image]")
    async for ev in runner.run_async(user_id=USER, session_id=s.id, new_message=turn1):
        for c in ev.get_function_calls():
            print(f"  [call] {c.name}({dict(c.args)})")
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    print("\nuser> Remind me what that image showed.")
    turn2 = types.Content(role="user", parts=[types.Part(text="Remind me what that image showed.")])
    async for ev in runner.run_async(user_id=USER, session_id=s.id, new_message=turn2):
        for c in ev.get_function_calls():
            print(f"  [call] {c.name}({dict(c.args)})")
        if ev.is_final_response() and ev.content:
            print("agent>", "".join(p.text or "" for p in ev.content.parts).strip())

    keys = await art.list_artifact_keys(app_name=APP, user_id=USER, session_id=s.id)
    print("\nartifacts:", keys)


if __name__ == "__main__":
    asyncio.run(main())
