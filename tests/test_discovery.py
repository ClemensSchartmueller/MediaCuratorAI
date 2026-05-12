import unittest
from unittest.mock import patch
from src.ai.discovery import DiscoveryPipeline

class TestDiscoveryPipeline(unittest.TestCase):
    @patch('src.ai.discovery.Database')
    @patch('src.ai.discovery.GeminiClient')
    @patch('src.ai.discovery.JellyfinClient')
    @patch('src.ai.discovery.SonarrClient')
    @patch('src.ai.discovery.RadarrClient')
    @patch('src.ai.discovery.TMDBClient')
    def test_run_weekly_discovery(self, MockTMDB, MockRadarr, MockSonarr, MockJellyfin, MockGemini, MockDB):
        # Setup mocks
        mock_db = MockDB.return_value
        mock_db.get_taste_profile.return_value = "Likes action."
        
        mock_radarr = MockRadarr.return_value
        mock_radarr.get_movies.return_value = [{'tmdbId': 1}]
        
        mock_sonarr = MockSonarr.return_value
        mock_sonarr.get_series.return_value = [{'tmdbId': 2}]
        
        mock_jellyfin = MockJellyfin.return_value
        mock_jellyfin.get_recent_items.return_value = {'Items': [{'ExternalIds': {'Tmdb': '3'}}]}
        
        mock_tmdb = MockTMDB.return_value
        mock_tmdb.discover_new_releases.return_value = {'results': [{'id': 4, 'title': 'New Movie', 'overview': '...'}]}
        mock_tmdb.discover_new_tv.return_value = {'results': [{'id': 5, 'name': 'New Show', 'overview': '...'}]}
        
        mock_gemini = MockGemini.return_value
        mock_gemini.curate_recommendations.return_value = '{"recommendations": [{"title": "New Movie", "tmdb_id": 4, "media_type": "movie", "justification": "Because action."}]}'
        
        # Run
        pipeline = DiscoveryPipeline()
        recs, raw_curation = pipeline.run_weekly_discovery()
        
        # Assertions
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs[0]['title'], "New Movie")
        self.assertEqual(recs[0]['position'], 1)
        self.assertEqual(recs[0]['justification'], "Because action.")

    @patch('src.ai.discovery.Database')
    @patch('src.ai.discovery.GeminiClient')
    @patch('src.ai.discovery.JellyfinClient')
    @patch('src.ai.discovery.SonarrClient')
    @patch('src.ai.discovery.RadarrClient')
    @patch('src.ai.discovery.TMDBClient')
    def test_missing_profile(self, MockTMDB, MockRadarr, MockSonarr, MockJellyfin, MockGemini, MockDB):
        mock_db = MockDB.return_value
        mock_db.get_taste_profile.return_value = None # No profile

        pipeline = DiscoveryPipeline()
        
        with self.assertRaises(ValueError) as context:
            pipeline.run_weekly_discovery()
        
        self.assertTrue("Taste profile missing" in str(context.exception))

if __name__ == '__main__':
    unittest.main()
