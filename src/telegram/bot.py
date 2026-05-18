import telebot
import time
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
        
        self.last_interaction_time = 0.0
        self.compressed_context = ""
        self.base_system_instruction = (
            "You are Media Curator AI, a highly agentic media assistant. "
            "You have direct access to tools to download movies/series, get media information, "
            "recommend media by genre, and generate weekly recommendation proposals. "
            "Autonomously call the relevant tool when a user makes a request. "
            "Always be polite, helpful, and concise in your natural language replies."
        )
        
        # Instantiate standalone tool list using our factory
        self.tools = create_tools(
            tmdb=self.tmdb,
            radarr=self.radarr,
            sonarr=self.sonarr,
            bot_instance=self
        )
        
        self._recreate_chat_session()
        
        if self.token:
            self.bot = telebot.TeleBot(self.token)
        else:
            self.bot = None

    def _recreate_chat_session(self):
        instruction = self.base_system_instruction
        if self.compressed_context:
            instruction += f"\n\nHere is a summary of the past conversation history for context:\n{self.compressed_context}"
        
        self.chat = self.gemini.create_chat_session(
            tools=self.tools,
            system_instruction=instruction
        )

    def _format_history_for_summary(self):
        try:
            history = self.chat.get_history()
        except Exception:
            return ""
        
        lines = []
        for item in history:
            role = getattr(item, 'role', 'unknown')
            for part in getattr(item, 'parts', []):
                text = getattr(part, 'text', None)
                if text:
                    lines.append(f"{role.capitalize()}: {text}")
                elif getattr(part, 'function_call', None):
                    lines.append(f"{role.capitalize()} called tool: {part.function_call.name}")
                elif getattr(part, 'function_response', None):
                    lines.append(f"Tool returned: {part.function_response.response}")
        return "\n".join(lines)

    def _compress_history_action(self) -> str:
        history_text = self._format_history_for_summary()
        if not history_text.strip():
            return "No conversation history to compress."

        prompt = f"""
        Summarize the following conversation history between the user and the AI assistant, 
        capturing the key context, active user requests, preferences, and state. 
        Keep it extremely concise (under 200 words).
        
        History:
        {history_text}
        """
        try:
            response = self.gemini.generate_content(prompt)
            summary = response.text.strip()
        except Exception as e:
            summary = f"Failed to generate summary: {str(e)}"
        
        self.compressed_context = summary
        self._recreate_chat_session()
        return summary

    def _clear_history_action(self) -> str:
        self.compressed_context = ""
        self._recreate_chat_session()
        return "Conversation history completely cleared."

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
        # Check automatic 24-hour compression
        now = time.time()
        if self.last_interaction_time > 0 and (now - self.last_interaction_time) > 86400:
            history_text = self._format_history_for_summary()
            if history_text.strip():
                try:
                    self.send_message("📦 Automatic 24-hour history compression triggered.")
                except Exception:
                    pass
                self._compress_history_action()
        
        self.last_interaction_time = now

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
                
                cleaned_text = text.strip()
                if cleaned_text == "/clear":
                    self._clear_history_action()
                    try:
                        self.bot.reply_to(message, "🧹 Chat history completely cleared and reset.")
                    except Exception as e:
                        print(f"Error replying: {e}")
                    return
                elif cleaned_text == "/compress":
                    summary = self._compress_history_action()
                    reply_msg = f"📦 Chat history compressed successfully!\n\n**Context Summary:**\n{summary}"
                    try:
                        self.bot.reply_to(message, reply_msg)
                    except Exception as e:
                        print(f"Error replying: {e}")
                    return
                
                response_text = self.handle_reply(text)
                try:
                    self.bot.reply_to(message, response_text)
                except Exception as e:
                    print(f"Error replying to message: {e}")

        # Starts clean polling optimized for LXC environment (low CPU/memory usage, auto-reconnects on drop)
        self.bot.infinity_polling(timeout=20, long_polling_timeout=20)
