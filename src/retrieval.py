import math
import re
import difflib
from database import get_all_chunks, get_distinct_champions, get_chunks_by_champion, get_chunks_by_region, get_chunks_by_role, get_champion_display_names
from embedding import embed_text
from regions import find_mentioned_regions
from roles import find_mentioned_roles
from roles import ROLES
from lanes import ALL_LANES
from regions import REGION_KEYWORDS
_STOPWORDS = {w.lower() for w in ROLES} | {w.lower() for w in ALL_LANES} | set(REGION_KEYWORDS.keys()) | {
    "which", "champions", "champ", "champs", "character", "who", "list", "name", "all",
    "lane", "region", "role", "ability", "abilities", "passive", "ulti", "ultimate",
    "from", "does", "have", "what", "the", "and",
}


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_mentioned_champions(query: str, all_champions: list[str]) -> list[str]:
    query_lower = query.lower()
    query_no_spaces = re.sub(r"\s+", "", query_lower)
    mentioned = []
    for champ in all_champions:
        champ_lower = champ.lower()
        if re.search(rf"\b{re.escape(champ_lower)}\b", query_lower):
            mentioned.append(champ)
        elif champ_lower in query_no_spaces:
            mentioned.append(champ)
    return mentioned
def _build_champion_tokens() -> dict:
    """Maps champion_id -> set of searchable name tokens (id + name parts)."""
    display_names = get_champion_display_names()
    tokens_map = {}
    for champ_id, display_name in display_names.items():
        tokens = {champ_id.lower()}
        for part in re.split(r"[\s'\.]+", display_name.lower()):
            if len(part) >= 3:
                tokens.add(part)
        tokens_map[champ_id] = tokens
    return tokens_map



def fuzzy_find_champions(query: str) -> list[str]:
    tokens_map = _build_champion_tokens()
    query_words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ']{3,}", query.lower())
    query_words = [w for w in query_words if w not in _STOPWORDS]

    matched = set()
    for champ_id, tokens in tokens_map.items():
        for word in query_words:
            # Aşama 1: tüm tokenlarla (id + isim parçaları) sıkı eşik
            if difflib.get_close_matches(word, tokens, n=1, cutoff=0.87):
                matched.add(champ_id)
                break
            # Aşama 2: sadece champion id'sinin kendisiyle, biraz daha gevşek eşik
            # (id'ler genelde tek/özgün kelimeler olduğu için yanlış-pozitif riski düşük)
            if difflib.get_close_matches(word, [champ_id], n=1, cutoff=0.8):
                matched.add(champ_id)
                break
    return list(matched)
def get_top_chunks(query: str, top_k: int = 8):
    all_champions = get_distinct_champions()
    mentioned_champions = find_mentioned_champions(query, all_champions)
    if not mentioned_champions:
        mentioned_champions = fuzzy_find_champions(query)
    mentioned_regions = find_mentioned_regions(query)

    included_ids = set()
    results = []

    for champ in mentioned_champions:
        for _id, champion, source_file, content, embedding in get_chunks_by_champion(champ):
            if _id not in included_ids:
                included_ids.add(_id)
                results.append((champion, content, 1.0))

    for region in mentioned_regions:
        seen_champions = set()
        for _id, champion, source_file, content, embedding in get_chunks_by_region(region):
            if champion in seen_champions or _id in included_ids:
                continue
            included_ids.add(_id)
            seen_champions.add(champion)
            results.append((champion, content, 1.0))

    if len(results) > top_k:
        results = results[:top_k]

    # Belirli bir şampiyon zaten kesin eşleştiyse, semantic doldurmaya GEREK YOK —
    # ekstra alakasız chunk eklemek küçük modelde kafa karışıklığına yol açıyor.
    if mentioned_champions:
        return results

    remaining_slots = max(top_k - len(results), 0)
    if remaining_slots > 0:
        query_vec = embed_text(query)
        rows = get_all_chunks()

        scored = []
        for _id, champion, source_file, content, embedding in rows:
            if _id in included_ids:
                continue
            score = cosine_similarity(query_vec, embedding)
            scored.append((_id, champion, content, score))

        scored.sort(key=lambda x: x[3], reverse=True)
        for _id, champion, content, score in scored[:remaining_slots]:
            results.append((champion, content, score))

    return results


if __name__ == "__main__":
    results = get_top_chunks("which champions are from ionia")
    for champion, content, score in results:
        print(f"[{champion}] (score={score:.3f}) {content[:60]}")