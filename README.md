# Media Curator AI

AI-driven media recommendation daemon for self-hosted stacks.

## Features
- **Taste Profiler:** Analyzes Jellyfin history to understand what you like.
- **Hybrid Discovery:** Finds new VOD/Digital releases on TMDB and filters against your existing library.
- **AI Curation:** Uses Google Gemini with Google Search grounding to pick the best releases based on your profile.
- **Telegram Integration:** Weekly recommendations sent via Telegram; supports natural language replies to add media to Radarr/Sonarr.

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
