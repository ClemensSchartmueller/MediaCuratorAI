# Media Curator AI

AI-driven media recommendation daemon for self-hosted stacks.

## Features
- **Taste Profiler:** Analyzes Jellyfin history to understand what you like.
- **Hybrid Discovery:** Finds new VOD/Digital releases on TMDB and filters against your existing library.
- **AI Curation:** Uses Google Gemini with Google Search grounding to pick the best releases based on your profile.
- **Signal Integration:** Weekly recommendations sent via Signal; supports natural language replies to add media to Radarr/Sonarr.

## Setup

1. **Clone & Install:**
   ```bash
   git clone <repo-url> /opt/media_curator
   cd /opt/media_curator
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
   - `systemctl enable --now media-curator.service`

6. **Scheduling:**
   Add the following to your crontab (`crontab -e`):
   ```cron
   # Weekly discovery (Sundays at 10 AM)
   0 10 * * 0 cd /opt/media_curator && ./venv/bin/python main.py discover

   # Monthly profile refresh (1st of every month)
   0 2 1 * * cd /opt/media_curator && ./venv/bin/python main.py profile
   ```

## Requirements
- Python 3.11+
- Radarr/Sonarr/Jellyfin
- TMDB API Key
- Google Gemini API Key
- [signal-cli-rest-api](https://github.com/bbernhard/signal-cli-rest-api) running
