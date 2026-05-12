import requests
from src.config import Config
from src.database import Database
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.ai.gemini import GeminiClient
import time
import json

class SignalBot:
    def __init__(self):
        self.url = Config.SIGNAL_URL.rstrip("/")
        self.number = Config.SIGNAL_NUMBER
        self.recipient = Config.SIGNAL_RECIPIENT
        self.db = Database()
        self.radarr = RadarrClient(Config.RADARR_URL, Config.RADARR_API_KEY)
        self.sonarr = SonarrClient(Config.SONARR_URL, Config.SONARR_API_KEY)
        self.gemini = GeminiClient()

    def send_message(self, text):
        payload = {
            "message": text,
            "number": self.number,
            "recipients": [self.recipient]
        }
        response = requests.post(f"{self.url}/v2/send", json=payload)
        response.raise_for_status()
        return response.json()

    def receive_messages(self):
        # Long polling or frequent polling of the receive endpoint
        response = requests.get(f"{self.url}/v1/receive/{self.number}")
        if response.status_code == 200:
            return response.json()
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
        if "```json" in intent_response:
            intent_response = intent_response.split("```json")[1].split("```")[0].strip()
        
        try:
            items_to_add = json.loads(intent_response)
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
        print("Signal listener started...")
        while True:
            try:
                messages = self.receive_messages()
                for msg in messages:
                    # Filter for messages from our recipient
                    envelope = msg.get('envelope', {})
                    source = envelope.get('source')
                    data_msg = envelope.get('dataMessage', {})
                    text = data_msg.get('message')
                    
                    if source == self.recipient and text:
                        print(f"Received: {text}")
                        response_text = self.handle_reply(text)
                        self.send_message(response_text)
            except Exception as e:
                print(f"Error in listen loop: {e}")
            time.sleep(5) # Poll every 5 seconds
