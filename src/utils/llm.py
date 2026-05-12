import re


_CODE_BLOCK_PATTERN = re.compile(
    r"(?ms)(?:^|\n)```(?P<lang>[^\n`]*)[ \t]*\n"
    r"(?P<content>.*?)(?:\n?```[ \t]*(?=\n|$))"
)


def extract_json_from_response(text: str) -> str:
    """
    Extracts JSON from LLM responses that may be wrapped in markdown code blocks.
    """
    text = text.strip()
    blocks = list(_CODE_BLOCK_PATTERN.finditer(text))
    if not blocks:
        return text

    for block in blocks:
        if block.group("lang").strip().lower() == "json":
            return block.group("content").strip()

    return blocks[0].group("content").strip()
