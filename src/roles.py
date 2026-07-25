import difflib

import re

ROLES = ["Assassin", "Fighter", "Mage", "Marksman", "Support", "Tank"]


def find_mentioned_roles(query: str) -> list[str]:
    query_lower = query.lower()
    mentioned = []
    for role in ROLES:
        if role.lower() in query_lower:
            mentioned.append(role)
    return mentioned
def fuzzy_find_roles(query: str) -> list[str]:
    query_words = re.findall(r"[a-zA-Z]{4,}", query.lower())
    matched = []
    for role in ROLES:
        for word in query_words:
            if difflib.get_close_matches(word, [role.lower()], n=1, cutoff=0.8):
                if role not in matched:
                    matched.append(role)
    return matched