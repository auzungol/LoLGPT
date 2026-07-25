# Not: Riot bunu resmi API'de vermiyor, bu yüzden elle derlenmiştir.
# Anahtar olarak dosya adlarınla (küçük harf, champion_id) eşleşmeli.
# Bazı yeni şampiyonlar (henüz emin olamadıklarım) "Unknown" bırakıldı — ekleyebilirsin.
import re
import difflib

LANES = {
    "aatrox": ["Top"],
    "ahri": ["Mid"],
    "akali": ["Mid", "Top"],
    "akshan": ["Mid", "Top"],
    "alistar": ["Support"],
    "ambessa": ["Top", "Mid"],
    "amumu": ["Jungle", "Support"],
    "anivia": ["Mid"],
    "annie": ["Mid", "Support"],
    "aphelios": ["ADC"],
    "ashe": ["ADC", "Support"],
    "aurelionsol": ["Mid"],
    "aurora": ["Mid", "Top"],
    "azir": ["Mid"],
    "bard": ["Support"],
    "belveth": ["Jungle"],
    "blitzcrank": ["Support"],
    "brand": ["Support", "Mid"],
    "braum": ["Support"],
    "briar": ["Jungle"],
    "caitlyn": ["ADC"],
    "camille": ["Top"],
    "cassiopeia": ["Mid"],
    "chogath": ["Top"],
    "corki": ["Mid"],
    "darius": ["Top"],
    "diana": ["Jungle", "Mid"],
    "drmundo": ["Top"],
    "draven": ["ADC"],
    "ekko": ["Jungle", "Mid"],
    "elise": ["Jungle"],
    "evelynn": ["Jungle"],
    "ezreal": ["ADC"],
    "fiddlesticks": ["Jungle"],
    "fiora": ["Top"],
    "fizz": ["Mid"],
    "galio": ["Mid", "Support"],
    "gangplank": ["Top"],
    "garen": ["Top"],
    "gnar": ["Top"],
    "gragas": ["Jungle", "Top"],
    "graves": ["Jungle"],
    "gwen": ["Top", "Jungle"],
    "hecarim": ["Jungle"],
    "heimerdinger": ["Mid", "Support", "Top"],
    "hwei": ["Mid", "Support"],
    "illaoi": ["Top"],
    "irelia": ["Top", "Mid"],
    "ivern": ["Jungle"],
    "janna": ["Support"],
    "jarvaniv": ["Jungle"],
    "jax": ["Top", "Jungle"],
    "jayce": ["Top", "Mid"],
    "jhin": ["ADC"],
    "jinx": ["ADC"],
    "ksante": ["Top"],
    "kaisa": ["ADC"],
    "kalista": ["ADC"],
    "karma": ["Support", "Mid"],
    "karthus": ["Jungle", "Mid"],
    "kassadin": ["Mid"],
    "katarina": ["Mid"],
    "kayle": ["Top", "Mid"],
    "kayn": ["Jungle"],
    "kennen": ["Top"],
    "khazix": ["Jungle"],
    "kindred": ["Jungle"],
    "kled": ["Top"],
    "kogmaw": ["ADC"],
    "leblanc": ["Mid"],
    "leesin": ["Jungle"],
    "leona": ["Support"],
    "lillia": ["Jungle"],
    "lissandra": ["Mid"],
    "lucian": ["ADC", "Mid"],
    "lulu": ["Support"],
    "lux": ["Support", "Mid"],
    "malphite": ["Top", "Support"],
    "malzahar": ["Mid"],
    "maokai": ["Support", "Top", "Jungle"],
    "masteryi": ["Jungle"],
    "milio": ["Support"],
    "missfortune": ["ADC"],
    "mordekaiser": ["Top"],
    "morgana": ["Support", "Mid"],
    "naafiri": ["Mid", "Jungle"],
    "nami": ["Support"],
    "nasus": ["Top"],
    "nautilus": ["Support", "Jungle"],
    "neeko": ["Support", "Mid"],
    "nidalee": ["Jungle"],
    "nilah": ["ADC"],
    "nocturne": ["Jungle"],
    "nunu": ["Jungle"],
    "olaf": ["Jungle", "Top"],
    "orianna": ["Mid"],
    "ornn": ["Top"],
    "pantheon": ["Support", "Top", "Mid"],
    "poppy": ["Top", "Jungle", "Support"],
    "pyke": ["Support"],
    "qiyana": ["Mid", "Jungle"],
    "quinn": ["Top"],
    "rakan": ["Support"],
    "rammus": ["Jungle"],
    "reksai": ["Jungle"],
    "rell": ["Support"],
    "renata": ["Support"],
    "renekton": ["Top"],
    "rengar": ["Jungle"],
    "riven": ["Top"],
    "rumble": ["Top", "Jungle"],
    "ryze": ["Mid"],
    "samira": ["ADC"],
    "sejuani": ["Jungle"],
    "senna": ["Support", "ADC"],
    "seraphine": ["Support", "ADC"],
    "sett": ["Top", "Support"],
    "shaco": ["Jungle", "Support"],
    "shen": ["Top", "Support"],
    "shyvana": ["Jungle"],
    "singed": ["Top"],
    "sion": ["Top"],
    "sivir": ["ADC"],
    "skarner": ["Jungle"],
    "smolder": ["ADC"],
    "sona": ["Support"],
    "soraka": ["Support"],
    "swain": ["Support", "Mid"],
    "sylas": ["Mid", "Jungle"],
    "syndra": ["Mid"],
    "tahmkench": ["Support", "Top"],
    "taliyah": ["Jungle", "Mid"],
    "talon": ["Mid", "Jungle"],
    "taric": ["Support"],
    "teemo": ["Top"],
    "thresh": ["Support"],
    "tristana": ["ADC", "Mid"],
    "trundle": ["Top", "Jungle"],
    "tryndamere": ["Top"],
    "twistedfate": ["Mid"],
    "twitch": ["ADC"],
    "udyr": ["Jungle"],
    "urgot": ["Top"],
    "varus": ["ADC"],
    "vayne": ["ADC", "Top"],
    "veigar": ["Mid", "Support"],
    "velkoz": ["Support", "Mid"],
    "vex": ["Mid"],
    "vi": ["Jungle"],
    "viego": ["Jungle"],
    "viktor": ["Mid"],
    "vladimir": ["Mid", "Top"],
    "volibear": ["Jungle", "Top"],
    "warwick": ["Jungle"],
    "xayah": ["ADC"],
    "xerath": ["Mid", "Support"],
    "xinzhao": ["Jungle"],
    "yasuo": ["Mid", "Top"],
    "yone": ["Mid", "Top"],
    "yorick": ["Top"],
    "yuumi": ["Support"],
    "zac": ["Jungle"],
    "zed": ["Mid"],
    "zeri": ["ADC"],
    "ziggs": ["Mid", "ADC"],
    "zilean": ["Support"],
    "zoe": ["Mid", "Support"],
    "zyra": ["Support", "Mid"],
    "monkeyking": ["Jungle", "Top"],
    "locke": ["Unknown"],
    "mel": ["Mid", "Support"],
    "yunara": ["Unknown"],
    "zaahen": ["Unknown"],
}

