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
    # Use GitHub CLI if available, otherwise fallback to curl
    if command -v gh &> /dev/null; then
        gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh | bash
    else
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | bash
    fi
    msg_ok "Updated ${APP}"
}

# This function runs on the Proxmox Host to handle the installation
function install_script() {
    # 1. Initialize environment and get user configuration
    variables
    color
    catch_errors
    
    # 2. Storage Selection and Confirmation
    # The 'start' logic in build.func handles the Default/Advanced prompt
    # but we need to ensure the variables are set correctly for our manual creation.
    # Note: build.func handles most of this in advanced_settings/base_settings
    
    msg_info "Creating LXC Container"
    
    # Get template
    pveam update >/dev/null
    TEMPLATE=$(pveam available -section system | grep "${var_os}-${var_version}" | head -1 | awk '{print $2}')
    msg_info "Using template: ${TEMPLATE} on ${TEMPLATE_STORAGE}"
    pveam download $TEMPLATE_STORAGE $TEMPLATE >/dev/null || true

    # Create Container
    # We use the variables set by the library's prompts
    pct create $CT_ID "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}" \
        --hostname $HN \
        --password $PASSWORD \
        --rootfs "volume=${CONTAINER_STORAGE},size=${DISK_SIZE}G" \
        --memory $RAM_SIZE \
        --cores $CORE_COUNT \
        --net0 name=eth0,bridge=$BRG,ip=$NET$GATE \
        --onboot 1 \
        --unprivileged $CT_TYPE \
        --features nesting=1

    pct start $CT_ID
    msg_ok "Created LXC Container ${CT_ID}"

    msg_info "Running Application Setup"
    # Run app_setup.sh inside the container
    if command -v gh &> /dev/null; then
        gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh | pct exec $CT_ID -- bash
    else
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | pct exec $CT_ID -- bash
    fi
    
    description
}

# --- Execution Flow ---

# The start function in build.func will:
# 1. Detect if running on host (via pveversion)
# 2. If host: Call install_script
# 3. If container: Call update_script
start
