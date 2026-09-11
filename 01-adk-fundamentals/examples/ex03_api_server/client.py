"""Minimal HTTP client for `adk api_server` — stdlib only, no dependencies.

Prereq: in another terminal, from …/01-adk-fundamentals/examples:
    adk api_server

Then:
    python client.py
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

BASE = "http://localhost:8000"
APP = "ex01_multi_tool_agent"
USER = "u1"
SESSION = "s1"


def _req(method: str, path: str, body: dict | None = None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        BASE + path, data=data, method=method,
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        raw = resp.read().decode()
    return json.loads(raw) if raw else None


def list_apps():
    print("GET /list-apps")
    apps = _req("GET", "/list-apps")
    print("  ->", apps)
    return apps


def create_session():
    path = f"/apps/{APP}/users/{USER}/sessions/{SESSION}"
    print(f"POST {path}")
    try:
        s = _req("POST", path, {})
        print("  -> created:", {k: s[k] for k in ("id", "appName", "userId")})
    except urllib.error.HTTPError as e:
        # 400/409 if it already exists from a previous run — fine for a demo
        print(f"  -> {e.code} (session probably already exists, continuing)")


def run_collect(text: str):
    print(f'\nPOST /run   newMessage="{text}"')
    events = _req("POST", "/run", {
        "appName": APP, "userId": USER, "sessionId": SESSION,
        "newMessage": {"role": "user", "parts": [{"text": text}]},
    })
    print(f"  -> {len(events)} events")
    for ev in events:
        _print_event(ev)


def run_sse(text: str):
    print(f'\nPOST /run_sse   newMessage="{text}"  (streaming)')
    body = json.dumps({
        "appName": APP, "userId": USER, "sessionId": SESSION,
        "newMessage": {"role": "user", "parts": [{"text": text}]},
        "streaming": True,
    }).encode()
    req = urllib.request.Request(
        BASE + "/run_sse", data=body, method="POST",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        for line in resp:
            line = line.decode().strip()
            if line.startswith("data:"):
                _print_event(json.loads(line[5:].strip()), prefix="  data: ")


def _print_event(ev: dict, prefix: str = "  ") -> None:
    author = ev.get("author", "?")
    parts = (ev.get("content") or {}).get("parts") or []
    for p in parts:
        if "functionCall" in p:
            fc = p["functionCall"]
            print(f"{prefix}[{author}] functionCall  {fc['name']}({fc.get('args', {})})")
        elif "functionResponse" in p:
            fr = p["functionResponse"]
            print(f"{prefix}[{author}] functionResp  {fr['name']} -> {fr.get('response')}")
        elif "text" in p and p["text"]:
            partial = " (partial)" if ev.get("partial") else ""
            print(f"{prefix}[{author}] text{partial}  {p['text']!r}")


if __name__ == "__main__":
    list_apps()
    create_session()
    run_collect("weather in Paris?")
    run_sse("and what time is it there?")
