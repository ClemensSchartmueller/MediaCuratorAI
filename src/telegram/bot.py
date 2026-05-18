import requests
from src.config import Config
from src.database import Database
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.ai.gemini import GeminiClient
import time
import json

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.offset = None
        self.db = Database()
        self.radarr = RadarrClient(Config.RADARR_URL, Config.RADARR_API_KEY)
        self.sonarr = SonarrClient(Config.SONARR_URL, Config.SONARR_API_KEY)
        self.gemini = GeminiClient()

    def send_message(self, text):
        if not self.token or not self.chat_id:
            print("Telegram Bot Token or Chat ID not configured. Skipping send_message.")
            return {}
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        return response.json()

    def receive_messages(self):
        if not self.token:
            print("Telegram Bot Token not configured. Skipping receive_messages.")
            return []
        url = f"https://api.telegram.org/bot{self.token}/getUpdates"
        params = {}
        if self.offset:
            params["offset"] = self.offset
        try:
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
        except Exception as e:
            print(f"Error fetching updates from Telegram: {e}")
        return []

    def handle_reply(self, reply_text):
        # 1. Use Gemini to interpret intent and map to active recommendations
        active_recs = self.db.get_recommendation_by_position(1) # Just checking if we have any
        if not active_recs:
            return "No active recommendations to act on."

        prompt = f"""
        The user said: "{reply_text}"
        
        Currently active recommendations:
        {self._get_active_recs_summary()}
        
        Identify which item(s) the user wants to add or download. 
        Return a JSON list of objects with 'tmdb_id', 'title', and 'type' (movie/tv).
        If they don't want to add anything, return an empty list [].
        """
        
        # Use simple flash model for quick interpretation
        intent_response = self.gemini.generate_content(prompt).text.strip()
        # Clean up JSON if LLM added backticks
        json_str = intent_response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0].strip()
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0].strip()
        
        try:
            items_to_add = json.loads(json_str)
            results = []
            for item in items_to_add:
                if item['type'] == 'movie':
                    res = self.radarr.add_movie(
                        item['tmdb_id'], 
                        Config.RADARR_ROOT_FOLDER, 
                        Config.RADARR_QUALITY_PROFILE
                    )
                    results.append(f"Added Movie: {item['title']}")
                elif item['type'] == 'tv':
                    res = self.sonarr.add_series(
                        item['tmdb_id'], 
                        Config.SONARR_ROOT_FOLDER, 
                        Config.SONARR_QUALITY_PROFILE
                    )
                    results.append(f"Added Series: {item['title']}")
            
            if results:
                return "\n".join(results)
            else:
                if isinstance(items_to_add, list) and len(items_to_add) == 0:
                    return "No recommended items were added to your library."
                return "I couldn't figure out which item you meant. Could you be more specific?"
        except Exception as e:
            return f"Error processing request: {str(e)}"

    def _get_active_recs_summary(self):
        # Fetch all active recs from DB and format
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT position, title, tmdb_id, media_type FROM active_recommendations")
            rows = cursor.fetchall()
            return "\n".join([f"{r[0]}. {r[1]} (TMDB: {r[2]}, Type: {r[3]})" for r in rows])

    def listen_loop(self):
        print("Telegram listener started...")
        while True:
            try:
                updates = self.receive_messages()
                for update in updates:
                    update_id = update.get("update_id")
                    self.offset = update_id + 1
                    
                    message = update.get("message", {})
                    chat = message.get("chat", {})
                    chat_id = chat.get("id")
                    text = message.get("text")
                    
                    if str(chat_id) == str(self.chat_id) and text:
                        print(f"Received: {text}")
                        response_text = self.handle_reply(text)
                        self.send_message(response_text)
            except Exception as e:
                print(f"Error in listen loop: {e}")
            time.sleep(5) # Poll every 5 seconds
