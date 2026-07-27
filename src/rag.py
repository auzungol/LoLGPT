import re
from foundry_local_sdk import Configuration, FoundryLocalManager
from config import CHAT_MODEL
from retrieval import get_top_chunks, find_mentioned_champions, fuzzy_find_champions
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
import difflib

ATTRIBUTE_PATTERNS = {
    "lane": r"\blane\b|\bkoridor\w*\b",
    "region": r"\bregion\b|\bwhere.*from\b|\bbölge\w*\b|\bnereli\w*\b",
    "role": r"\brole\b|\brol\w*\b",
    "resource": r"\bresource\w*\b|\bkaynak\w*\b|\bmana\b",
}

ATTRIBUTE_KEYWORDS = {
    "lane": ["lane", "koridor"],
    "region": ["region", "bölge", "nereli"],
    "role": ["role", "rol"],
    "resource": ["resource", "kaynak"],
}
ATTRIBUTE_LABELS_TR = {
    "lane": "Koridor",
    "region": "Bölge",
    "role": "Rol",
    "resource": "Kaynak",
}
_manager = None
_chat_model = None
_chat_client = None

SYSTEM_PROMPT = """Sen League of Legends şampiyonları hakkında soru cevaplayan bir asistansın.
SADECE aşağıda verilen bağlamdaki (context) bilgiyi kullan.
Eğer cevap bağlamda yoksa, "Bu bilgi elimde yok" de — kesinlikle uydurma, tahmin etme ya da
genel bilgiden yararlanma.

Önemli kurallar:
1. Bağlamdaki her yetenek "Passive", "Q", "W", "E" veya "R" etiketiyle başlar (örn. "E - Spell Shield: ...").
   Belirli bir harf sorulduğunda SADECE o harfle başlayan satırı bul ve kullan. Harfi doğrulamadan cevap verme.
2. Eğer soru bir kategoriye (rol, bölge, özellik) uyan şampiyonları listelemeyi istiyorsa, bağlamdaki
   HER şampiyonu listele, sadece ilk fark ettiğini değil.
3. Cevabını TAMAMEN Türkçe yaz. Bağlamdaki (context) bilgi İngilizce olsa bile, sen onu Türkçeye
   çevirerek açıkla. Şampiyon isimleri ve yetenek isimleri (örn. "Baleful Strike") İngilizce kalabilir,
   ama açıklama cümlelerinin TAMAMI Türkçe olmalı — tek bir İngilizce cümle bile yazma.

Örnek (bağlam İngilizce olsa bile cevap böyle olmalı):
Context: "Q - Baleful Strike: Veigar unleashes a bolt of dark energy that deals magic damage."
Soru: veigar q nedir
Doğru cevap: "[Veigar] Q - Baleful Strike: Veigar, ilk vurduğu düşmana büyü hasarı veren karanlık
enerjiden oluşan bir mermi fırlatır."
Yanlış cevap: "[Veigar] Q - Baleful Strike: Veigar unleashes a bolt of dark energy..." (İngilizce kaldığı için YANLIŞ)"""




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
    # bu zaten yeterince net bir listeleme sinyalidir.
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

    query_words = re.findall(r"[a-zA-ZğüşıöçĞÜŞİÖÇ]{4,}", query_lower)
    for attr, keywords in ATTRIBUTE_KEYWORDS.items():
        for kw in keywords:
            for word in query_words:
                if difflib.get_close_matches(word, [kw], n=1, cutoff=0.8):
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

    # 1) Listeleme sorgusu mu? (örn. "top laner champions", "mage champs", "orman şampiyonları")
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
                value = metadata[attribute]
                if value == "None":
                    value = "Yok (kaynak kullanmıyor)"
                return f"[{name}] {ATTRIBUTE_LABELS_TR[attribute]}: {value}"
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
    try:
        response = client.complete_chat(messages)
    except Exception as e:
        # Geçici bellek baskısı/iptal durumunda bir kez daha dene
        import time
        time.sleep(2)
        try:
            response = client.complete_chat(messages)
        except Exception as e2:
            return f"(Model şu anda cevap veremedi, lütfen tekrar deneyin. Hata: {e2})"
    return response.choices[0].message.content

if __name__ == "__main__":
    answer = answer_query("What is Garen's ultimate ability?")
    print(answer)