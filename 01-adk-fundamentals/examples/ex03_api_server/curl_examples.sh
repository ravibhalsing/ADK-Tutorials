#!/usr/bin/env bash
# Raw HTTP against `adk api_server`. Run under Git Bash (Windows) or any bash.
# Start the server first, from  …/01-adk-fundamentals/examples :   adk api_server
set -euo pipefail

BASE=http://localhost:8000
APP=ex01_multi_tool_agent
USER=u1
SESSION=s1

echo "== list apps =="
curl -s "$BASE/list-apps"; echo

echo "== create session =="
curl -s -X POST "$BASE/apps/$APP/users/$USER/sessions/$SESSION" \
  -H 'Content-Type: application/json' -d '{}'; echo

echo "== /run (collect all events) =="
curl -s -X POST "$BASE/run" -H 'Content-Type: application/json' -d "{
  \"appName\": \"$APP\", \"userId\": \"$USER\", \"sessionId\": \"$SESSION\",
  \"newMessage\": {\"role\": \"user\", \"parts\": [{\"text\": \"weather in Paris?\"}]}
}"; echo

echo "== /run_sse (stream events) =="
curl -sN -X POST "$BASE/run_sse" -H 'Content-Type: application/json' -d "{
  \"appName\": \"$APP\", \"userId\": \"$USER\", \"sessionId\": \"$SESSION\",
  \"newMessage\": {\"role\": \"user\", \"parts\": [{\"text\": \"and the time there?\"}]},
  \"streaming\": true
}"; echo

echo "== get session (state + full event history) =="
curl -s "$BASE/apps/$APP/users/$USER/sessions/$SESSION"; echo

echo "== delete session =="
curl -s -X DELETE "$BASE/apps/$APP/users/$USER/sessions/$SESSION"; echo
