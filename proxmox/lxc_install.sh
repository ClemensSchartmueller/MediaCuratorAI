#!/usr/bin/env bash

# Media Curator Proxmox LXC Installer
# Powered by ProxmoxVE Community Scripts

set -euo pipefail

# --- App Specific Variables ---
# These are used by build.func to configure the container
export APP="Media-Curator"
export var_os="debian"
export var_version="12"
export var_cpu="1"
export var_ram="1024"
export var_disk="8"
export var_unprivileged="1"
# We define a custom setup function that will be called after container creation
export NSAPP="media-curator"

# --- Source Community Functions ---
# This library handles storage selection, template downloads, and pct create logic
source <(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/misc/build.func)

# --- Overrides and Custom Logic ---

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

# The build_container function in build.func will call this if it exists
# to perform app-specific installation inside the container.
function update_script() {
    header_info
    echo -e "${GN}Running Application Setup...${CL}"
    
    # We download the app_setup.sh from the repository and run it
    # This ensures the latest version is used even if the local host script is older.
    curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/master/proxmox/app_setup.sh | bash
}

# --- Execution ---

# 1. Initialize environment
header_info
variables
color
catch_errors

# 2. Trigger standardized build process
# This handles:
# - Validating Proxmox host
# - Advanced vs Default settings prompt
# - Storage selection (fixes the "no such logical volume" issues)
# - Template download
# - pct create
# - Starting container
start

# 3. Build and Configure
build_container

# 4. Final Description
description
