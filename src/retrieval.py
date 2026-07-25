import math
import re
from database import get_all_chunks, get_distinct_champions, get_chunks_by_champion, get_chunks_by_region, get_chunks_by_role
from embedding import embed_text
from regions import find_mentioned_regions
from roles import find_mentioned_roles


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def find_mentioned_champions(query: str, all_champions: list[str]) -> list[str]:
    query_lower = query.lower()
    mentioned = []
    for champ in all_champions:
        if re.search(rf"\b{re.escape(champ.lower())}\b", query_lower):
            mentioned.append(champ)
    return mentioned


def get_top_chunks(query: str, top_k: int = 8):
    all_champions = get_distinct_champions()
    mentioned_champions = find_mentioned_champions(query, all_champions)
    mentioned_regions = find_mentioned_regions(query)
    mentioned_roles = find_mentioned_roles(query)

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

    for role in mentioned_roles:
        seen_champions = set()
        for _id, champion, source_file, content, embedding in get_chunks_by_role(role):
            if champion in seen_champions or _id in included_ids:
                continue
            included_ids.add(_id)
            seen_champions.add(champion)
            results.append((champion, content, 1.0))

    # Context'in patlamaması için exact-match sonuçlarını da top_k ile sınırla
    if len(results) > top_k:
        results = results[:top_k]

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