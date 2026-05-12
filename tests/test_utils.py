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

    def test_extract_json_ignores_inline_fence_mention(self):
        text = (
            'I used ```json``` as an example format.\n'
            'Actual output:\n```json\n{"key": "value"}\n```'
        )
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_prefers_json_block_among_multiple_blocks(self):
        text = (
            "First block:\n```\nnot json\n```\n"
            'Then JSON:\n```json\n{"key": "value"}\n```'
        )
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_with_no_newline_before_closing_fence(self):
        text = '```json\n{"key": "value"}```'
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)

    def test_extract_json_does_not_treat_jsonnet_as_json(self):
        text = (
            "```jsonnet\nnot json\n```\n"
            '```json\n{"key": "value"}\n```'
        )
        expected = '{"key": "value"}'
        self.assertEqual(extract_json_from_response(text), expected)


if __name__ == "__main__":
    unittest.main()
