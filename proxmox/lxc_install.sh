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
# We source the library to get access to whiptail menus, storage selection, and UI helpers
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

# This function runs when the script is executed INSIDE the LXC (Update Mode)
function update_script() {
    header_info
    if [[ ! -d /opt/media-curator ]]; then
        msg_error "No ${APP} Installation Found!"
        exit 1
    fi
    
    msg_info "Updating ${APP}"
    if command -v gh &> /dev/null; then
        gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh | bash
    else
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | bash
    fi
    msg_ok "Updated ${APP}"
}

# This function overrides the community's install_script to handle our custom installation flow
function install_script() {
    # 1. Populate Variables based on Method (Default/Advanced)
    base_settings
    if [[ "$METHOD" == "advanced" ]]; then
        advanced_settings
    fi
    
    # 2. Storage Selection
    # We use a temporary file for the library's storage selection logic
    VARS_FILE="/tmp/media-curator.vars"
    touch "$VARS_FILE"
    
    # We remove msg_info here as it breaks the following whiptail dialogs
    choose_and_set_storage_for_file "$VARS_FILE" "container"
    CONTAINER_STORAGE=$STORAGE_RESULT
    
    choose_and_set_storage_for_file "$VARS_FILE" "template"
    TEMPLATE_STORAGE=$STORAGE_RESULT

    # 3. Create LXC Container
    msg_info "Creating LXC Container"
    
    # Get template
    pveam update >/dev/null
    TEMPLATE=$(pveam available -section system | grep "${var_os}-${var_version}" | head -1 | awk '{print $2}')
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE" >/dev/null || true

    # Create Container
    pct create "$CT_ID" "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}" \
        --hostname "$HN" \
        --password "$PASSWORD" \
        --rootfs "volume=${CONTAINER_STORAGE},size=${DISK_SIZE}G" \
        --memory "$RAM_SIZE" \
        --cores "$CORE_COUNT" \
        --net0 "name=eth0,bridge=${BRG:-vmbr0},ip=${NET:-dhcp}${GATE:-}" \
        --onboot 1 \
        --unprivileged "$CT_TYPE" \
        --features "nesting=1"

    pct start "$CT_ID"
    msg_ok "Created LXC Container ${CT_ID}"

    msg_info "Running Application Setup"
    # Run app_setup.sh inside the container
    if command -v gh &> /dev/null; then
        gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh | pct exec "$CT_ID" -- bash
    else
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | pct exec "$CT_ID" -- bash
    fi
    
    description
}

# --- Execution Flow ---

# 1. Basic initialization
# Note: We do NOT call header_info here as it breaks the whiptail UI initialization in start
variables
color
catch_errors

# 2. Detect environment and start the appropriate flow
start
