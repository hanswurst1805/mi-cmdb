from typing import List

import voyageai

from app.config import settings

_client: voyageai.Client | None = None


def _get_client() -> voyageai.Client:
    global _client
    if _client is None:
        _client = voyageai.Client(api_key=settings.voyage_api_key)
    return _client


def embed_text(text: str) -> List[float]:
    client = _get_client()
    result = client.embed([text], model="voyage-2", input_type="document")
    return result.embeddings[0]


def embed_query(query: str) -> List[float]:
    client = _get_client()
    result = client.embed([query], model="voyage-2", input_type="query")
    return result.embeddings[0]
