import re
from foundry_local_sdk import Configuration, FoundryLocalManager
from config import CHAT_MODEL
from retrieval import get_top_chunks, find_mentioned_champions, find_mentioned_regions, find_mentioned_roles, fuzzy_find_champions
from database import (
    get_chunks_by_role,
    get_chunks_by_region,
    get_chunks_by_lane,
    get_champion_display_names,
    get_distinct_champions,
    get_champion_full_text,
    get_champion_metadata,
)
from abilities import find_mentioned_ability_letter, extract_ability_line
from regions import find_mentioned_regions, fuzzy_find_regions
from roles import find_mentioned_roles, fuzzy_find_roles
from lanes import find_mentioned_lanes, fuzzy_find_lanes

_manager = None
_chat_model = None
_chat_client = None

SYSTEM_PROMPT = """You are a League of Legends assistant that answers questions about champions.
Only use the information provided in the context below to answer.
If the answer is not in the context, say you don't know — do not make anything up.
Keep answers concise and mention which champion the info is about.

Important rules:
1. Each ability in the context is explicitly labeled as "Passive", "Q", "W", "E", or "R" followed
   by a dash and the ability name (e.g. "E - Spell Shield: ..."). When asked about a specific
   ability letter, find the exact line starting with that letter and use ONLY that line. Double
   check the letter before answering — do not substitute a different ability of the same champion.
2. If the question asks to list or name champions matching a category (e.g. a role, region, or
   trait), list EVERY champion from the context that matches — not just the first one you notice.
   Go through the context entry by entry before answering."""

LISTING_WORDS = ["champion", "champs", "character", "who", "which", "list", "name all"]

ATTRIBUTE_PATTERNS = {
    "lane": r"\blane\b",
    "region": r"\bregion\b|\bwhere.*from\b",
    "role": r"\brole\b",
}


def _get_chat_client():
    global _manager, _chat_model, _chat_client
    if _chat_client is None:
        if FoundryLocalManager.instance is not None:
            _manager = FoundryLocalManager.instance
        else:
            config = Configuration(app_name="LoLGPT")
            _manager = FoundryLocalManager(config)

        _chat_model = _manager.catalog.get_model(CHAT_MODEL)
        if not _chat_model.is_cached:
            _chat_model.download()
        if not _chat_model.is_loaded:
            _chat_model.load()

        _chat_client = _chat_model.get_chat_client()
    return _chat_client


def is_listing_query(query: str, mentioned_champions: list, mentioned_roles: list,
                      mentioned_regions: list, mentioned_lanes: list) -> bool:
    if mentioned_champions:
        return False
    # Champion adı geçmiyor ama role/region/lane kesin eşleşmesi varsa,
    # bu zaten yeterince net bir listeleme sinyalidir — ayrıca listeleme
    # kelimesi (champion/champs/list vb.) aramaya gerek yok.
    return bool(mentioned_roles or mentioned_regions or mentioned_lanes)

def answer_listing_query(mentioned_roles: list, mentioned_regions: list, mentioned_lanes: list) -> str:
    display_names = get_champion_display_names()
    matched_ids = set()

    for role in mentioned_roles:
        for _id, champion, source_file, content, embedding in get_chunks_by_role(role):
            matched_ids.add(champion)

    for region in mentioned_regions:
        for _id, champion, source_file, content, embedding in get_chunks_by_region(region):
            matched_ids.add(champion)

    for lane in mentioned_lanes:
        for _id, champion, source_file, content, embedding in get_chunks_by_lane(lane):
            matched_ids.add(champion)

    names = sorted(display_names.get(champ, champ) for champ in matched_ids)

    label_parts = []
    if mentioned_roles:
        label_parts.append(" / ".join(mentioned_roles))
    if mentioned_regions:
        label_parts.append(" / ".join(mentioned_regions))
    if mentioned_lanes:
        label_parts.append(" / ".join(mentioned_lanes))
    label = " + ".join(label_parts)

    if not names:
        return f"{label} kriterine uyan şampiyon bulunamadı."

    champion_list = "\n".join(f"- {name}" for name in names)
    return f"{label} ({len(names)} champion):\n{champion_list}"


def find_mentioned_attribute(query: str) -> str | None:
    query_lower = query.lower()
    for attr, pattern in ATTRIBUTE_PATTERNS.items():
        if re.search(pattern, query_lower):
            return attr
    return None


def answer_query(user_question: str, top_k: int = 8) -> str:
    all_champions = get_distinct_champions()
    mentioned_champions = find_mentioned_champions(user_question, all_champions)
    if not mentioned_champions:
        mentioned_champions = fuzzy_find_champions(user_question)
    mentioned_roles = find_mentioned_roles(user_question)
    if not mentioned_roles:
        mentioned_roles = fuzzy_find_roles(user_question)

    mentioned_regions = find_mentioned_regions(user_question)
    if not mentioned_regions:
        mentioned_regions = fuzzy_find_regions(user_question)

    mentioned_lanes = find_mentioned_lanes(user_question)
    if not mentioned_lanes:
        mentioned_lanes = fuzzy_find_lanes(user_question)

    # 1) Listeleme sorgusu mu? (örn. "top laner champions", "mage champs")
    if is_listing_query(user_question, mentioned_champions, mentioned_roles, mentioned_regions, mentioned_lanes):
        return answer_listing_query(mentioned_roles, mentioned_regions, mentioned_lanes)

    # 2) Tek şampiyon + belirli bir ability harfi mi soruluyor? (örn. "yasuo q")
    if len(mentioned_champions) == 1:
        letter = find_mentioned_ability_letter(user_question)
        if letter:
            full_text = get_champion_full_text(mentioned_champions[0])
            line = extract_ability_line(full_text, letter)
            if line:
                display_names = get_champion_display_names()
                name = display_names.get(mentioned_champions[0], mentioned_champions[0])
                return f"[{name}] {line}"

    # 3) Tek şampiyon + lane/region/role gibi yapısal bir öznitelik mi soruluyor? (örn. "veigar lane")
    if len(mentioned_champions) == 1:
        attribute = find_mentioned_attribute(user_question)
        if attribute:
            metadata = get_champion_metadata(mentioned_champions[0])
            if metadata:
                display_names = get_champion_display_names()
                name = display_names.get(mentioned_champions[0], mentioned_champions[0])
                return f"[{name}] {attribute.capitalize()}: {metadata[attribute]}"

    # 4) Diğer her şey için: semantic retrieval + LLM
    top_chunks = get_top_chunks(user_question, top_k=top_k)

    context_parts = []
    for i, (champion, content, score) in enumerate(top_chunks, 1):
        context_parts.append(f"--- Entry {i}: {champion} ---\n{content}")
    context = "\n\n".join(context_parts)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context ({len(top_chunks)} entries):\n{context}\n\nQuestion: {user_question}"},
    ]

    client = _get_chat_client()
    response = client.complete_chat(messages)
    return response.choices[0].message.content


if __name__ == "__main__":
    answer = answer_query("What is Garen's ultimate ability?")
    print(answer)