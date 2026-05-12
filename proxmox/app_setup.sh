#!/usr/bin/env bash

# Media Curator LXC Setup Script (Internal)
# This script runs INSIDE the LXC container.

set -e

# --- Configuration ---
APP_DIR="/opt/media-curator"
REPO_URL="https://github.com/ClemensSchartmueller/MediaCuratorAI.git"

echo "Updating container OS..."
apt-get update && apt-get upgrade -y
apt-get install -y python3 python3-venv git curl sqlite3

echo "Cloning Media Curator..."
git clone $REPO_URL $APP_DIR || (cd $APP_DIR && git pull)
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

echo "Setup complete!"
echo "Next steps:"
echo "1. Edit /opt/media-curator/.env with your credentials."
echo "2. Run: cd /opt/media-curator && ./venv/bin/python main.py profile"
echo "3. Restart services: systemctl restart media-curator.service"
