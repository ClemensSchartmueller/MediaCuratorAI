#!/usr/bin/env bash

# Media Curator Proxmox LXC Installer & Updater
# Powered by ProxmoxVE Community Scripts

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
# We source this first so we can use its utility functions and hooks
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

# --- Hooks & Overrides ---

# This function is called by the standard install_script -> build_container -> lxc_provision
# We override it to handle our private repository setup
function lxc_provision() {
  msg_info "Running Application Setup"
  
  # Retrieve host's GitHub token
  GH_TOKEN_VAL=""
  if command -v gh &> /dev/null; then
      GH_TOKEN_VAL=$(gh auth token 2>/dev/null || true)
  fi

  # Run app_setup.sh inside the container
  if [[ -n "$GH_TOKEN_VAL" ]]; then
      (echo "export GH_TOKEN=\"$GH_TOKEN_VAL\""; gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh) | pct exec "$CTID" -- bash -s
  else
      curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh | pct exec "$CTID" -- bash -s
  fi
  
  msg_ok "Completed Application Setup"
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
    exit
}

# --- Execution Flow ---

# 1. Basic initialization from build.func
variables
color
catch_errors

# 2. Detect environment and start the appropriate flow (Install or Update)
# Standard start() will call install_script() which now uses the robust community flow
start
build_container
description

msg_ok "Completed Successfully"
