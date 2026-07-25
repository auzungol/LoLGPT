from foundry_local_sdk import Configuration, FoundryLocalManager
from config import CHAT_MODEL
from retrieval import get_top_chunks

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


def answer_query(user_question: str, top_k: int = 8) -> str:
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