import re


def format_markdown_for_telegram(text: str) -> str:
    """
    Converts standard Markdown text into Telegram-compatible HTML.

    Supported formats:
    - Escapes HTML special characters: &, <, >
    - Preserves code blocks (```code```) and inline code (`code`) by placeholder isolation
    - Headers:
        - # Header -> <b>🌟 HEADER 🌟</b>
        - ## Header -> <b>HEADER</b>
        - ### Header -> <b>Header</b>
    - Lists: Converts leading '- ' or '* ' to '• ' (preserving indentation)
    - Bold: **text** or __text__ -> <b>text</b>
    - Italic: *text* or _text_ -> <i>text</i> (using word-boundary safety for underscores)
    - Links: [text](url) -> <a href="url">text</a>
    """
    if not text:
        return ""

    # 1. Escape HTML special characters so they don't get parsed as HTML tags
    escaped_text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # 2. Extract code blocks and isolate them with placeholders (no formatting chars to avoid regex collisions)
    code_blocks = []

    def save_code_block(match):
        code = match.group(1)
        code_blocks.append(code)
        placeholder_idx = len(code_blocks) - 1
        return f"CODEBLOCKPLAT{placeholder_idx}"

    # Match ```optional_lang\ncode\n```
    escaped_text = re.sub(
        r"```(?:\w+)?\n?(.*?)\n?```", save_code_block, escaped_text, flags=re.DOTALL
    )

    # 3. Extract inline code and isolate with placeholders
    inline_codes = []

    def save_inline_code(match):
        code = match.group(1)
        inline_codes.append(code)
        placeholder_idx = len(inline_codes) - 1
        return f"INLINECODEPLAT{placeholder_idx}"

    # Match `code` (excluding newlines for inline code)
    escaped_text = re.sub(r"`([^`\n]+)`", save_inline_code, escaped_text)

    # 4. Line-by-line processing for headers and lists
    lines = escaped_text.split("\n")
    processed_lines = []
    for line in lines:
        # Match headers in decreasing order of hashes
        h3_match = re.match(r"^###\s+(.+)$", line)
        h2_match = re.match(r"^##\s+(.+)$", line)
        h1_match = re.match(r"^#\s+(.+)$", line)

        if h3_match:
            line = f"<b>{h3_match.group(1).strip()}</b>"
        elif h2_match:
            line = f"<b>{h2_match.group(1).strip().upper()}</b>"
        elif h1_match:
            line = f"<b>🌟 {h1_match.group(1).strip().upper()} 🌟</b>"
        else:
            # Match list items and convert '-' or '*' to '•' preserving spaces
            bullet_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
            if bullet_match:
                indent = bullet_match.group(1)
                content = bullet_match.group(2)
                line = f"{indent}• {content}"

        processed_lines.append(line)

    escaped_text = "\n".join(processed_lines)

    # 5. Process Bold and Italic formatting
    # Bold: **bold** or __bold__
    escaped_text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", escaped_text)
    escaped_text = re.sub(r"__(.*?)__", r"<b>\1</b>", escaped_text)

    # Italic: *italic* or _italic_ (with word-boundary lookarounds for underscores to avoid matching within words)
    escaped_text = re.sub(r"\*(.*?)\*", r"<i>\1</i>", escaped_text)
    escaped_text = re.sub(r"(?<!\w)_(.*?)_(?!\w)", r"<i>\1</i>", escaped_text)

    # 6. Process Links: [text](url) -> <a href="url">text</a>
    escaped_text = re.sub(r"\[(.*?)\]\((.*?)\)", r'<a href="\2">\1</a>', escaped_text)

    # 7. Restore placeholders
    # Inline code first
    for idx, code in enumerate(inline_codes):
        placeholder = f"INLINECODEPLAT{idx}"
        escaped_text = escaped_text.replace(placeholder, f"<code>{code}</code>")

    # Code blocks
    for idx, code in enumerate(code_blocks):
        placeholder = f"CODEBLOCKPLAT{idx}"
        escaped_text = escaped_text.replace(placeholder, f"<pre>{code}</pre>")

    return escaped_text


def format_recommendations(recs: list) -> str:
    """
    Formats a list of recommendation dictionaries into a single markdown string
    suitable for passing to format_markdown_for_telegram.
    """
    movies = [r for r in recs if r.get("media_type") == "movie"]
    tv_shows = [r for r in recs if r.get("media_type") == "tv"]

    message = "# Weekly Media Recommendations\n\n"

    if movies:
        message += "## Movies\n"
        for rec in movies:
            icon = "🎥"
            release_info = f" ({rec.get('release_info', '')})" if rec.get('release_info') else ""
            rating_info = f" - ⭐ {rec.get('rating')}/10" if rec.get('rating') else ""
            tmdb_link = f" [TMDB](https://www.themoviedb.org/movie/{rec.get('tmdb_id')})" if rec.get('tmdb_id') else ""
            message += f"**{rec['position']}. {icon} {rec['title']}{release_info}**{rating_info}{tmdb_link}\n"
            message += f"Why: *{rec['justification']}*\n\n"

    if tv_shows:
        message += "## TV Series\n"
        for rec in tv_shows:
            icon = "📺"
            release_info = f" ({rec.get('release_info', '')})" if rec.get('release_info') else ""
            rating_info = f" - ⭐ {rec.get('rating')}/10" if rec.get('rating') else ""
            tmdb_link = f" [TMDB](https://www.themoviedb.org/tv/{rec.get('tmdb_id')})" if rec.get('tmdb_id') else ""
            message += f"**{rec['position']}. {icon} {rec['title']}{release_info}**{rating_info}{tmdb_link}\n"
            message += f"Why: *{rec['justification']}*\n\n"

    message += "Reply with 'Add [Title]' or 'Download #1' to add to your library!"
    return message
