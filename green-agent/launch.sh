# /mechgaia-agentbeats/green/launch.sh
#!/bin/bash

set -e

# set configuration variables
export HTTPS_ENABLED=true
export CLOUDRUN_HOST=green.mechgaia.org
export ROLE=green
export PORT=8010

# launch agentbeats controller
agentbeats run_ctrl
