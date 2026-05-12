import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    JELLYFIN_URL = os.getenv("JELLYFIN_URL")
    JELLYFIN_API_KEY = os.getenv("JELLYFIN_API_KEY")
    JELLYFIN_USER_ID = os.getenv("JELLYFIN_USER_ID")

    SONARR_URL = os.getenv("SONARR_URL")
    SONARR_API_KEY = os.getenv("SONARR_API_KEY")

    RADARR_URL = os.getenv("RADARR_URL")
    RADARR_API_KEY = os.getenv("RADARR_API_KEY")

    TMDB_API_KEY = os.getenv("TMDB_API_KEY")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

    SIGNAL_URL = os.getenv("SIGNAL_URL")
    SIGNAL_NUMBER = os.getenv("SIGNAL_NUMBER")
    SIGNAL_RECIPIENT = os.getenv("SIGNAL_RECIPIENT")

    RADARR_ROOT_FOLDER = os.getenv("RADARR_ROOT_FOLDER", "/data/media/movies")
    RADARR_QUALITY_PROFILE = int(os.getenv("RADARR_QUALITY_PROFILE", "1"))

    SONARR_ROOT_FOLDER = os.getenv("SONARR_ROOT_FOLDER", "/data/media/tv")
    SONARR_QUALITY_PROFILE = int(os.getenv("SONARR_QUALITY_PROFILE", "1"))

    DB_PATH = "media_curator.db"
