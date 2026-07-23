from foundry_local_sdk import Configuration, FoundryLocalManager
from config import CHAT_MODEL
from retrieval import get_top_chunks

_manager = None
_chat_model = None
_chat_client = None

SYSTEM_PROMPT = """You are a League of Legends assistant that answers questions about champions.
Only use the information provided in the context below to answer.
If the answer is not in the context, say you don't know — do not make anything up.
Keep answers concise and mention which champion the info is about."""


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


def answer_query(user_question: str, top_k: int = 3) -> str:
    top_chunks = get_top_chunks(user_question, top_k=top_k)
    context = "\n\n".join(f"[{champion}]\n{content}" for champion, content, score in top_chunks)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {user_question}"},
    ]

    client = _get_chat_client()
    response = client.complete_chat(messages)
    return response.choices[0].message.content


if __name__ == "__main__":
    answer = answer_query("What is Garen's ultimate ability?")
    print(answer)