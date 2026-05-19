import unittest
from unittest.mock import patch, MagicMock
import time
from requests.exceptions import ConnectionError, HTTPError, Timeout
from src.telegram.bot import TelegramBot
from src.ai.agent_tools import create_tools, _is_retryable_error, _parse_title_and_year
from src.clients.exceptions import MediaAlreadyExistsError


class TestTelegramBot(unittest.TestCase):
    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_handle_reply(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        # Setup mocks
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat

        mock_response = MagicMock()
        mock_response.text = "Hello! I am your assistant."
        mock_chat.send_message.return_value = mock_response

        bot = TelegramBot()
        response = bot.handle_reply("Hi")

        self.assertEqual(response, "Hello! I am your assistant.")
        mock_chat.send_message.assert_called_once_with("Hi")

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_handle_reply_error(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat
        mock_chat.send_message.side_effect = Exception("API connection lost")

        bot = TelegramBot()
        response = bot.handle_reply("Hi")

        self.assertIn("An error occurred while communicating with Gemini", response)

    @patch("src.telegram.bot.time.time")
    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_database_persistence_flow(
        self,
        mock_telebot,
        MockDB,
        MockRadarr,
        MockSonarr,
        MockTMDB,
        MockGemini,
        mock_time,
    ):
        mock_time.return_value = 12345.6 + 100.0
        mock_db = MockDB.return_value
        mock_db.get_state.side_effect = lambda k: (
            "compressed summary" if k == "compressed_context" else "12345.6"
        )
        mock_db.get_chat_history.return_value = [{"role": "user", "text": "Hi"}]

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat

        mock_response = MagicMock()
        mock_response.text = "Hello"
        mock_chat.send_message.return_value = mock_response

        # Mock get_history to return parts
        mock_item = MagicMock()
        mock_item.role = "user"
        mock_part = MagicMock()
        mock_part.text = "Hi"
        mock_item.parts = [mock_part]
        mock_chat.get_history.return_value = [mock_item]

        # Init bot
        bot = TelegramBot()

        # Assert database loading at startup
        self.assertEqual(bot.compressed_context, "compressed summary")
        self.assertEqual(bot.last_interaction_time, 12345.6)
        mock_db.get_chat_history.assert_called_once()
        mock_gemini.create_chat_session.assert_called_once_with(
            tools=bot.tools,
            system_instruction=bot.base_system_instruction
            + "\n\nHere is a summary of the past conversation history for context:\ncompressed summary",
            history=[{"role": "user", "text": "Hi"}],
        )

        # Handle a reply
        res = bot.handle_reply("How are you?")
        self.assertEqual(res, "Hello")

        # Assert database saving
        mock_db.set_state.assert_any_call(
            "last_interaction_time", str(bot.last_interaction_time)
        )
        mock_db.save_chat_history.assert_called_once()

        # Clear history action
        bot._clear_history_action()
        mock_db.set_state.assert_any_call("compressed_context", "")
        mock_db.clear_chat_history.assert_called_once()

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_clear_history_action(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat

        bot = TelegramBot()
        bot.compressed_context = "some past context"

        res = bot._clear_history_action()
        self.assertEqual(res, "Conversation history completely cleared.")
        self.assertEqual(bot.compressed_context, "")
        # Should recreate the session twice: once at __init__ and once at _clear_history_action
        self.assertEqual(mock_gemini.create_chat_session.call_count, 2)

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_compress_history_action(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat

        # Mock get_history to return some contents
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_part = MagicMock()
        mock_part.text = "Tell me a joke"
        mock_msg.parts = [mock_part]
        mock_chat.get_history.return_value = [mock_msg]

        # Mock gemini.generate_content for summarization
        mock_summary_resp = MagicMock()
        mock_summary_resp.text = "Summary: requested jokes"
        mock_gemini.generate_content.return_value = mock_summary_resp

        bot = TelegramBot()
        res = bot._compress_history_action()

        self.assertEqual(res, "Summary: requested jokes")
        self.assertEqual(bot.compressed_context, "Summary: requested jokes")
        mock_gemini.generate_content.assert_called_once()

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_compress_history_action_error_does_not_overwrite_state(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.side_effect = lambda k: (
            "existing summary" if k == "compressed_context" else None
        )
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat
        mock_msg = MagicMock()
        mock_msg.role = "user"
        mock_part = MagicMock()
        mock_part.text = "Tell me a joke"
        mock_msg.parts = [mock_part]
        mock_chat.get_history.return_value = [mock_msg]
        mock_gemini.generate_content.side_effect = Exception("summary failure")

        bot = TelegramBot()
        res = bot._compress_history_action()

        self.assertIn("Failed to generate summary", res)
        self.assertEqual(bot.compressed_context, "existing summary")
        mock_db.set_state.assert_not_called()
        mock_db.clear_chat_history.assert_not_called()

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_automatic_24h_compression(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat

        bot = TelegramBot()
        bot.last_interaction_time = time.time() - 90000  # 25 hours ago

        # Mock format history to return non-empty so compression triggers
        bot._format_history_for_summary = MagicMock(return_value="User: Hello")
        bot._compress_history_action = MagicMock(return_value="Summary")
        bot.send_message = MagicMock()

        bot.handle_reply("New message")

        bot._compress_history_action.assert_called_once()
        bot.send_message.assert_called_with(
            "📦 Automatic 24-hour history compression triggered."
        )

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_record_interaction_persists_timestamp(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []
        mock_gemini = MockGemini.return_value
        mock_gemini.create_chat_session.return_value = MagicMock()

        bot = TelegramBot()
        bot._record_interaction(42.5)

        self.assertEqual(bot.last_interaction_time, 42.5)
        mock_db.set_state.assert_any_call("last_interaction_time", "42.5")

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_send_message_success_html(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        bot = TelegramBot()
        bot.bot = MagicMock()
        bot.chat_id = "12345"

        bot.send_message("Hello **world**")

        bot.bot.send_message.assert_called_once_with(
            "12345", "Hello <b>world</b>", parse_mode="HTML"
        )

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_send_message_fallback_plain(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        bot = TelegramBot()
        bot.bot = MagicMock()
        bot.chat_id = "12345"

        # Raise exception on HTML call, return success on plain call
        bot.bot.send_message.side_effect = [Exception("HTML parse error"), MagicMock()]

        bot.send_message("Hello **world**")

        # Should have called it twice: first with HTML mode, then with raw text
        self.assertEqual(bot.bot.send_message.call_count, 2)
        bot.bot.send_message.assert_any_call(
            "12345", "Hello <b>world</b>", parse_mode="HTML"
        )
        bot.bot.send_message.assert_any_call("12345", "Hello **world**")

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_send_reply_success_html(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        bot = TelegramBot()
        bot.bot = MagicMock()
        mock_msg = MagicMock()

        bot.send_reply(mock_msg, "Hello *world*")

        bot.bot.reply_to.assert_called_once_with(
            mock_msg, "Hello <i>world</i>", parse_mode="HTML"
        )

    @patch("src.telegram.bot.GeminiClient")
    @patch("src.telegram.bot.TMDBClient")
    @patch("src.telegram.bot.SonarrClient")
    @patch("src.telegram.bot.RadarrClient")
    @patch("src.telegram.bot.Database")
    @patch("src.telegram.bot.telebot")
    def test_send_reply_fallback_plain(
        self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini
    ):
        mock_db = MockDB.return_value
        mock_db.get_state.return_value = None
        mock_db.get_chat_history.return_value = []

        bot = TelegramBot()
        bot.bot = MagicMock()
        mock_msg = MagicMock()

        # Raise exception on HTML call, return success on plain call
        bot.bot.reply_to.side_effect = [Exception("HTML parse error"), MagicMock()]

        bot.send_reply(mock_msg, "Hello *world*")

        # Should have called it twice: first with HTML mode, then with raw text
        self.assertEqual(bot.bot.reply_to.call_count, 2)
        bot.bot.reply_to.assert_any_call(
            mock_msg, "Hello <i>world</i>", parse_mode="HTML"
        )
        bot.bot.reply_to.assert_any_call(mock_msg, "Hello *world*")


class TestAgentTools(unittest.TestCase):
    def setUp(self):
        self.mock_tmdb = MagicMock()
        self.mock_radarr = MagicMock()
        self.mock_sonarr = MagicMock()
        self.mock_bot = MagicMock()

        self.tools = create_tools(
            self.mock_tmdb, self.mock_radarr, self.mock_sonarr, self.mock_bot
        )
        self.tools_dict = {t.__name__: t for t in self.tools}

    def test_add_movie_success(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "movie", "id": 123, "title": "Dune"}]
        }

        res = add_movie("Dune")
        self.assertIn("Successfully added movie 'Dune' to your Radarr library", res)
        self.mock_radarr.add_movie.assert_called_once_with(
            123, unittest.mock.ANY, unittest.mock.ANY
        )

    def test_add_movie_not_found(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.return_value = {"results": []}

        res = add_movie("Nonexistent")
        self.assertIn("Could not find any movie matching", res)
        self.mock_radarr.add_movie.assert_not_called()

    def test_add_movie_duplicate(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "movie", "id": 123, "title": "Dune"}]
        }
        self.mock_radarr.add_movie.side_effect = MediaAlreadyExistsError(
            "movie", "Dune", "Radarr"
        )

        res = add_movie("Dune")
        self.assertEqual(
            "The movie 'Dune' is already in your Radarr library!",
            res,
        )

    def test_add_movie_ambiguous_requires_clarification(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [
                {
                    "media_type": "movie",
                    "id": 1,
                    "title": "Dune",
                    "release_date": "1984-12-14",
                },
                {
                    "media_type": "movie",
                    "id": 2,
                    "title": "Dune",
                    "release_date": "2021-10-22",
                },
            ]
        }

        res = add_movie("Dune")
        self.assertIn("Multiple movie matches found", res)
        self.mock_radarr.add_movie.assert_not_called()

    @patch("time.sleep", return_value=None)
    def test_retry_logic_failure_then_success(self, mock_sleep):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.side_effect = [
            Timeout("Temporary Timeout"),
            {"results": [{"media_type": "movie", "id": 123, "title": "Dune"}]},
        ]

        res = add_movie("Dune")
        self.assertIn("Successfully added movie 'Dune'", res)
        self.mock_bot.send_message.assert_any_call(
            "⚠️ Transient API/network error during adding movie 'Dune'. Retrying in 2s... (Attempt 1/3)"
        )

    @patch("time.sleep", return_value=None)
    def test_retry_logic_exhaustion(self, mock_sleep):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.side_effect = Timeout("Persistent Timeout")

        res = add_movie("Dune")
        self.assertIn("Failed to execute adding movie 'Dune' after 3 attempts", res)
        self.mock_bot.send_message.assert_any_call(
            "❌ Failed to execute adding movie 'Dune' after 3 attempts. Error: Persistent Timeout"
        )

    def test_retry_logic_non_retryable_error(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.side_effect = TypeError("Bad input")

        res = add_movie("Dune")
        self.assertIn("Failed to execute adding movie 'Dune'. Error: Bad input", res)
        self.assertEqual(self.mock_tmdb.search_multi.call_count, 1)
        self.mock_bot.send_message.assert_any_call(
            "❌ Failed to execute adding movie 'Dune'. Error: Bad input"
        )

    def test_is_retryable_error_classification(self):
        self.assertTrue(_is_retryable_error(Timeout("timeout")))
        self.assertTrue(_is_retryable_error(ConnectionError("connection")))

        http_429 = HTTPError("429")
        http_429.response = MagicMock(status_code=429)
        self.assertTrue(_is_retryable_error(http_429))

        http_503 = HTTPError("503")
        http_503.response = MagicMock(status_code=503)
        self.assertTrue(_is_retryable_error(http_503))

        http_400 = HTTPError("400")
        http_400.response = MagicMock(status_code=400)
        self.assertFalse(_is_retryable_error(http_400))

        self.assertFalse(_is_retryable_error(TypeError("bad input")))

    def test_add_series_success(self):
        add_series = self.tools_dict["add_series_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "tv", "id": 456, "name": "Breaking Bad"}]
        }

        res = add_series("Breaking Bad")
        self.assertIn(
            "Successfully added series 'Breaking Bad' to your Sonarr library", res
        )
        self.mock_sonarr.add_series.assert_called_once_with(
            456, unittest.mock.ANY, unittest.mock.ANY
        )

    def test_add_series_ambiguous_requires_clarification(self):
        add_series = self.tools_dict["add_series_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [
                {
                    "media_type": "tv",
                    "id": 10,
                    "name": "Shogun",
                    "first_air_date": "1980-09-15",
                },
                {
                    "media_type": "tv",
                    "id": 11,
                    "name": "Shogun",
                    "first_air_date": "2024-02-27",
                },
            ]
        }

        res = add_series("Shogun")
        self.assertIn("Multiple TV series matches found", res)
        self.mock_sonarr.add_series.assert_not_called()

    def test_add_series_duplicate(self):
        add_series = self.tools_dict["add_series_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "tv", "id": 456, "name": "Breaking Bad"}]
        }
        self.mock_sonarr.add_series.side_effect = MediaAlreadyExistsError(
            "series", "Breaking Bad", "Sonarr"
        )

        res = add_series("Breaking Bad")
        self.assertEqual(
            "The series 'Breaking Bad' is already in your Sonarr library!",
            res,
        )

    def test_get_media_information_movie(self):
        get_info = self.tools_dict["get_media_information"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "movie", "id": 123}]
        }
        self.mock_tmdb.get_movie_details.return_value = {
            "title": "Dune",
            "release_date": "2021-10-22",
            "vote_average": 8.1,
            "overview": "A noble family...",
        }

        res = get_info("Dune")
        self.assertIn("🎬 **Dune** (2021)", res)
        self.assertIn("⭐ Rating: 8.1/10", res)
        self.assertIn("Plot: A noble family...", res)

    def test_discover_by_genre(self):
        discover = self.tools_dict["discover_by_genre"]
        self.mock_tmdb.get_genres.return_value = {
            "genres": [{"name": "Action", "id": 28}]
        }
        self.mock_tmdb.discover_by_genre.return_value = {
            "results": [
                {"title": "Action Movie", "vote_average": 7.5, "overview": "Boom!"}
            ]
        }

        res = discover("Action", "movie")
        self.assertIn("Top 5 popular movies in genre 'Action'", res)
        self.assertIn("Action Movie", res)
        self.assertIn("_Boom!_", res)

    def test_discover_by_genre_empty_overview(self):
        discover = self.tools_dict["discover_by_genre"]
        self.mock_tmdb.get_genres.return_value = {
            "genres": [{"name": "Action", "id": 28}]
        }
        self.mock_tmdb.discover_by_genre.return_value = {
            "results": [{"title": "Action Movie", "vote_average": 7.5, "overview": ""}]
        }

        res = discover("Action", "movie")
        self.assertIn("_No overview available._", res)

    @patch("src.ai.agent_tools.Profiler")
    @patch("src.ai.agent_tools.DiscoveryPipeline")
    @patch("src.ai.agent_tools.Database")
    def test_generate_new_proposals(self, MockDB, MockPipeline, MockProfiler):
        generate = self.tools_dict["generate_new_proposals"]
        mock_profiler = MockProfiler.return_value
        mock_pipeline = MockPipeline.return_value
        mock_db = MockDB.return_value

        mock_pipeline.run_weekly_discovery.return_value = (
            [
                {
                    "position": 1,
                    "media_type": "movie",
                    "title": "Rec Movie",
                    "justification": "Fits taste",
                }
            ],
            "raw_curation",
        )

        res = generate()
        self.assertIn("Fresh Media Recommendations Generated", res)
        self.assertIn("1. 🎥 Rec Movie", res)
        mock_profiler.run.assert_called_once()
        mock_pipeline.run_weekly_discovery.assert_called_once()
        mock_db.set_active_recommendations.assert_called_once()

    def test_clear_chat_history_tool(self):
        clear_history = self.tools_dict["clear_chat_history"]
        self.mock_bot._clear_history_action.return_value = "Cleared"

        res = clear_history()
        self.assertEqual(res, "Cleared")
        self.mock_bot._clear_history_action.assert_called_once()

    def test_compress_chat_history_tool(self):
        compress_history = self.tools_dict["compress_chat_history"]
        self.mock_bot._compress_history_action.return_value = "Compressed"

        res = compress_history()
        self.assertEqual(res, "Compressed")
        self.mock_bot._compress_history_action.assert_called_once()


class TestParseTitleAndYear(unittest.TestCase):
    def test_title_with_year(self):
        clean, year = _parse_title_and_year("Dune (2021)")
        self.assertEqual(clean, "Dune")
        self.assertEqual(year, 2021)

    def test_title_without_year(self):
        clean, year = _parse_title_and_year("Dune")
        self.assertEqual(clean, "Dune")
        self.assertIsNone(year)

    def test_title_with_year_and_extra_spaces(self):
        clean, year = _parse_title_and_year("  Blade Runner 2049  (1996)  ")
        self.assertEqual(clean, "Blade Runner 2049")
        self.assertEqual(year, 1996)

    def test_title_year_not_at_end_is_ignored(self):
        """A year in the middle of the title should not be extracted."""
        clean, year = _parse_title_and_year("2001: A Space Odyssey")
        self.assertEqual(clean, "2001: A Space Odyssey")
        self.assertIsNone(year)


class TestYearAwareSearch(unittest.TestCase):
    def setUp(self):
        self.mock_tmdb = MagicMock()
        self.mock_radarr = MagicMock()
        self.mock_sonarr = MagicMock()
        self.mock_bot = MagicMock()

        self.tools = create_tools(
            self.mock_tmdb, self.mock_radarr, self.mock_sonarr, self.mock_bot
        )
        self.tools_dict = {t.__name__: t for t in self.tools}

    def test_add_movie_with_year_uses_search_movie(self):
        """When a year is provided, search_movie is called instead of search_multi."""
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_movie.return_value = {
            "results": [{"id": 10, "title": "Sabrina", "release_date": "1996-01-01"}]
        }

        res = add_movie("Sabrina (1996)")
        self.assertIn("Successfully added movie 'Sabrina'", res)
        self.mock_tmdb.search_movie.assert_called_once_with("Sabrina", year=1996)
        self.mock_tmdb.search_multi.assert_not_called()

    def test_add_movie_without_year_uses_search_multi(self):
        """Without a year, the original search_multi path is used."""
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "movie", "id": 10, "title": "Sabrina"}]
        }

        res = add_movie("Sabrina")
        self.assertIn("Successfully added movie 'Sabrina'", res)
        self.mock_tmdb.search_multi.assert_called_once_with("Sabrina")
        self.mock_tmdb.search_movie.assert_not_called()

    def test_add_series_with_year_uses_search_tv(self):
        """When a year is provided, search_tv is called instead of search_multi."""
        add_series = self.tools_dict["add_series_to_library"]
        self.mock_tmdb.search_tv.return_value = {
            "results": [{"id": 20, "name": "Shogun", "first_air_date": "1980-09-15"}]
        }

        res = add_series("Shogun (1980)")
        self.assertIn("Successfully added series 'Shogun'", res)
        self.mock_tmdb.search_tv.assert_called_once_with("Shogun", year=1980)
        self.mock_tmdb.search_multi.assert_not_called()

    def test_add_series_without_year_uses_search_multi(self):
        """Without a year, the original search_multi path is used."""
        add_series = self.tools_dict["add_series_to_library"]
        self.mock_tmdb.search_multi.return_value = {
            "results": [{"media_type": "tv", "id": 20, "name": "Shogun"}]
        }

        res = add_series("Shogun")
        self.assertIn("Successfully added series 'Shogun'", res)
        self.mock_tmdb.search_multi.assert_called_once_with("Shogun")
        self.mock_tmdb.search_tv.assert_not_called()

    def test_add_movie_with_year_not_found(self):
        add_movie = self.tools_dict["add_movie_to_library"]
        self.mock_tmdb.search_movie.return_value = {"results": []}

        res = add_movie("Ghost (2026)")
        self.assertIn("Could not find any movie matching 'Ghost (2026)'", res)
        self.mock_radarr.add_movie.assert_not_called()


if __name__ == "__main__":
    unittest.main()
