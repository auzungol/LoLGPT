REGION_KEYWORDS = {
    "Bandle City": ["bandle city", "yordle"],
    "Shadow Isles": ["shadow isles", "black mist", "ruined"],
    "Bilgewater": ["bilgewater"],
    "Demacia": ["demacia", "demacian"],
    "Freljord": ["freljord", "freljordian", "avarosan", "winter's claw", "frostguard"],
    "Ionia": ["ionia", "ionian", "vastaya", "vastayan"],
    "Ixtal": ["ixtal", "ixtali"],
    "Noxus": ["noxus", "noxian"],
    "Piltover": ["piltover", "piltovan"],
    "Zaun": ["zaun", "zaunite"],
    "Shurima": ["shurima", "shuriman"],
    "Targon": ["targon", "targonian", "aspect of"],
    "Camavor": ["camavor", "camavoran"],
    "Icathia": ["icathia", "icathian"],
    "Void": ["the void", "void-born", "voidborn"],
}


def detect_region(text: str) -> str:
    """Find the earliest-mentioned known region (by name or common adjective/demonym) in the text."""
    text_lower = text.lower()
    best_region = None
    best_pos = None
    for region, keywords in REGION_KEYWORDS.items():
        for kw in keywords:
            pos = text_lower.find(kw)
            if pos != -1 and (best_pos is None or pos < best_pos):
                best_pos = pos
                best_region = region
    return best_region or "Unknown"


def find_mentioned_regions(query: str) -> list[str]:
    """Detect which known regions are literally mentioned (by name or keyword) in a query."""
    query_lower = query.lower()
    mentioned = []
    for region, keywords in REGION_KEYWORDS.items():
        if any(kw in query_lower for kw in keywords):
            mentioned.append(region)
    return mentioned

CHAMPION_REGION_OVERRIDES = {
    "akshan": "Shurima",
    "aphelios": "Targon",
    "briar": "Noxus",
    "gwen": "Shadow Isles",
    "illaoi": "Bilgewater",
    "lissandra": "Freljord",
    "malphite": "Shurima",
    "mordekaiser": "Noxus",
    "nilah": "Ixtal",
    "qiyana": "Ixtal",
    "tahmkench": "Bilgewater",
    "twistedfate": "Bilgewater",
    "viktor": "Zaun",
    "yone": "Ionia",
    "zyra": "Shurima",
}