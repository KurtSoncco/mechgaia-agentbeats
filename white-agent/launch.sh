#!/bin/bash
# Launch script for white agent controller
# Sets configuration variables and launches agentbeats controller

set -e  # Exit on error

# Change to the directory containing this script (where run.sh is located)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=white.mechgaia.org
export ROLE=white
export AGENT_TYPE=white
export PORT=8012

# Launch agentbeats controller (must be run from directory containing run.sh)
agentbeats run_ctrl
