#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "========================================================"
echo "Starting CURRENT Production Pipeline Dashboard Server..."
echo "URL: http://127.0.0.1:8001"
echo "========================================================"
if [ -f "./.venv/bin/python3" ]; then
    ./.venv/bin/python3 current/server.py --port 8001 "$@"
elif [ -f "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]; then
    "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" current/server.py --port 8001 "$@"
else
    python3 current/server.py --port 8001 "$@"
fi
