#!/usr/bin/env python3
"""Start AgentBeats controller with both agents."""

import os
import sys
from pathlib import Path

# Set port to 8000 BEFORE importing (settings are initialized at import time)
os.environ["PORT"] = "8000"

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from agentbeats.controller import main as controller_main
except ImportError:
    print("Error: agentbeats (earthshaker package) not installed.")
    print("The package 'earthshaker' installs as 'agentbeats' module.")
    print("Install it with:")
    print("  uv pip install earthshaker")
    print("  or: uv sync")
    sys.exit(1)

if __name__ == "__main__":
    print("Starting AgentBeats controller...")
    print("  Controller will run on port 8000")
    print("  The controller will look for 'run.sh' to start agents")
    print("  Make sure 'run.sh' is in the current directory")
    print("")

    # The controller.main() function:
    # - Looks for run.sh in current directory
    # - Creates agent instances in .ab/agents/
    # - Starts the FastAPI controller server on the configured port
    # - Manages agent lifecycle
    controller_main()
