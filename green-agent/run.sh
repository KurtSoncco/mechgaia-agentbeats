#!/bin/bash
# Entrypoint for green agent
# This script is called by the agentbeats controller to start the agent

set -e  # Exit on error

# Navigate to project root (parent directory)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT" || exit 1

# Verify main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in $PROJECT_ROOT" >&2
    exit 1
fi

# Run the agent
python main.py run
