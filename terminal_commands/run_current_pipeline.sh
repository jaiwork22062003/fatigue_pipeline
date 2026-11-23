#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
echo "========================================================"
echo "Starting OWN Sense CURRENT Production Pipeline..."
echo "========================================================"
if [ -f "./.venv/bin/python3" ]; then
    ./.venv/bin/python3 current/run_pipeline.py "$@"
elif [ -f "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" ]; then
    "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3" current/run_pipeline.py "$@"
else
    python3 current/run_pipeline.py "$@"
fi
