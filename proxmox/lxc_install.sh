#!/usr/bin/env bash

# Media Curator Proxmox LXC Installer & Updater
# Powered by ProxmoxVE Community Scripts

set -eo pipefail

# --- App Specific Variables ---
export APP="Media-Curator"
export var_os="debian"
export var_version="12"
export var_cpu="1"
export var_ram="1024"
export var_disk="8"
export var_unprivileged="1"
export NSAPP="media-curator"

# --- Source Community Functions ---
source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)

function header_info() {
cat <<EOF
  __  __          _ _         _____                _             
 |  \/  |        | (_)       / ____|              | |            
 | \  / | ___  __| |_  __ _ | |    _   _ _ __ __ _| |_ ___  _ __ 
 | |\/| |/ _ \/ _  | |/ _  || |   | | | | '__/ _  | __/ _ \| '__|
 | |  | |  __/ (_| | | (_| || |___| |_| | | | (_| | || (_) | |   
 |_|  |_|\___|\__,_|_|\__,_| \_____\__,_|_|  \__,_|\__\___/|_|   
                                                                 
EOF
}

# This function runs when the script is executed INSIDE the LXC
function update_script() {
    header_info
    if [[ ! -d /opt/media-curator ]]; then
        msg_error "No ${APP} Installation Found!"
        exit 1
    fi
    
    msg_info "Updating ${APP}"
    # Fetch and run the app setup script which handles the actual logic (git pull, pip install, etc)
    curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/master/proxmox/app_setup.sh | bash
    msg_ok "Updated ${APP}"
}

# --- Execution Flow ---

# If we are NOT running in an LXC, we are on the Proxmox Host -> Install Mode
if [[ ! -d /etc/pve ]]; then
    # We are inside the container (or at least not on the host)
    update_script
    exit
fi

# We are on the host -> Run installation logic
header_info
variables
color
catch_errors
start
build_container
description
