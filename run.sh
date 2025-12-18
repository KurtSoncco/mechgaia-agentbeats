#!/bin/bash
# AgentBeats controller launch script
# This script is used by the AgentBeats controller to start the agent
# The controller will set HOST and AGENT_PORT environment variables

set -e  # Exit on error

# Determine which agent to run (default to green if not specified)
AGENT_TYPE=${AGENT_TYPE:-green}

# Set ROLE based on AGENT_TYPE for compatibility with existing code
if [ "$AGENT_TYPE" = "green" ]; then
    ROLE=green
elif [ "$AGENT_TYPE" = "white" ]; then
    ROLE=white
else
    echo "ERROR: Unknown AGENT_TYPE: $AGENT_TYPE (must be 'green' or 'white')" >&2
    exit 1
fi

# Change to script directory (where main.py is located)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# In Cloud Run Buildpacks, the working directory might be /workspace
# but our code is in the app root, so ensure we're in the right place
if [ ! -f "main.py" ]; then
    # Try to find main.py in parent directories or current location
    if [ -f "/workspace/main.py" ]; then
        cd /workspace || exit 1
    elif [ -f "./main.py" ]; then
        # Already in right place
        :
    else
        echo "ERROR: main.py not found in $(pwd) or /workspace" >&2
        ls -la >&2
        exit 1
    fi
fi

# Debug: Print environment info
echo "Starting agent (type: $AGENT_TYPE, role: $ROLE)" >&2
echo "Working directory: $(pwd)" >&2
echo "HOST: ${HOST:-not set}" >&2
echo "AGENT_PORT: ${AGENT_PORT:-not set}" >&2

# Find and activate .venv
VENV_PATH=""
if [ -d ".venv" ]; then
    VENV_PATH="$(pwd)/.venv"
elif [ -d "../.venv" ]; then
    VENV_PATH="$(cd .. && pwd)/.venv"
elif [ -d "/workspace/.venv" ]; then
    VENV_PATH="/workspace/.venv"
fi

if [ -n "$VENV_PATH" ] && [ -f "$VENV_PATH/bin/activate" ]; then
    echo "Activating venv at: $VENV_PATH" >&2
    source "$VENV_PATH/bin/activate"
    echo "Venv activated successfully" >&2
else
    echo "WARNING: .venv not found, using system Python" >&2
fi

# Try python3 first, fall back to python
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "ERROR: Python not found!" >&2
    exit 1
fi

echo "Python path: $(which $PYTHON_CMD)" >&2
echo "Python version: $($PYTHON_CMD --version)" >&2

# Run the agent directly - all output to stderr so controller captures it
echo "Launching agent with: $PYTHON_CMD main.py run" >&2

# Test if Python can even run a simple command
echo "Testing Python execution..." >&2
$PYTHON_CMD -c "import sys; print('Python works!', file=sys.stdout, flush=True)"

# Export ROLE for main.py to use
export ROLE

# Now run main.py directly - use -u for unbuffered output
# All output goes to stderr so controller can capture it
echo "Running main.py..." >&2
exec $PYTHON_CMD -u -W all main.py run 2>&1
