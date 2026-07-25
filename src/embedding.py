from foundry_local_sdk import Configuration, FoundryLocalManager
from config import EMBEDDING_MODEL

_manager = None
_model = None
_client = None


def _get_client():
    """Lazily initialize Foundry Local and return an embedding client for EMBEDDING_MODEL."""
    global _manager, _model, _client
    if _client is None:
        if FoundryLocalManager.instance is not None:
            _manager = FoundryLocalManager.instance
        else:
            config = Configuration(app_name="LoLGPT")
            _manager = FoundryLocalManager(config)

        _model = _manager.catalog.get_model(EMBEDDING_MODEL)
        if not _model.is_cached:
            _model.download()
        if not _model.is_loaded:
            _model.load()

        _client = _model.get_embedding_client()
    return _client


def embed_text(text: str) -> list[float]:
    client = _get_client()
    response = client.generate_embedding(text)
    return response.data[0].embedding


def embed_batch(texts: list[str]) -> list[list[float]]:
    client = _get_client()
    response = client.generate_embeddings(texts)
    return [item.embedding for item in response.data]