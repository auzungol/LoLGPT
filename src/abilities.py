import re
import difflib

ABILITY_LETTERS = ["Passive", "Q", "W", "E", "R"]


def find_mentioned_ability_letter(query: str) -> str | None:
    """Detect a standalone ability letter/keyword mentioned in the query (EN or TR, with or without apostrophe)."""
    query_lower = query.lower()

    if re.search(r"\b(ultimate|ulti|ult)\w*\b", query_lower):
        return "R"
    if re.search(r"\b(passive\w*|pasif\w*)\b", query_lower):
        return "Passive"

    for letter in ["Q", "W", "E", "R"]:
        l = letter.lower()
        if re.search(rf"\b{l}\b", query_lower):
            return letter
        if re.search(rf"\b{l}['’]\w*", query_lower):
            return letter
        if re.search(rf"\b{l}(sunu|sını|sini|sünü|yu|yı|yi|yü|su|sı|si|sü)\b", query_lower):
            return letter

    # Hiçbiri tam eşleşmediyse, yazım hatası toleranslı dene (örn. "passiv", "pasifi")
    words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}", query_lower)
    for word in words:
        if difflib.get_close_matches(word, ["passive", "pasif"], n=1, cutoff=0.75):
            return "Passive"
        if difflib.get_close_matches(word, ["ultimate", "ulti"], n=1, cutoff=0.75):
            return "R"

    return None


def extract_ability_line(full_content: str, letter: str) -> str | None:
    pattern = rf"^{re.escape(letter)} - .+$"
    match = re.search(pattern, full_content, re.MULTILINE)
    return match.group(0) if match else None