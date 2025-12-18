# /mechgaia-agentbeats/white/launch.sh
#!/bin/bash

set -e

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=white.mechgaia.org
export ROLE=white
export PORT=8012

# launch agentbeats controller
agentbeats run_ctrl
