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

# This function runs when the script is executed INSIDE the LXC (Update Mode)
function update_script() {
    header_info
    if [[ ! -d /opt/media-curator ]]; then
        msg_error "No ${APP} Installation Found!"
        exit 1
    fi
    
    msg_info "Updating ${APP}"
    GH_TOKEN_VAL=""
    if command -v gh &> /dev/null; then
        GH_TOKEN_VAL=$(gh auth token 2>/dev/null || true)
    fi

    if [[ -n "$GH_TOKEN_VAL" ]]; then
        (echo "export GH_TOKEN=\"$GH_TOKEN_VAL\""; gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh) | bash
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
    # We use the internal select_storage and provide fallbacks to ensure variables are set
    # Note: No msg_info here as it breaks the following whiptail dialogs
    if ! select_storage "container"; then
        STORAGE_RESULT=$(pvesm status -content rootdir | awk 'NR>1{print $1; exit}')
    fi
    CONTAINER_STORAGE="${STORAGE_RESULT:-local-lvm}"
    
    if ! select_storage "template"; then
        STORAGE_RESULT=$(pvesm status -content vztmpl | awk 'NR>1{print $1; exit}')
    fi
    TEMPLATE_STORAGE="${STORAGE_RESULT:-local}"

    # 3. Create LXC Container
    msg_info "Creating LXC Container"
    
    # Ensure CTID is set (exported for post-install)
    CTID=${CT_ID:-$(pvesh get /cluster/nextid)}
    
    # Get template
    pveam update >/dev/null
    TEMPLATE=$(pveam available -section system | grep "${var_os}-${var_version}" | head -1 | awk '{print $2}')
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE" >/dev/null || true

    # Create Container
    # Using the most robust storage:size syntax
    pct create "$CTID" "${TEMPLATE_STORAGE}:vztmpl/${TEMPLATE}" \
        --hostname "${HN:-$NSAPP}" \
        $PW \
        --rootfs "${CONTAINER_STORAGE}:${DISK_SIZE:-8}" \
        --memory "${RAM_SIZE:-1024}" \
        --cores "${CORE_COUNT:-1}" \
        --net0 "name=eth0,bridge=${BRG:-vmbr0},ip=${NET:-dhcp}${GATE:-}" \
        --onboot 1 \
        --unprivileged "${CT_TYPE:-1}" \
        --features "nesting=1"

    pct start "$CTID"
    msg_ok "Created LXC Container ${CTID}"

    msg_info "Running Application Setup"
    # Run app_setup.sh inside the container
    GH_TOKEN_VAL=""
    if command -v gh &> /dev/null; then
        GH_TOKEN_VAL=$(gh auth token 2>/dev/null || true)
    fi

    if [[ -n "$GH_TOKEN_VAL" ]]; then
        (echo "export GH_TOKEN=\"$GH_TOKEN_VAL\""; gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh) | pct exec "$CTID" -- bash
    else
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | pct exec "$CTID" -- bash
    fi
    
    description
}

# --- Execution Flow ---

# 1. Basic initialization
variables
color
catch_errors

# 2. Detect environment and start the appropriate flow
start
