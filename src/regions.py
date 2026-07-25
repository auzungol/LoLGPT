REGIONS = [
    "Bandle City",
    "Shadow Isles",
    "Bilgewater",
    "Demacia",
    "Freljord",
    "Ionia",
    "Ixtal",
    "Noxus",
    "Piltover",
    "Zaun",
    "Shurima",
    "Targon",
    "Camavor",
    "Icathia",
    "the Void",
]


def detect_region(text: str) -> str:
    """Find the first-mentioned known region name in the given text."""
    text_lower = text.lower()
    best_region = None
    best_pos = None
    for region in REGIONS:
        pos = text_lower.find(region.lower())
        if pos != -1 and (best_pos is None or pos < best_pos):
            best_pos = pos
            best_region = region
    if best_region == "the Void":
        best_region = "Void"
    return best_region or "Unknown"


def find_mentioned_regions(query: str) -> list[str]:
    """Detect which known regions are literally mentioned in a query."""
    query_lower = query.lower()
    mentioned = []
    for region in REGIONS:
        name = region.replace("the ", "")
        if name.lower() in query_lower:
            mentioned.append(name if name != "Void" else "Void")
    return mentioned