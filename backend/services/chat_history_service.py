"""
Pinecone-backed chat history service.

Stores conversation messages as vector embeddings in Pinecone for:
1. Semantic retrieval of relevant past conversations
2. Persistent, searchable chat history per user
"""

import logging
import httpx
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime, timezone

from pinecone import Pinecone

from backend.core.config import settings

logger = logging.getLogger(__name__)

# ── Singleton Pinecone index ──────────────────────────────────────────
_pc: Optional[Pinecone] = None
_index = None


def _get_pinecone_index():
    """Lazy-init the Pinecone index singleton."""
    global _pc, _index
    if _index is None:
        if not settings.PINECONE_API_KEY:
            logger.warning("PINECONE_API_KEY not set — chat history will not be persisted to Pinecone.")
            return None
        _pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        _index = _pc.Index(settings.PINECONE_INDEX_NAME)
        logger.info(f"Pinecone index '{settings.PINECONE_INDEX_NAME}' initialised.")
    return _index


# ── Embedding helper ─────────────────────────────────────────────────

async def _get_embedding(text: str) -> List[float]:
    """Generate an embedding vector using Ollama's embedding endpoint."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            "http://localhost:11434/api/embed",
            json={
                "model": settings.EMBEDDING_MODEL,
                "input": text,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        # Ollama /api/embed returns {"embeddings": [[...], ...]}
        return data["embeddings"][0]


# ── Public API ────────────────────────────────────────────────────────

class ChatHistoryService:
    """Manages chat message persistence in Pinecone."""

    def __init__(self):
        """  init  ."""
        self.index = _get_pinecone_index()

    # ─── Write ────────────────────────────────────────────────────────

    async def store_message(
        self,
        message_id: str,
        user_id: str,
        conversation_id: str,
        role: str,
        text: str,
        metadata_extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Embed and upsert a single message into Pinecone."""
        if self.index is None:
            return

        try:
            embedding = await _get_embedding(text)

            meta: Dict[str, Any] = {
                "user_id": str(user_id),
                "conversation_id": str(conversation_id),
                "role": role,
                "text": text[:1000],  # Pinecone metadata limit ≈ 40 KB
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            if metadata_extra:
                meta.update(metadata_extra)

            self.index.upsert(
                vectors=[
                    {
                        "id": str(message_id),
                        "values": embedding,
                        "metadata": meta,
                    }
                ],
                namespace=f"user_{user_id}",
            )
        except Exception as e:
            # Never let Pinecone failures break the chat flow
            logger.error(f"Pinecone upsert failed: {e}")

    # ─── Read: by conversation ────────────────────────────────────────

    async def get_conversation_messages(
        self,
        user_id: str,
        conversation_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Fetch all messages for a specific conversation from Pinecone,
        sorted chronologically.
        """
        if self.index is None:
            return []

        try:
            # Use a zero vector to list by metadata filter.
            # Pinecone requires a query vector even for filtered queries,
            # so we use a dummy vector and rely on the metadata filter.
            dummy_vector = [0.0] * 1024
            results = self.index.query(
                vector=dummy_vector,
                top_k=limit,
                namespace=f"user_{user_id}",
                filter={
                    "conversation_id": {"$eq": str(conversation_id)},
                },
                include_metadata=True,
            )
            messages = []
            for match in results.get("matches", []):
                meta = match.get("metadata", {})
                messages.append({
                    "id": match["id"],
                    "role": meta.get("role", "unknown"),
                    "content": meta.get("text", ""),
                    "timestamp": meta.get("timestamp", ""),
                    "conversation_id": meta.get("conversation_id", ""),
                })
            # Sort chronologically
            messages.sort(key=lambda m: m.get("timestamp", ""))
            return messages
        except Exception as e:
            logger.error(f"Pinecone query failed: {e}")
            return []

    # ─── Read: semantic search ────────────────────────────────────────

    async def search_chat_history(
        self,
        user_id: str,
        query: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Semantically search a user's entire chat history.
        Returns the most relevant past messages.
        """
        if self.index is None:
            return []

        try:
            query_embedding = await _get_embedding(query)
            results = self.index.query(
                vector=query_embedding,
                top_k=limit,
                namespace=f"user_{user_id}",
                include_metadata=True,
            )
            return [
                {
                    "id": m["id"],
                    "role": m["metadata"].get("role", "unknown"),
                    "content": m["metadata"].get("text", ""),
                    "conversation_id": m["metadata"].get("conversation_id", ""),
                    "timestamp": m["metadata"].get("timestamp", ""),
                    "score": m.get("score", 0),
                }
                for m in results.get("matches", [])
            ]
        except Exception as e:
            logger.error(f"Pinecone semantic search failed: {e}")
            return []
