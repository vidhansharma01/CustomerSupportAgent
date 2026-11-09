"""Pinecone vector store service.

Handles all interaction with Pinecone: upserting document embeddings and
querying for nearest neighbours.  Document metadata (title, content,
category) is stored as Pinecone vector metadata so a Postgres round-trip
is only needed for full-text search results.
"""
from __future__ import annotations

import logging
from typing import Any

from pinecone import Pinecone, ServerlessSpec

from backend.config import settings

logger = logging.getLogger(__name__)

# Pinecone embedding dimension must match the OpenAI model output.
# text-embedding-3-small  → 1536 dims
EMBEDDING_DIM = 1536


class PineconeService:
    """Thin async-friendly wrapper around the Pinecone Python SDK (v5+)."""

    def __init__(self) -> None:
        self._client = Pinecone(api_key=settings.pinecone_api_key)
        self._index_name = settings.pinecone_index_name
        self._namespace = settings.pinecone_namespace
        self._index = None  # lazy initialised

    # ------------------------------------------------------------------
    # Index management
    # ------------------------------------------------------------------

    def ensure_index(self) -> None:
        """Create the Pinecone index if it does not already exist.

        Uses the *Serverless* (free-tier) spec on AWS us-east-1.
        Call this once at application startup.
        """
        existing = [idx.name for idx in self._client.list_indexes()]
        if self._index_name not in existing:
            logger.info(
                "Creating Pinecone index '%s' (dim=%d, metric=cosine).",
                self._index_name,
                EMBEDDING_DIM,
            )
            self._client.create_index(
                name=self._index_name,
                dimension=EMBEDDING_DIM,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            logger.info("Pinecone index '%s' created.", self._index_name)
        else:
            logger.debug("Pinecone index '%s' already exists.", self._index_name)

        self._index = self._client.Index(self._index_name)

    @property
    def index(self):
        """Return the Pinecone Index object, initialising lazily if needed."""
        if self._index is None:
            self._index = self._client.Index(self._index_name)
        return self._index

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def upsert_document(
        self,
        doc_id: str,
        embedding: list[float],
        title: str,
        content: str,
        category: str,
    ) -> None:
        """Upsert a single document vector with metadata into Pinecone.

        Args:
            doc_id:    Unique identifier (UUID string) matching the Postgres row.
            embedding: 1536-dim float vector produced by OpenAI embeddings.
            title:     Document title stored as metadata for retrieval.
            content:   Full document text (truncated to 20 000 chars — Pinecone
                       metadata limit is 40 KB per vector).
            category:  Document category tag (policy / product / faq / procedure).
        """
        # Pinecone metadata values must be strings, numbers, booleans, or lists.
        # Truncate content to stay well inside the 40 KB metadata limit.
        self.index.upsert(
            vectors=[
                {
                    "id": doc_id,
                    "values": embedding,
                    "metadata": {
                        "title": title,
                        "content": content[:20_000],
                        "category": category,
                    },
                }
            ],
            namespace=self._namespace,
        )

    def upsert_batch(
        self,
        records: list[dict[str, Any]],
    ) -> None:
        """Batch-upsert multiple document vectors.

        Args:
            records: List of dicts, each with keys:
                     id, embedding, title, content, category.
        """
        vectors = [
            {
                "id": r["id"],
                "values": r["embedding"],
                "metadata": {
                    "title": r["title"],
                    "content": r["content"][:20_000],
                    "category": r["category"],
                },
            }
            for r in records
        ]
        # Pinecone recommends batches of ≤100 vectors.
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            self.index.upsert(
                vectors=vectors[i : i + batch_size],
                namespace=self._namespace,
            )
        logger.info("Upserted %d vectors to Pinecone.", len(vectors))

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(
        self,
        embedding: list[float],
        top_k: int = 5,
        score_threshold: float = 0.30,
    ) -> list[dict[str, Any]]:
        """Query Pinecone for the top-k most similar documents.

        Args:
            embedding:        Query vector (1536-dim).
            top_k:            Maximum number of results to return.
            score_threshold:  Minimum cosine similarity score (0–1) to include.

        Returns:
            List of dicts: {id, title, content, category, score}
            sorted by score descending.
        """
        response = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True,
            namespace=self._namespace,
        )

        results = []
        for match in response.matches:
            if match.score < score_threshold:
                continue
            meta = match.metadata or {}
            results.append(
                {
                    "id": match.id,
                    "title": meta.get("title", "Untitled"),
                    "content": meta.get("content", ""),
                    "category": meta.get("category", "unknown"),
                    "score": float(match.score),
                }
            )
        return results

    def delete_document(self, doc_id: str) -> None:
        """Remove a vector from Pinecone by document ID."""
        self.index.delete(ids=[doc_id], namespace=self._namespace)

    def index_stats(self) -> dict[str, Any]:
        """Return index statistics (vector count, dimension, etc.)."""
        return self.index.describe_index_stats()


# Module-level singleton — imported by tools and seeds.
pinecone_service = PineconeService()
