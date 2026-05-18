import unittest
from unittest.mock import patch, MagicMock
from src.telegram.bot import TelegramBot
from src.ai.agent_tools import create_tools

class TestTelegramBot(unittest.TestCase):
    @patch('src.telegram.bot.GeminiClient')
    @patch('src.telegram.bot.TMDBClient')
    @patch('src.telegram.bot.SonarrClient')
    @patch('src.telegram.bot.RadarrClient')
    @patch('src.telegram.bot.Database')
    @patch('src.telegram.bot.telebot')
    def test_handle_reply(self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini):
        # Setup mocks
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

    @patch('src.telegram.bot.GeminiClient')
    @patch('src.telegram.bot.TMDBClient')
    @patch('src.telegram.bot.SonarrClient')
    @patch('src.telegram.bot.RadarrClient')
    @patch('src.telegram.bot.Database')
    @patch('src.telegram.bot.telebot')
    def test_handle_reply_error(self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockTMDB, MockGemini):
        mock_gemini = MockGemini.return_value
        mock_chat = MagicMock()
        mock_gemini.create_chat_session.return_value = mock_chat
        mock_chat.send_message.side_effect = Exception("API connection lost")
        
        bot = TelegramBot()
        response = bot.handle_reply("Hi")
        
        self.assertIn("An error occurred while communicating with Gemini", response)


class TestAgentTools(unittest.TestCase):
    def setUp(self):
        self.mock_tmdb = MagicMock()
        self.mock_radarr = MagicMock()
        self.mock_sonarr = MagicMock()
        self.mock_notify = MagicMock()
        self.tools = create_tools(
            self.mock_tmdb,
            self.mock_radarr,
            self.mock_sonarr,
            self.mock_notify
        )
        # Find tools by name
        self.tools_dict = {t.__name__: t for t in self.tools}

    def test_add_movie_success(self):
        add_movie = self.tools_dict['add_movie_to_library']
        self.mock_tmdb.search_multi.return_value = {
            'results': [{'media_type': 'movie', 'id': 123, 'title': 'Dune'}]
        }
        
        res = add_movie("Dune")
        self.assertIn("Successfully added movie 'Dune' to your Radarr library", res)
        self.mock_radarr.add_movie.assert_called_once_with(123, unittest.mock.ANY, unittest.mock.ANY)

    def test_add_movie_not_found(self):
        add_movie = self.tools_dict['add_movie_to_library']
        self.mock_tmdb.search_multi.return_value = {'results': []}
        
        res = add_movie("Nonexistent")
        self.assertIn("Could not find any movie matching", res)
        self.mock_radarr.add_movie.assert_not_called()

    @patch('time.sleep', return_value=None) # avoid delay in tests
    def test_retry_logic_failure_then_success(self, mock_sleep):
        add_movie = self.tools_dict['add_movie_to_library']
        # Fail first, succeed second
        self.mock_tmdb.search_multi.side_effect = [Exception("Temporary Timeout"), {
            'results': [{'media_type': 'movie', 'id': 123, 'title': 'Dune'}]
        }]
        
        res = add_movie("Dune")
        self.assertIn("Successfully added movie 'Dune'", res)
        self.mock_notify.assert_any_call("⚠️ Rate limit or API error during adding movie 'Dune'. Retrying in 2s... (Attempt 1/3)")

    @patch('time.sleep', return_value=None)
    def test_retry_logic_exhaustion(self, mock_sleep):
        add_movie = self.tools_dict['add_movie_to_library']
        self.mock_tmdb.search_multi.side_effect = Exception("Persistent Timeout")
        
        res = add_movie("Dune")
        self.assertIn("Failed to execute adding movie 'Dune' after 3 attempts", res)
        self.mock_notify.assert_any_call("❌ Failed to execute adding movie 'Dune' after 3 attempts. Error: Persistent Timeout")

    def test_add_series_success(self):
        add_series = self.tools_dict['add_series_to_library']
        self.mock_tmdb.search_multi.return_value = {
            'results': [{'media_type': 'tv', 'id': 456, 'name': 'Breaking Bad'}]
        }
        
        res = add_series("Breaking Bad")
        self.assertIn("Successfully added series 'Breaking Bad' to your Sonarr library", res)
        self.mock_sonarr.add_series.assert_called_once_with(456, unittest.mock.ANY, unittest.mock.ANY)

    def test_get_media_information_movie(self):
        get_info = self.tools_dict['get_media_information']
        self.mock_tmdb.search_multi.return_value = {
            'results': [{'media_type': 'movie', 'id': 123}]
        }
        self.mock_tmdb.get_movie_details.return_value = {
            'title': 'Dune', 'release_date': '2021-10-22', 'vote_average': 8.1, 'overview': 'A noble family...'
        }
        
        res = get_info("Dune")
        self.assertIn("🎬 **Dune** (2021)", res)
        self.assertIn("⭐ Rating: 8.1/10", res)
        self.assertIn("Plot: A noble family...", res)

    def test_discover_by_genre(self):
        discover = self.tools_dict['discover_by_genre']
        self.mock_tmdb.get_genres.return_value = {
            'genres': [{'name': 'Action', 'id': 28}]
        }
        self.mock_tmdb.discover_by_genre.return_value = {
            'results': [{'title': 'Action Movie', 'vote_average': 7.5, 'overview': 'Boom!'}]
        }
        
        res = discover("Action", "movie")
        self.assertIn("Top 5 popular movies in genre 'Action'", res)
        self.assertIn("Action Movie", res)

    @patch('src.ai.agent_tools.Profiler')
    @patch('src.ai.agent_tools.DiscoveryPipeline')
    @patch('src.ai.agent_tools.Database')
    def test_generate_new_proposals(self, MockDB, MockPipeline, MockProfiler):
        generate = self.tools_dict['generate_new_proposals']
        mock_profiler = MockProfiler.return_value
        mock_pipeline = MockPipeline.return_value
        mock_db = MockDB.return_value
        
        mock_pipeline.run_weekly_discovery.return_value = (
            [{'position': 1, 'media_type': 'movie', 'title': 'Rec Movie', 'justification': 'Fits taste'}],
            "raw_curation"
        )
        
        res = generate()
        self.assertIn("Fresh Media Recommendations Generated", res)
        self.assertIn("1. 🎥 Rec Movie", res)
        mock_profiler.run.assert_called_once()
        mock_pipeline.run_weekly_discovery.assert_called_once()
        mock_db.set_active_recommendations.assert_called_once()

if __name__ == '__main__':
    unittest.main()
