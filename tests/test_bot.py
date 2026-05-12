import unittest
from unittest.mock import patch, MagicMock
from src.signals.bot import SignalBot

class TestSignalBot(unittest.TestCase):
    @patch('src.signals.bot.GeminiClient')
    @patch('src.signals.bot.SonarrClient')
    @patch('src.signals.bot.RadarrClient')
    @patch('src.signals.bot.Database')
    @patch('src.signals.bot.requests')
    def test_handle_reply_movie(self, mock_requests, MockDB, MockRadarr, MockSonarr, MockGemini):
        mock_db = MockDB.return_value
        mock_db.get_recommendation_by_position.return_value = {"id": 1}
        
        # Test the bot handling a reply
        mock_gemini_instance = MockGemini.return_value
        mock_model_response = MagicMock()
        mock_model_response.text = '[{"tmdb_id": 4, "title": "New Movie", "type": "movie"}]'
        mock_gemini_instance.generate_content.return_value = mock_model_response
        
        mock_radarr_instance = MockRadarr.return_value
        
        bot = SignalBot()
        bot.url = "http://mock-signal"
        bot.number = "+1"
        bot.recipient = "+2"
        
        # Mock summary to avoid DB fetch error inside _get_active_recs_summary
        bot._get_active_recs_summary = MagicMock(return_value="1. New Movie (TMDB: 4, Type: movie)")
        
        response = bot.handle_reply("Add New Movie")
        
        self.assertIn("Added Movie: New Movie", response)
        mock_radarr_instance.add_movie.assert_called_once()

    @patch('src.signals.bot.GeminiClient')
    @patch('src.signals.bot.SonarrClient')
    @patch('src.signals.bot.RadarrClient')
    @patch('src.signals.bot.Database')
    @patch('src.signals.bot.requests')
    def test_handle_reply_no_recs(self, mock_requests, MockDB, MockRadarr, MockSonarr, MockGemini):
        mock_db = MockDB.return_value
        mock_db.get_recommendation_by_position.return_value = None # No active recs
        
        bot = SignalBot()
        response = bot.handle_reply("Add New Movie")
        
        self.assertEqual(response, "No active recommendations to act on.")

if __name__ == '__main__':
    unittest.main()
