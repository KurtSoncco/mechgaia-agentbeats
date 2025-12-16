#!/bin/bash
# Fix AgentBeats state file issues

echo "Cleaning up AgentBeats state files..."

# Remove .ab directory to start fresh (AgentBeats will recreate it)
if [ -d ".ab" ]; then
    echo "Removing .ab directory..."
    rm -rf .ab
    echo "✅ Cleaned up .ab directory"
    echo "AgentBeats will recreate it on next run"
else
    echo "No .ab directory found"
fi

echo ""
echo "To start Cloudflare tunnel, use:"
echo "  uv run python main.py run-ctrl"
echo ""
echo "NOT: agentbeats run_ctrl (that's AgentBeats' controller, different thing!)"

