#!/bin/bash
# Launch script for green agent controller
# Sets configuration variables and launches agentbeats controller

set -e  # Exit on error

# Change to the directory containing this script (where run.sh is located)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=green.mechgaia.org
export ROLE=green
export AGENT_TYPE=green
export PORT=8011

# Launch agentbeats controller (must be run from directory containing run.sh)
agentbeats run_ctrl
