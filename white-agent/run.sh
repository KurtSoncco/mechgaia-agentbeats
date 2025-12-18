# /mechgaia-agentbeats/white/run.sh
#!/bin/bash

set -e

# entrypoint for white agent
export ROLE=white

cd ../
python main.py run
