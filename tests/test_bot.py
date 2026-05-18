import unittest
from unittest.mock import patch, MagicMock
from src.telegram.bot import TelegramBot

class TestTelegramBot(unittest.TestCase):
    @patch('src.telegram.bot.GeminiClient')
    @patch('src.telegram.bot.SonarrClient')
    @patch('src.telegram.bot.RadarrClient')
    @patch('src.telegram.bot.Database')
    @patch('src.telegram.bot.telebot')
    def test_handle_reply_movie(self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockGemini):
        mock_db = MockDB.return_value
        mock_db.get_recommendation_by_position.return_value = {"id": 1}
        
        # Test the bot handling a reply
        mock_gemini_instance = MockGemini.return_value
        mock_model_response = MagicMock()
        mock_model_response.text = '[{"tmdb_id": 4, "title": "New Movie", "type": "movie"}]'
        mock_gemini_instance.generate_content.return_value = mock_model_response
        
        mock_radarr_instance = MockRadarr.return_value
        
        bot = TelegramBot()
        bot.token = "mock-token"
        bot.chat_id = "12345"
        
        # Mock summary to avoid DB fetch error inside _get_active_recs_summary
        bot._get_active_recs_summary = MagicMock(return_value="1. New Movie (TMDB: 4, Type: movie)")
        
        response = bot.handle_reply("Add New Movie")
        
        self.assertIn("Added Movie: New Movie", response)
        mock_radarr_instance.add_movie.assert_called_once()

    @patch('src.telegram.bot.GeminiClient')
    @patch('src.telegram.bot.SonarrClient')
    @patch('src.telegram.bot.RadarrClient')
    @patch('src.telegram.bot.Database')
    @patch('src.telegram.bot.telebot')
    def test_handle_reply_no_recs(self, mock_telebot, MockDB, MockRadarr, MockSonarr, MockGemini):
        mock_db = MockDB.return_value
        mock_db.get_recommendation_by_position.return_value = None # No active recs
        
        bot = TelegramBot()
        response = bot.handle_reply("Add New Movie")
        
        self.assertEqual(response, "No active recommendations to act on.")

if __name__ == '__main__':
    unittest.main()
