def extract_json_from_response(text: str) -> str:
    """
    Extracts JSON string from an LLM response that might be wrapped in markdown code blocks.
    """
    text = text.strip()
    if "```json" in text:
        return text.split("```json")[1].split("```")[0].strip()
    elif "```" in text:
        return text.split("```")[1].split("```")[0].strip()
    return text
