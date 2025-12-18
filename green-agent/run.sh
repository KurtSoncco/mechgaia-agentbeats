# /mechgaia-agentbeats/green/run.sh
#!/bin/bash

set -e

# entrypoint for green agent
export ROLE=green

cd ../
python main.py run
