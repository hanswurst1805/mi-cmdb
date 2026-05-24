from typing import List

from openai import OpenAI

from app.config import settings

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.openrouter_api_key,
            base_url="https://openrouter.ai/api/v1",
        )
    return _client


def embed_text(text: str) -> List[float]:
    response = _get_client().embeddings.create(
        model=settings.openrouter_embedding_model,
        input=text,
    )
    return response.data[0].embedding


def embed_query(query: str) -> List[float]:
    return embed_text(query)
