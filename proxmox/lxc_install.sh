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

# This function handles the private repository setup inside the newly created container.
# It is called explicitly after the container is built, since build_container in the 
# standard build.func runs an installer script for official community apps, which 404s for us.
function lxc_provision() {
  msg_info "Running Application Setup"
  
  # Retrieve host's GitHub token
  GH_TOKEN_VAL=""
  if command -v gh &> /dev/null; then
      GH_TOKEN_VAL=$(gh auth token 2>/dev/null || true)
  fi

  # Create a temporary file on the host to store the script
  TEMP_SCRIPT=$(mktemp)
  
  # Fetch app_setup.sh
  if [[ -n "$GH_TOKEN_VAL" ]]; then
      msg_info "Fetching app_setup.sh using GitHub CLI (private/authenticated path)..."
      gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh > "$TEMP_SCRIPT" 2>/dev/null || true
  fi
  
  # Fallback to curl if gh was not run or failed to fetch
  if [[ ! -s "$TEMP_SCRIPT" ]]; then
      msg_info "Fetching app_setup.sh using curl (public path)..."
      curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh > "$TEMP_SCRIPT" 2>/dev/null || true
  fi

  # Check if we successfully fetched the script
  if [[ ! -s "$TEMP_SCRIPT" ]]; then
      msg_error "Failed to retrieve app_setup.sh! Cannot provision the application."
      rm -f "$TEMP_SCRIPT"
      exit 1
  fi

  # Push the script into the container, make it executable, and run it
  msg_info "Pushing and executing setup script inside the container..."
  pct push "$CTID" "$TEMP_SCRIPT" /tmp/app_setup.sh
  pct exec "$CTID" -- chmod +x /tmp/app_setup.sh
  
  # Execute with GH_TOKEN if available so the container can clone/pull
  local exit_code=0
  if [[ -n "$GH_TOKEN_VAL" ]]; then
      pct exec "$CTID" -- env GH_TOKEN="$GH_TOKEN_VAL" /tmp/app_setup.sh || exit_code=$?
  else
      pct exec "$CTID" -- /tmp/app_setup.sh || exit_code=$?
  fi

  # Cleanup inside container and host
  pct exec "$CTID" -- rm -f /tmp/app_setup.sh
  rm -f "$TEMP_SCRIPT"

  if [[ $exit_code -ne 0 ]]; then
      msg_error "Application setup failed inside the container with exit code $exit_code!"
      exit $exit_code
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

    TEMP_SCRIPT=$(mktemp)

    # Fetch app_setup.sh
    if [[ -n "$GH_TOKEN_VAL" ]]; then
        gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/app_setup.sh > "$TEMP_SCRIPT" 2>/dev/null || true
    fi
    
    if [[ ! -s "$TEMP_SCRIPT" ]]; then
        curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/app_setup.sh > "$TEMP_SCRIPT" 2>/dev/null || true
    fi

    # Check if we successfully fetched the script
    if [[ ! -s "$TEMP_SCRIPT" ]]; then
        msg_error "Failed to retrieve app_setup.sh! Cannot update the application."
        rm -f "$TEMP_SCRIPT"
        exit 1
    fi

    # Make executable and run inside container
    chmod +x "$TEMP_SCRIPT"
    local exit_code=0
    if [[ -n "$GH_TOKEN_VAL" ]]; then
        env GH_TOKEN="$GH_TOKEN_VAL" "$TEMP_SCRIPT" || exit_code=$?
    else
        "$TEMP_SCRIPT" || exit_code=$?
    fi

    rm -f "$TEMP_SCRIPT"

    if [[ $exit_code -ne 0 ]]; then
        msg_error "Application update failed with exit code $exit_code!"
        exit $exit_code
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

# 3. Explicitly execute our custom provision function (since build.func installation 404s for custom apps)
lxc_provision

# 4. Display installation summary and next steps
description

msg_ok "Completed Successfully"
