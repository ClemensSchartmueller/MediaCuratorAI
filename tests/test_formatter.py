import unittest
from src.telegram.formatter import format_markdown_for_telegram


class TestTelegramFormatter(unittest.TestCase):
    def test_plain_text(self):
        self.assertEqual(format_markdown_for_telegram("Hello world"), "Hello world")
        self.assertEqual(format_markdown_for_telegram(""), "")
        self.assertEqual(format_markdown_for_telegram(None), "")

    def test_html_escaping(self):
        # & -> &amp;, < -> &lt;, > -> &gt;
        self.assertEqual(
            format_markdown_for_telegram("A & B < C > D"), "A &amp; B &lt; C &gt; D"
        )

    def test_bold_formatting(self):
        self.assertEqual(
            format_markdown_for_telegram("This is **bold** text"),
            "This is <b>bold</b> text",
        )
        self.assertEqual(
            format_markdown_for_telegram("This is __bold__ text"),
            "This is <b>bold</b> text",
        )

    def test_italic_formatting(self):
        self.assertEqual(
            format_markdown_for_telegram("This is *italic* text"),
            "This is <i>italic</i> text",
        )
        self.assertEqual(
            format_markdown_for_telegram("This is _italic_ text"),
            "This is <i>italic</i> text",
        )
        # Ensure underscores inside words are not matched
        self.assertEqual(
            format_markdown_for_telegram("some_variable_name"), "some_variable_name"
        )
        self.assertEqual(
            format_markdown_for_telegram("hello _world_ check_this"),
            "hello <i>world</i> check_this",
        )

    def test_headers(self):
        self.assertEqual(format_markdown_for_telegram("# title"), "<b>🌟 TITLE 🌟</b>")
        self.assertEqual(
            format_markdown_for_telegram("## sub title"), "<b>SUB TITLE</b>"
        )
        self.assertEqual(format_markdown_for_telegram("### section"), "<b>section</b>")

    def test_lists(self):
        self.assertEqual(format_markdown_for_telegram("- item 1"), "• item 1")
        self.assertEqual(format_markdown_for_telegram("* item 2"), "• item 2")
        self.assertEqual(
            format_markdown_for_telegram("  - indented item"), "  • indented item"
        )
        self.assertEqual(
            format_markdown_for_telegram("  * indented item 2"), "  • indented item 2"
        )

    def test_links(self):
        self.assertEqual(
            format_markdown_for_telegram("Check [Google](https://google.com) here"),
            'Check <a href="https://google.com">Google</a> here',
        )

    def test_code_preservation(self):
        # Inline code
        self.assertEqual(
            format_markdown_for_telegram("Run `pip install telebot` now"),
            "Run <code>pip install telebot</code> now",
        )
        # Inline code with formatting characters inside shouldn't be formatted
        self.assertEqual(
            format_markdown_for_telegram("Code `a * b` and `x_y`"),
            "Code <code>a * b</code> and <code>x_y</code>",
        )
        # Inline code with HTML characters inside
        self.assertEqual(
            format_markdown_for_telegram("Compare `a < b`"),
            "Compare <code>a &lt; b</code>",
        )

        # Code block
        code_block = "```python\nfor i in range(5):\n    print(i)\n```"
        self.assertEqual(
            format_markdown_for_telegram(code_block),
            "<pre>for i in range(5):\n    print(i)</pre>",
        )

        # Code block with formatting/HTML characters inside
        code_block_complex = "```\nif x < y and a * b:\n    _print_err()\n```"
        self.assertEqual(
            format_markdown_for_telegram(code_block_complex),
            "<pre>if x &lt; y and a * b:\n    _print_err()</pre>",
        )

    def test_complex_combination(self):
        markdown_input = (
            "# Recommendations\n\n"
            "Here is the list of movies you should check out:\n"
            "- **Dune** (Rating: *8.1*)\n"
            "  - Why: Great sci-fi visuals.\n"
            "- **The Batman** (Rating: *7.9*)\n"
            "  - Why: Gritty detective story.\n\n"
            "For details, visit [IMDb](https://imdb.com).\n"
            "Use command `python main.py discover` to refresh."
        )
        expected_output = (
            "<b>🌟 RECOMMENDATIONS 🌟</b>\n\n"
            "Here is the list of movies you should check out:\n"
            "• <b>Dune</b> (Rating: <i>8.1</i>)\n"
            "  • Why: Great sci-fi visuals.\n"
            "• <b>The Batman</b> (Rating: <i>7.9</i>)\n"
            "  • Why: Gritty detective story.\n\n"
            'For details, visit <a href="https://imdb.com">IMDb</a>.\n'
            "Use command <code>python main.py discover</code> to refresh."
        )
        self.assertEqual(format_markdown_for_telegram(markdown_input), expected_output)


if __name__ == "__main__":
    unittest.main()