ALL_LANES = ["Top", "Jungle", "Mid", "ADC", "Support"]

LANE_KEYWORDS = {
    "Top": ["top", "toplaner", "top lane"],
    "Jungle": ["jungle", "jungler", "jg"],
    "Mid": ["mid", "midlane", "mid lane", "midlaner"],
    "ADC": ["adc", "bot lane", "botlane", "marksman lane"],
    "Support": ["support", "sup"],
}

LANE_TR_SYNONYMS = {
    "Top": ["üst koridor", "ust koridor"],
    "Jungle": ["orman", "ormancı", "ormanci"],
    "Mid": ["orta koridor", "orta"],
    "ADC": ["alt koridor"],
    "Support": ["destek"],
}


def _all_lane_keywords(lane: str) -> list[str]:
    return LANE_KEYWORDS.get(lane, []) + LANE_TR_SYNONYMS.get(lane, [])


def get_lanes_for_champion(champion_id: str) -> list[str]:
    return LANES.get(champion_id.lower(), ["Unknown"])


def find_mentioned_lanes(query: str) -> list[str]:
    query_lower = query.lower()
    mentioned = []
    for lane in LANE_KEYWORDS:
        for kw in _all_lane_keywords(lane):
            if re.search(rf"\b{re.escape(kw)}\b", query_lower):
                mentioned.append(lane)
                break
    return mentioned


def fuzzy_find_lanes(query: str) -> list[str]:
    query_words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]{3,}", query.lower())
    matched = []
    for lane in LANE_KEYWORDS:
        for kw in _all_lane_keywords(lane):
            for word in query_words:
                if difflib.get_close_matches(word, [kw], n=1, cutoff=0.8):
                    if lane not in matched:
                        matched.append(lane)
    return matched