from src.clients.jellyfin import JellyfinClient
from src.ai.gemini import GeminiClient
from src.database import Database
from src.config import Config


class Profiler:
    def __init__(self):
        self.jellyfin = JellyfinClient(
            Config.JELLYFIN_URL, Config.JELLYFIN_API_KEY, Config.JELLYFIN_USER_ID
        )
        self.gemini = GeminiClient()
        self.db = Database()

    def run(self):
        # 1. Fetch watch history
        history = self.jellyfin.get_watch_history()
        items = history.get("Items", [])

        # 2. Summarize (chunked if necessary, but we'll try to be efficient)
        summary_data = []
        for item in items:
            summary_data.append(
                f"Title: {item.get('Name')}, Genres: {item.get('Genres', [])}, Overview: {item.get('Overview', '')[:100]}"
            )

        # Limit to last 50 items for token efficiency
        watch_history_text = "\n".join(summary_data[:50])

        # 3. Generate Profile
        profile = self.gemini.generate_taste_profile(watch_history_text)

        # 4. Save to DB
        self.db.save_taste_profile(profile)
        return profile
