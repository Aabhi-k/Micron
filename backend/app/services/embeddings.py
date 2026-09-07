import logging
from typing import List, Optional, Tuple
from app.core.config import settings
from app.core.observability import observe

logger = logging.getLogger("backend.services.embeddings")

class EmbeddingService:
    """Manages dense vector generation via OpenAI with sentence-transformers fallback."""

    def __init__(self):
        self._openai_client = None
        self._local_model = None
        self._dimension: Optional[int] = None

    def _get_openai_client(self):
        if self._openai_client is None and settings.OPENAI_API_KEY and not settings.OPENAI_API_KEY.startswith("dummy") and not settings.OPENAI_API_KEY.startswith("sk-placeholder"):
            try:
                from openai import AsyncOpenAI
                self._openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI client for embeddings: {e}")
        return self._openai_client

    def _get_local_model(self):
        if self._local_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                logger.info(f"Loading fallback embedding model: {settings.FALLBACK_EMBEDDING_MODEL}")
                self._local_model = SentenceTransformer(settings.FALLBACK_EMBEDDING_MODEL)
            except Exception as e:
                logger.error(f"Failed to load fallback SentenceTransformer model: {e}")
                raise RuntimeError("No embedding provider is available.") from e
        return self._local_model

    @property
    def dimension(self) -> int:
        if self._dimension is None:
            if self._get_openai_client() is not None:
                self._dimension = 1536  # text-embedding-3-small dimension
            else:
                self._dimension = 384   # all-MiniLM-L6-v2 dimension
        return self._dimension

    async def embed_query(self, text: str) -> List[float]:
        """Generate embedding vector for a single search query."""
        results = await self.embed_documents([text])
        return results[0] if results else [0.0] * self.dimension

    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a batch of text chunks."""
        if not texts:
            return []

        openai_client = self._get_openai_client()
        if openai_client is not None:
            try:
                response = await openai_client.embeddings.create(
                    input=texts,
                    model=settings.OPENAI_EMBEDDING_MODEL
                )
                self._dimension = 1536
                return [data.embedding for data in response.data]
            except Exception as e:
                logger.warning(f"OpenAI embedding call failed ({e}), falling back to local sentence-transformer.")

        # Local sentence-transformers fallback
        local_model = self._get_local_model()
        embeddings = local_model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        self._dimension = 384
        return [vec.tolist() for vec in embeddings]

    @observe(name="get_embedding", as_type="embedding")
    async def get_embedding(self, text: str) -> Tuple[List[float], int]:
        """Generate embedding and return (vector, dimension) tuple for compatibility."""
        vec = await self.embed_query(text)
        return vec, self.dimension

    @observe(name="get_embeddings", as_type="embedding")
    async def get_embeddings(self, texts: List[str]) -> Tuple[List[List[float]], int]:
        """Generate embeddings for multiple texts and return (vectors, dimension) tuple."""
        vecs = await self.embed_documents(texts)
        return vecs, self.dimension

# Global singleton
embedding_service = EmbeddingService()
