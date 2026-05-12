#!/usr/bin/env bash

# Media Curator Proxmox LXC Installer
# Inspired by ProxmoxVE Community Scripts

set -euo pipefail

# --- Defaults ---
CT_ID=$(pvesh get /cluster/nextid)
CT_NAME="media-curator"
DISK_SIZE="8G"
RAM="1024"
CORES="1"
BRIDGE="vmbr0"
GATEWAY=""
IP_ADDRESS="dhcp"
STORAGE="local-lvm"
PASSWORD="media" # Default password, user should change it

echo "-------------------------------------------------------"
echo "  Media Curator LXC Installer for Proxmox VE"
echo "-------------------------------------------------------"

# Check if running on Proxmox
if ! command -v pveversion >/dev/null 2>&1; then
    echo "Error: This script must be run on a Proxmox VE host."
    exit 1
fi

# Ask for configuration (simplified for now)
read -p "Enter Container ID [$CT_ID]: " input_id
CT_ID=${input_id:-$CT_ID}

read -p "Enter Hostname [$CT_NAME]: " input_name
CT_NAME=${input_name:-$CT_NAME}

# Check if container already exists
if pct status $CT_ID >/dev/null 2>&1; then
    echo "Error: Container $CT_ID already exists."
    exit 1
fi

echo "Fetching Debian 12 template..."
pveam update
TEMPLATE=$(pveam available -section system | grep "debian-12-standard" | head -1 | awk '{print $2}')
STORAGE_PATH=$(pvesm path $STORAGE)
TEMPLATE_PATH="${STORAGE_PATH}/template/cache/${TEMPLATE}"

if [ ! -f "$TEMPLATE_PATH" ]; then
    echo "Downloading template: $TEMPLATE..."
    pveam download local $TEMPLATE
fi

echo "Creating LXC container $CT_ID ($CT_NAME)..."
pct create $CT_ID "local:vztmpl/$TEMPLATE" \
    --hostname $CT_NAME \
    --password $PASSWORD \
    --storage $STORAGE \
    --rootfs $STORAGE:$DISK_SIZE \
    --memory $RAM \
    --cores $CORES \
    --net0 name=eth0,bridge=$BRIDGE,ip=$IP_ADDRESS \
    --onboot 1 \
    --unprivileged 1 \
    --features nesting=1

echo "Starting container..."
pct start $CT_ID

echo "Waiting for network to be ready..."
sleep 5

# Transfer and run setup script
echo "Running application setup inside container..."
# In a real scenario, we might download the script directly in the LXC or pipe it
cat proxmox/app_setup.sh | pct exec $CT_ID -- bash

echo "-------------------------------------------------------"
echo "  Installation Complete!"
echo "  Container ID: $CT_ID"
echo "  Hostname: $CT_NAME"
echo "  Access it via: pct enter $CT_ID"
echo "-------------------------------------------------------"
