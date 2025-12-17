#!/bin/bash

source .venv/bin/activate 2>/dev/null || true

# White agent runs on port 9003 (controller uses 9002 for Cloudflare)
# Set default host if not provided
HOST="${HOST:-0.0.0.0}"
PORT=9003

exec uv run python -m main white --host "$HOST" --port "$PORT"
