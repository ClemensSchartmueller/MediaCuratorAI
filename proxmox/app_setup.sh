#!/usr/bin/env bash

# Media Curator LXC Setup Script (Internal)
# This script runs INSIDE the LXC container.

set -e

# --- Configuration ---
APP_DIR="/opt/media-curator"
REPO_URL="https://github.com/ClemensSchartmueller/MediaCuratorAI.git"

echo "Updating container OS..."
apt-get update && apt-get upgrade -y
# Added python3-pip to ensure virtual environments can bootstrap pip without ensurepip errors on Debian
apt-get install -y python3 python3-venv python3-pip git curl sqlite3

# Install GitHub CLI if GH_TOKEN is provided and gh is not installed
if [[ -n "$GH_TOKEN" ]] && ! command -v gh &> /dev/null; then
    echo "Installing GitHub CLI..."
    mkdir -p -m 755 /etc/apt/keyrings
    curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | tee /etc/apt/keyrings/githubcli-archive-keyring.gpg > /dev/null
    chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | tee /etc/apt/keyrings/githubcli.list > /dev/null
    apt-get update
    apt-get install gh -y
fi

if [[ -n "$GH_TOKEN" ]]; then
    echo "Authenticating GitHub CLI..."
    # We must unset GH_TOKEN so gh auth login can actually write to the config file
    # otherwise it just uses the env var and might skip the login process or warn.
    _TOKEN="$GH_TOKEN"
    (unset GH_TOKEN; echo "$_TOKEN" | gh auth login --with-token)
fi

echo "Cloning Media Curator..."
if command -v gh &> /dev/null; then
    gh repo clone ClemensSchartmueller/MediaCuratorAI $APP_DIR || (cd $APP_DIR && git pull)
else
    # Fallback to git with token if available
    if [[ -n "$GH_TOKEN" ]]; then
        git clone https://x-access-token:${GH_TOKEN}@github.com/ClemensSchartmueller/MediaCuratorAI.git $APP_DIR || (cd $APP_DIR && git pull)
    else
        git clone $REPO_URL $APP_DIR || (cd $APP_DIR && git pull)
    fi
fi
cd $APP_DIR

echo "Setting up virtual environment..."
python3 -m venv venv
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install -r requirements.txt

echo "Configuring environment..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit $APP_DIR/.env with your API keys later."
fi

echo "Installing systemd services..."
cp deployment/media-curator.service /etc/systemd/system/
cp deployment/media-curator-discovery.service /etc/systemd/system/
cp deployment/media-curator-discovery.timer /etc/systemd/system/

systemctl daemon-reload
systemctl enable --now media-curator.service
systemctl enable --now media-curator-discovery.timer

# Restart the daemon service to ensure any newly pulled python code is loaded
echo "Restarting service to apply updates..."
systemctl restart media-curator.service

echo "Setup complete!"
echo "Next steps:"
echo "1. Edit /opt/media-curator/.env with your credentials."
echo "2. Run: cd /opt/media-curator && ./venv/bin/python main.py profile"
echo "3. Restart services: systemctl restart media-curator.service"
