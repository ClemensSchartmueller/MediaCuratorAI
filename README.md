# Media Curator AI

AI-driven media recommendation daemon for self-hosted stacks.

## Features
- **Taste Profiler:** Analyzes Jellyfin history to understand what you like.
- **Hybrid Discovery:** Finds new VOD/Digital releases on TMDB and filters against your existing library.
- **AI Curation:** Uses Google Gemini with Google Search grounding to pick the best releases based on your profile.
- **Signal Integration:** Weekly recommendations sent via Signal; supports natural language replies to add media to Radarr/Sonarr.

## Proxmox LXC Installation

If you are running Proxmox VE, you can use the automated installer. Run this command on your **Proxmox host**:

```bash
# Using wget
bash -c "$(wget -qLO - https://raw.githubusercontent.com/ClemensSchartmueller/MediaCuratorAI/main/proxmox/lxc_install.sh)"

# Or using GitHub CLI
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
- [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) running
