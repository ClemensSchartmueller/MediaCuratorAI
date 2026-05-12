import unittest
from unittest.mock import patch, MagicMock
from src.ai.profiler import Profiler


class TestProfiler(unittest.TestCase):
    @patch("src.ai.profiler.Database")
    @patch("src.ai.profiler.GeminiClient")
    @patch("src.ai.profiler.JellyfinClient")
    def test_run(self, MockJellyfin, MockGemini, MockDB):
        # Setup mocks
        mock_jellyfin_instance = MockJellyfin.return_value
        mock_jellyfin_instance.get_watch_history.return_value = {
            "Items": [
                {
                    "Name": "Test Movie",
                    "Genres": ["Action"],
                    "Overview": "An action movie.",
                }
            ]
        }

        mock_gemini_instance = MockGemini.return_value
        mock_gemini_instance.generate_taste_profile.return_value = (
            "User likes Action movies."
        )

        mock_db_instance = MockDB.return_value

        # Run
        profiler = Profiler()
        profile = profiler.run()

        # Assertions
        self.assertEqual(profile, "User likes Action movies.")
        mock_jellyfin_instance.get_watch_history.assert_called_once()
        mock_gemini_instance.generate_taste_profile.assert_called_once()
        mock_db_instance.save_taste_profile.assert_called_once_with(
            "User likes Action movies."
        )


if __name__ == "__main__":
    unittest.main()
