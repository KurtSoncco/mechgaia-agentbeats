#!/bin/bash
# AgentBeats green agent launch script
# This script launches the green agent from the green-agent subdirectory
# It navigates to the project root and calls the main run.sh script

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

# Set agent type and role for green agent
export AGENT_TYPE=green
export ROLE=green

# Debug output
echo "Starting green agent from: $SCRIPT_DIR" >&2
echo "Project root: $PROJECT_ROOT" >&2
echo "HOST: ${HOST:-not set}" >&2
echo "AGENT_PORT: ${AGENT_PORT:-not set}" >&2

# Call the root run.sh script
exec "$PROJECT_ROOT/run.sh"
