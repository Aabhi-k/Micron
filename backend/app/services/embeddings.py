import os
import asyncio
import logging
import hashlib
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.observability import observe

logger = logging.getLogger("backend.services.embeddings")

class EmbeddingService:
    """Provides async embeddings via OpenAI with automatic fallback to sentence-transformers."""

    def __init__(self):
        self._st_model = None
        self._openai_client = None

    def _get_openai_client(self):
        if self._openai_client is None and settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-placeholder") and not settings.OPENAI_API_KEY.startswith("dummy"):
            try:
                try:
                    from langfuse.openai import AsyncOpenAI
                except ImportError:
                    from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize AsyncOpenAI: {e}")
                self._openai_client = None
        return self._openai_client

    def _get_sentence_transformer(self):
        if self._st_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading local fallback embedding model: {settings.FALLBACK_EMBEDDING_MODEL}")
                self._st_model = SentenceTransformer(settings.FALLBACK_EMBEDDING_MODEL)
            except Exception as e:
                logger.warning(f"Could not load SentenceTransformer '{settings.FALLBACK_EMBEDDING_MODEL}': {e}")
                self._st_model = None
        return self._st_model

    def _hash_mock_vector(self, text: str, dimension: int = 1536) -> List[float]:
        """Deterministic pseudo-embedding fallback for environments without network/model weights."""
        vector = []
        salt = text.encode("utf-8")
        for i in range(dimension):
            h = hashlib.sha256(salt + f":{i}".encode("utf-8")).digest()
            val = (int.from_bytes(h[:4], "big") / 0xFFFFFFFF) * 2.0 - 1.0
            vector.append(float(val))
        # Normalize
        norm = sum(x * x for x in vector) ** 0.5 or 1.0
        return [x / norm for x in vector]

    @observe(name="generate_embedding", as_type="embedding")
    async def get_embedding(self, text: str) -> Tuple[List[float], int]:
        """Generates a dense embedding vector for the provided text, returning (vector, dimension)."""
        vectors, dim = await self.get_embeddings([text])
        return vectors[0], dim

    @observe(name="generate_embeddings_batch", as_type="embedding")
    async def get_embeddings(self, texts: List[str]) -> Tuple[List[List[float]], int]:
        """Generates dense embeddings for a batch of texts."""
        if not texts:
            return [], 1536

        client = self._get_openai_client()
        if client is not None:
            try:
                response = await client.embeddings.create(
                    input=texts,
                    model=settings.OPENAI_EMBEDDING_MODEL
                )
                embeddings = [data.embedding for data in response.data]
                dim = len(embeddings[0]) if embeddings else 1536
                return embeddings, dim
            except Exception as e:
                logger.warning(f"OpenAI embedding generation failed ({e}). Falling back to local SentenceTransformer...")

        # Local SentenceTransformer Fallback
        st = self._get_sentence_transformer()
        if st is not None:
            try:
                def _encode():
                    arr = st.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
                    return arr.tolist()

                embeddings = await asyncio.to_thread(_encode)
                dim = len(embeddings[0]) if embeddings else 384
                return embeddings, dim
            except Exception as e:
                logger.warning(f"SentenceTransformer encoding failed: {e}. Using deterministic fallback.")

        # Deterministic fallback
        dim = 1536 if (settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("sk-placeholder")) else 384
        logger.info(f"Using deterministic fallback embedding generator (dim={dim})")
        return [self._hash_mock_vector(t, dim) for t in texts], dim

embedding_service = EmbeddingService()
