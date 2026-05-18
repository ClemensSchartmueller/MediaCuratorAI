import telebot
from src.config import Config
from src.database import Database
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.clients.tmdb import TMDBClient
from src.ai.gemini import GeminiClient
from src.ai.agent_tools import create_tools

class TelegramBot:
    def __init__(self):
        self.token = Config.TELEGRAM_BOT_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.db = Database()
        self.radarr = RadarrClient(Config.RADARR_URL, Config.RADARR_API_KEY)
        self.sonarr = SonarrClient(Config.SONARR_URL, Config.SONARR_API_KEY)
        self.tmdb = TMDBClient(Config.TMDB_API_KEY)
        self.gemini = GeminiClient()
        
        # Instantiate standalone tool list using our factory
        self.tools = create_tools(
            tmdb=self.tmdb,
            radarr=self.radarr,
            sonarr=self.sonarr,
            notify_fn=self.send_message
        )
        
        # Initialize the persistent Gemini chat session with tools
        system_instruction = (
            "You are Media Curator AI, a highly agentic media assistant. "
            "You have direct access to tools to download movies/series, get media information, "
            "recommend media by genre, and generate weekly recommendation proposals. "
            "Autonomously call the relevant tool when a user makes a request. "
            "Always be polite, helpful, and concise in your natural language replies."
        )
        self.chat = self.gemini.create_chat_session(
            tools=self.tools,
            system_instruction=system_instruction
        )
        
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
        try:
            response = self.chat.send_message(reply_text)
            return response.text
        except Exception as e:
            return f"An error occurred while communicating with Gemini: {str(e)}"

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
