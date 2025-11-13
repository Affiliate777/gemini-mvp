#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
if [ -f ".venv/bin/activate" ]; then
  . .venv/bin/activate
fi

SESSION="gemini"
PORT="${GEMINI_PORT:-8765}"

if command -v tmux >/dev/null 2>&1; then
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "tmux session '$SESSION' already running. Attach with: tmux attach -t $SESSION"
    exit 0
  fi
  echo "Starting mock server in tmux session '$SESSION' (port $PORT)..."
  tmux new-session -d -s "$SESSION" "export GEMINI_PORT=$PORT; PYTHONPATH=. python3 -u -m runtime.mock_server"
  echo "Attach: tmux attach -t $SESSION"
else
  echo "tmux not found — running server in foreground (press Ctrl-C to stop)"
  export GEMINI_PORT=$PORT
  PYTHONPATH=. python3 -u -m runtime.mock_server
fi
