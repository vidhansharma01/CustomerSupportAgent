from __future__ import annotations

import openai
from openai import AsyncOpenAI

from backend.config import settings


class EmbeddingService:
    """Wraps OpenAI embeddings API for single and batch text embedding."""

    def __init__(self) -> None:
        self._client = AsyncOpenAI(api_key=settings.openai_api_key)
        self._model = settings.openai_embedding_model

    async def embed_text(self, text: str) -> list[float]:
        """Embed a single text string; returns a 1536-dim float vector."""
        text = text.replace("\n", " ").strip()
        response = await self._client.embeddings.create(
            input=[text],
            model=self._model,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts in a single API call; returns parallel list of vectors."""
        cleaned = [t.replace("\n", " ").strip() for t in texts]
        response = await self._client.embeddings.create(
            input=cleaned,
            model=self._model,
        )
        # Preserve order
        ordered = sorted(response.data, key=lambda d: d.index)
        return [item.embedding for item in ordered]


# Module-level singleton
embedding_service = EmbeddingService()
