import difflib
import re

ROLES = ["Assassin", "Fighter", "Mage", "Marksman", "Support", "Tank"]

ROLE_TR_SYNONYMS = {
    "Assassin": ["suikastçı", "suikastci"],
    "Fighter": ["dövüşçü", "dovuscu", "savaşçı", "savasci"],
    "Mage": ["büyücü", "buyucu"],
    "Marksman": ["nişancı", "nisanci"],
    "Support": ["destek"],
    "Tank": ["tank"],
}


def _role_keywords(role: str) -> list[str]:
    return [role.lower()] + [s.lower() for s in ROLE_TR_SYNONYMS.get(role, [])]


def find_mentioned_roles(query: str) -> list[str]:
    query_lower = query.lower()
    mentioned = []
    for role in ROLES:
        for kw in _role_keywords(role):
            if re.search(rf"\b{re.escape(kw)}\b", query_lower):
                mentioned.append(role)
                break
    return mentioned


def fuzzy_find_roles(query: str) -> list[str]:
    query_words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}", query.lower())
    matched = []
    for role in ROLES:
        for kw in _role_keywords(role):
            for word in query_words:
                if difflib.get_close_matches(word, [kw], n=1, cutoff=0.8):
                    if role not in matched:
                        matched.append(role)
    return matched