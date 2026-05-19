import unittest
from unittest.mock import patch, MagicMock
from src.clients.tmdb import TMDBClient
from src.ai.gemini import GeminiClient


class TestTMDBClient(unittest.TestCase):
    @patch("src.clients.base.requests.Session")
    def setUp(self, MockSession):
        self.mock_session = MockSession.return_value
        self.client = TMDBClient("mock-api-key")
        # Override session on the instantiated client
        self.client.session = self.mock_session

    def test_search_multi(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        self.mock_session.get.return_value = mock_response

        res = self.client.search_multi("Dune")
        self.assertEqual(res, {"results": []})
        self.mock_session.get.assert_called_once()
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("/search/multi", args[0])
        self.assertEqual(kwargs["params"]["query"], "Dune")

    def test_get_movie_details(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"title": "Dune"}
        self.mock_session.get.return_value = mock_response

        res = self.client.get_movie_details(123)
        self.assertEqual(res, {"title": "Dune"})
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("/movie/123", args[0])

    def test_get_tv_details(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"name": "Breaking Bad"}
        self.mock_session.get.return_value = mock_response

        res = self.client.get_tv_details(456)
        self.assertEqual(res, {"name": "Breaking Bad"})
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("/tv/456", args[0])

    def test_get_genres(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"genres": []}
        self.mock_session.get.return_value = mock_response

        res = self.client.get_genres("movie")
        self.assertEqual(res, {"genres": []})
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("/genre/movie/list", args[0])

    def test_discover_by_genre(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"results": []}
        self.mock_session.get.return_value = mock_response

        res = self.client.discover_by_genre(28, "movie")
        self.assertEqual(res, {"results": []})
        args, kwargs = self.mock_session.get.call_args
        self.assertIn("/discover/movie", args[0])
        self.assertEqual(kwargs["params"]["with_genres"], 28)


class TestGeminiClientChat(unittest.TestCase):
    @patch("src.ai.gemini.genai.Client")
    def test_create_chat_session(self, MockClient):
        mock_genai_client = MockClient.return_value
        client = GeminiClient("mock-api-key")
        client.client = mock_genai_client

        mock_chats = MagicMock()
        mock_genai_client.chats = mock_chats

        def mock_tool():
            """Mock tool description."""
            pass

        client.create_chat_session(tools=[mock_tool], system_instruction="Hello")

        mock_chats.create.assert_called_once()
        args, kwargs = mock_chats.create.call_args
        self.assertEqual(kwargs["model"], "gemini-flash-latest")
        self.assertIsNotNone(kwargs["config"])
        self.assertEqual(kwargs["config"].tools, [mock_tool])
        self.assertEqual(kwargs["config"].system_instruction, "Hello")


if __name__ == "__main__":
    unittest.main()
