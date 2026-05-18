import telebot
from src.config import Config
from src.database import Database
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.ai.gemini import GeminiClient
import json

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.db = Database()
        self.radarr = RadarrClient(Config.RADARR_URL, Config.RADARR_API_KEY)
        self.sonarr = SonarrClient(Config.SONARR_URL, Config.SONARR_API_KEY)
        self.gemini = GeminiClient()
        
        if self.token:
            self.bot = telebot.TeleBot(self.token)
        else:
            self.bot = None

    def send_message(self, text):
        if not self.bot or not self.chat_id:
            print("Telegram Bot Token or Chat ID not configured. Skipping send_message.")
            return {}
        try:
            res = self.bot.send_message(self.chat_id, text)
            # Return the message dict for mock compatibility in test suite
            return res.json if hasattr(res, "json") else {}
        except Exception as e:
            print(f"Error sending message via Telegram: {e}")
            raise

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
        if not self.bot or not self.chat_id:
            print("Telegram Bot Token or Chat ID not configured. Cannot start listen loop.")
            return

        print("Telegram listener started...")
        
        @self.bot.message_handler(func=lambda msg: str(msg.chat.id) == str(self.chat_id))
        def message_received(message):
            text = message.text
            if text:
                print(f"Received: {text}")
                response_text = self.handle_reply(text)
                try:
                    self.bot.reply_to(message, response_text)
                except Exception as e:
                    print(f"Error replying to message: {e}")

        # Starts clean polling optimized for LXC environment (low CPU/memory usage, auto-reconnects on drop)
        self.bot.infinity_polling(timeout=20, long_polling_timeout=20)
