ROLES = ["Assassin", "Fighter", "Mage", "Marksman", "Support", "Tank"]


def find_mentioned_roles(query: str) -> list[str]:
    query_lower = query.lower()
    mentioned = []
    for role in ROLES:
        if role.lower() in query_lower:
            mentioned.append(role)
    return mentioned