import re

ABILITY_LETTERS = ["Passive", "Q", "W", "E", "R"]


def find_mentioned_ability_letter(query: str) -> str | None:
    """Detect a standalone ability letter/keyword mentioned in the query."""
    query_lower = query.lower()
    if re.search(r"\b(ultimate|ulti|ult)\w*\b", query_lower):
        return "R"
    if re.search(r"\bpassive\w*\b", query_lower):
        return "Passive"
    for letter in ["Q", "W", "E", "R"]:
        if re.search(rf"\b{letter.lower()}\b", query_lower):
            return letter
    return None


def extract_ability_line(full_content: str, letter: str) -> str | None:
    pattern = rf"^{re.escape(letter)} - .+$"
    match = re.search(pattern, full_content, re.MULTILINE)
    return match.group(0) if match else None