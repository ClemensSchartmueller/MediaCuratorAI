# Media Curator AI

AI-driven media recommendation daemon for self-hosted stacks.

## Features
- **Taste Profiler:** Analyzes Jellyfin history to understand what you like.
- **Hybrid Discovery:** Finds new VOD/Digital releases on TMDB and filters against your existing library.
- **AI Curation:** Uses Google Gemini with Google Search grounding to pick the best releases based on your profile.
- **Interactive Agentic Telegram Integration:** Weekly recommendations and agent responses are formatted beautifully using premium, Telegram-compatible HTML (supporting stylized headers, bulleted lists, code blocks, bold/italics, and links). Powered by a custom Markdown-to-HTML formatter with a bulletproof plain-text fallback. You can chat with the bot to:
  - **Request recommendations on-demand:** "Give me new recommendations" (forces fresh Jellyfin history profiling and TMDB discovery).
  - **Discover by genre:** "What are some good recent comedy movies?" or "Show me scary TV series".
  - **Ask for details:** "Tell me about Interstellar" or "What is the plot of Dune?".
  - **Download specific media directly:** "Download Inception" or "Add Breaking Bad to my library".
- **Resilient API Calls:** Automatic retry logic with real-time status updates posted directly in Telegram if API timeouts or rate limits occur. Includes dynamic root folder and quality profile validation (with fallback to the first available options if misconfigured) and proactive duplicate pre-checks to reduce common "Bad Request" scenarios.
- **Context History Management:** Smart session tracking avoids expanding Gemini context windows, controls API costs, and survives system restarts:
  - **Persistent Conversational Memory:** Conversation history, last interaction timestamps, and compressed context summaries are saved in the local SQLite database, ensuring memory survives service or container restarts.
  - **Automatic 24-Hour Compression:** If you don't message the bot for 24 hours, it automatically compresses the conversation history into a concise context summary.
  - **Manual Clear/Compress Commands:** Send `/clear` or `/compress` directly in Telegram, or conversationally ask the bot *"please clear my history"* or *"compress our conversation"*, and the agent will execute the tool autonomously.

## Proxmox LXC Installation

If you are running Proxmox VE, you can use the automated installer. Run this command on your **Proxmox host**:

```bash
# Using curl (recommended and standard on Proxmox)
bash -c "$(curl -fsSL https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/lxc_install.sh)"

# Or using wget
bash -c "$(wget -qO- https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/lxc_install.sh)"

# Or using GitHub CLI (for private/authenticated access)
bash -c "$(gh api -H "Accept: application/vnd.github.raw" /repos/ClemensSchartmueller/MediaCuratorAI/contents/proxmox/lxc_install.sh)"
```

Alternatively, if you have the repo cloned locally on the host:
```bash
bash proxmox/lxc_install.sh
```

### Updating the LXC Container

The Proxmox LXC setup supports the standard Proxmox VE Helper-Scripts update mechanisms for both the application and the container operating system:

1. **Manual Application Updates**:
   Type `update` in the LXC container's console to update the application to the latest version:
   ```bash
   update
   ```

2. **Automated / Multi-Container Application Updates**:
   Use the community's `update-apps.sh` script on your **Proxmox Host** to automatically update all managed LXC containers (including Media Curator):
   ```bash
   bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/tools/pve/update-apps.sh)"
   ```

3. **Container Operating System Updates**:
   Use the PVE LXC Updater (`update-lxcs.sh`) on your **Proxmox Host** to upgrade the container operating system packages (unattended/dist-upgrade):
   ```bash
   bash -c "$(curl -fsSL https://raw.githubusercontent.com/community-scripts/ProxmoxVE/main/tools/pve/update-lxcs.sh)"
   ```

4. **Updating Private Installations from the Proxmox Host**:
   If the repository is private and was installed/cloned using `gh` (GitHub CLI), you can authenticate and run the update from your Proxmox Host:
   - **Step 1:** Authenticate the container's GitHub CLI using your host's active token:
     ```bash
     pct exec <CTID> -- bash -c "echo '\$(gh auth token)' | gh auth login --with-token"
     ```
   - **Step 2:** Link the Git credential helper to the GitHub CLI inside the container:
     ```bash
     pct exec <CTID> -- gh auth setup-git
     ```
   - **Step 3:** Trigger the update:
     ```bash
     pct exec <CTID> -- update
     ```

---

## Manual Setup (LXC or Linux)

1. **Clone & Install:**
   ```bash
   # Using git
   git clone https://github.com/ClemensSchartmueller/MediaCuratorAI.git /opt/media-curator
   
   # Or using GitHub CLI
   gh repo clone ClemensSchartmueller/MediaCuratorAI /opt/media-curator

   cd /opt/media-curator
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure:**
   Copy `.env.example` to `.env` and fill in your API keys and URLs.
   
   **Setting up Telegram Bot:**
   1. Open Telegram and search for [@BotFather](https://t.me/BotFather).
   2. Send `/newbot` and follow the instructions to create a bot. Copy the bot token provided.
   3. Search for your bot in Telegram and start a chat by clicking **Start** or sending a message.
   4. Search for [@userinfobot](https://t.me/userinfobot) and message it to find your Telegram Chat ID, or visit `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` to find the chat ID from the message you sent to your bot.
   5. Put these values in your `.env` file under `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`.

3. **Database Setup:**
   The database will be initialized on the first run.

4. **Initial Profile:**
   ```bash
   python main.py profile
   ```

5. **Deployment (LXC):**
   - Copy `deployment/media-curator.service` to `/etc/systemd/system/`.
   - Copy `deployment/media-curator-discovery.service` and `deployment/media-curator-discovery.timer` to `/etc/systemd/system/`.
   - `systemctl daemon-reload`
   - `systemctl enable --now media-curator.service`
   - `systemctl enable --now media-curator-discovery.timer`

## Scheduling
You can use the provided systemd timer (recommended for LXC) or traditional cron.
If using cron:
```cron
# Weekly discovery (Sundays at 10 AM)
0 10 * * 0 cd /opt/media-curator && ./venv/bin/python main.py discover

# Monthly profile refresh (1st of every month)
0 2 1 * * cd /opt/media-curator && ./venv/bin/python main.py profile
```

## Requirements
- Python 3.11+
- Radarr/Sonarr/Jellyfin
- TMDB API Key
- Google Gemini API Key
- Telegram Bot Token & Chat ID
