import math
from database import get_all_chunks
from embedding import embed_text


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def get_top_chunks(query: str, top_k: int = 3):
    """Returns top_k most relevant (champion, content, score) tuples for the query."""
    query_vec = embed_text(query)
    rows = get_all_chunks()  # (id, champion, source_file, content, embedding)

    scored = []
    for _id, champion, source_file, content, embedding in rows:
        score = cosine_similarity(query_vec, embedding)
        scored.append((champion, content, score))

    scored.sort(key=lambda x: x[2], reverse=True)
    return scored[:top_k]


if __name__ == "__main__":
    results = get_top_chunks("What is Garen's ultimate ability?")
    for champion, content, score in results:
        print(f"[{champion}] (score={score:.3f})\n{content}\n")