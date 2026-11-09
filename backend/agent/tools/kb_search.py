"""Knowledge-base search tool.

Hybrid retrieval strategy:
  1. Semantic search  — Pinecone cosine similarity on OpenAI embeddings.
  2. Full-text search — Postgres ts_vector / plainto_tsquery on raw content.
  3. Merge & deduplicate by document title, keeping top-5 by score.

Document metadata (title, content, category) is stored in Pinecone's vector
metadata, so semantic results require no Postgres round-trip.
Full-text results fetch from Postgres (which holds the canonical text).
"""
from __future__ import annotations

import logging
from typing import Any

from langchain_core.tools import tool
from sqlalchemy import text

from backend.database import AsyncSessionLocal
from backend.services.embedding import embedding_service
from backend.services.pinecone_service import pinecone_service

logger = logging.getLogger(__name__)


@tool
async def search_knowledge_base(query: str) -> str:
    """Search the company knowledge base for policies, procedures, FAQs, and product information.

    Uses hybrid retrieval: Pinecone semantic vector search combined with
    Postgres full-text search, results merged and ranked.

    Args:
        query: Natural-language search query string.

    Returns:
        Formatted string with the top relevant document titles and content snippets.
    """
    if not query or not query.strip():
        return "Please provide a search query."

    try:
        # ── 1. Semantic search via Pinecone ───────────────────────────────────
        embedding = await embedding_service.embed_text(query)

        pinecone_hits: list[dict[str, Any]] = pinecone_service.query(
            embedding=embedding,
            top_k=5,
            score_threshold=0.30,
        )
        logger.debug("Pinecone returned %d hits for query: %r", len(pinecone_hits), query)

        # ── 2. Full-text search via Postgres ──────────────────────────────────
        fts_hits: list[dict[str, Any]] = []
        try:
            async with AsyncSessionLocal() as session:
                fts_sql = text(
                    """
                    SELECT title, content, category,
                           ts_rank(
                               to_tsvector('english', content),
                               plainto_tsquery('english', :query)
                           ) AS rank
                    FROM documents
                    WHERE to_tsvector('english', content)
                          @@ plainto_tsquery('english', :query)
                    ORDER BY rank DESC
                    LIMIT 5
                    """
                )
                result = await session.execute(fts_sql, {"query": query})
                rows = result.fetchall()

            for row in rows:
                fts_hits.append(
                    {
                        "title": row.title,
                        "content": row.content,
                        "category": row.category,
                        "score": float(row.rank),
                    }
                )
            logger.debug("Postgres FTS returned %d hits.", len(fts_hits))

        except Exception as fts_exc:
            # FTS failure is non-fatal — Pinecone results alone are still useful.
            logger.warning("Postgres FTS failed (using Pinecone results only): %s", fts_exc)

        # ── 3. Merge & deduplicate by title ───────────────────────────────────
        # Pinecone hits take precedence (cosine score 0–1 is comparable to FTS rank).
        seen: dict[str, dict[str, Any]] = {}

        for hit in pinecone_hits:
            seen[hit["title"]] = hit

        for hit in fts_hits:
            title = hit["title"]
            if title not in seen or hit["score"] > seen[title]["score"]:
                seen[title] = hit

        merged = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:5]

        if not merged:
            return "No relevant documents found in the knowledge base for your query."

        # ── 4. Format response ────────────────────────────────────────────────
        lines: list[str] = ["=== Knowledge Base Results ==="]
        for i, doc in enumerate(merged, 1):
            snippet = doc["content"][:400].replace("\n", " ")
            lines.append(
                f"\n[{i}] {doc['title']} "
                f"(Category: {doc['category']}, Score: {doc['score']:.3f})"
            )
            lines.append(f"    {snippet}…")

        return "\n".join(lines)

    except Exception as exc:
        logger.exception("search_knowledge_base failed: %s", exc)
        return f"Knowledge base search encountered an error: {exc}"
