import difflib
import re

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

REGION_TR_SYNONYMS = {
    "Bandle City": ["yordle şehri"],
    "Shadow Isles": ["gölge adalar", "golge adalar"],
    "Demacia": ["demacialı", "demacyalı", "demacyali"],
    "Freljord": ["buz diyarı", "buz diyari", "buzul"],
    "Ionia": ["ionialı", "ionyalı", "ionyali"],
    "Noxus": ["noxuslu"],
    "Shurima": ["shurimalı", "shurimali"],
    "Void": ["uçurum", "ucurum", "boşluk", "bosluk"],
}


def _all_region_keywords(region: str) -> list[str]:
    return REGION_KEYWORDS.get(region, []) + REGION_TR_SYNONYMS.get(region, [])


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
    """Detect which known regions are literally mentioned (by name or keyword, EN or TR) in a query."""
    query_lower = query.lower()
    mentioned = []
    for region in REGION_KEYWORDS:
        if any(kw in query_lower for kw in _all_region_keywords(region)):
            mentioned.append(region)
    return mentioned


def fuzzy_find_regions(query: str) -> list[str]:
    query_words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}", query.lower())
    matched = []
    for region in REGION_KEYWORDS:
        for kw in _all_region_keywords(region):
            for word in query_words:
                if difflib.get_close_matches(word, [kw], n=1, cutoff=0.8):
                    if region not in matched:
                        matched.append(region)
    return matched


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