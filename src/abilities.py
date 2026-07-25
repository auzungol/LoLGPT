import re

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
        # Boşluklu tek harf: "yasuo r si", "veigar q"
        if re.search(rf"\b{l}\b", query_lower):
            return letter
        # Doğru Türkçe kullanım (kesme işaretiyle): "Q'sunu", "E'sini"
        if re.search(rf"\b{l}['’]\w*", query_lower):
            return letter
        # Kesmesiz bitişik yazım (yaygın hatalı kullanım): "qsunu", "esini"
        if re.search(rf"\b{l}(sunu|sını|sini|sünü|yu|yı|yi|yü|su|sı|si|sü)\b", query_lower):
            return letter
    return None


def extract_ability_line(full_content: str, letter: str) -> str | None:
    pattern = rf"^{re.escape(letter)} - .+$"
    match = re.search(pattern, full_content, re.MULTILINE)
    return match.group(0) if match else None