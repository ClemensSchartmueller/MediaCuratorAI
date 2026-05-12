import unittest
from src.utils.llm import extract_json_from_response

class TestLLMUtils(unittest.TestCase):
    def test_extract_json_with_backticks(self):
        text = '```json\n{"key": "value"}\n```'
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_with_generic_backticks(self):
        text = '```\n{"key": "value"}\n```'
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_no_backticks(self):
        text = '{"key": "value"}'
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_with_prefix_text(self):
        text = 'Here is the result:\n```json\n{"key": "value"}\n```'
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

if __name__ == "__main__":
    unittest.main()
