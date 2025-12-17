#!/bin/bash

# Script to connect this repository to a new GitHub repository
# Usage: ./setup_new_repo.sh <your-github-username> <repo-name>

if [ $# -lt 2 ]; then
    echo "Usage: $0 <your-github-username> <repo-name>"
    echo "Example: $0 kurt-asus mechgaia-agentbeats"
    exit 1
fi

GITHUB_USER=$1
REPO_NAME=$2
NEW_REMOTE_URL="https://github.com/${GITHUB_USER}/${REPO_NAME}.git"

echo "Setting up new GitHub repository..."
echo "Repository URL: ${NEW_REMOTE_URL}"
echo ""

# Add the new remote
echo "Adding new remote 'origin'..."
git remote add origin "${NEW_REMOTE_URL}"

# Verify remote was added
echo ""
echo "Current remotes:"
git remote -v

echo ""
echo "Next steps:"
echo "1. Make sure you've created the repository '${REPO_NAME}' on GitHub"
echo "2. Commit your changes (if not already committed):"
echo "   git add -A"
echo "   git commit -m 'Initial commit: mechgaia-agentbeats project'"
echo "3. Push to the new repository:"
echo "   git push -u origin main"
echo ""
echo "Or run this script with --push flag to automatically push:"
echo "   $0 ${GITHUB_USER} ${REPO_NAME} --push"

# If --push flag is provided, push to the new repo
if [ "$3" == "--push" ]; then
    echo ""
    echo "Pushing to new repository..."
    git push -u origin main
    echo "Done! Your repository is now connected to the new GitHub repo."
fi
