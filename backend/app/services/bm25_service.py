import re
import logging
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi

logger = logging.getLogger("backend.services.bm25_service")

class BM25Document:
    def __init__(self, doc_id: str, content: str, payload: Optional[Dict[str, Any]] = None):
        self.doc_id = doc_id
        self.content = content
        self.payload = payload or {}

class BM25TenantIndex:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.documents: List[BM25Document] = []
        self.bm25_model: Optional[BM25Okapi] = None

    def tokenize(self, text: str) -> List[str]:
        """Normalize and tokenize text for sparse keyword search."""
        return re.findall(r"\b\w+\b", text.lower())

    def update_index(self, documents: List[BM25Document]):
        self.documents = documents
        if not self.documents:
            self.bm25_model = None
            return

        corpus = [self.tokenize(doc.content) for doc in self.documents]
        self.bm25_model = BM25Okapi(corpus)

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        if not self.bm25_model or not self.documents:
            return []

        tokenized_query = self.tokenize(query)
        if not tokenized_query:
            return []

        scores = self.bm25_model.get_scores(tokenized_query)
        scored_docs = list(zip(self.documents, scores))
        # Filter out completely irrelevant docs (score == 0) and sort descending
        relevant = [item for item in scored_docs if item[1] > 0.0]
        relevant.sort(key=lambda x: x[1], reverse=True)

        return [
            {
                "id": doc.doc_id,
                "score": float(score),
                "content": doc.content,
                "payload": doc.payload
            }
            for doc, score in relevant[:top_k]
        ]

class BM25Service:
    """Manages isolated in-memory sparse keyword search indices per tenant."""

    def __init__(self):
        self._tenant_indices: Dict[str, BM25TenantIndex] = {}

    def _get_tenant_index(self, tenant_id: str) -> BM25TenantIndex:
        if not tenant_id or not str(tenant_id).strip():
            raise ValueError("tenant_id is strictly required for BM25 operations.")
        tenant_id = str(tenant_id).strip()
        if tenant_id not in self._tenant_indices:
            self._tenant_indices[tenant_id] = BM25TenantIndex(tenant_id)
        return self._tenant_indices[tenant_id]

    def index_documents(self, tenant_id: str, documents: List[Dict[str, Any]]):
        """Index a list of documents for a specific tenant.
        Each doc dict must contain 'id' and 'content', plus optional 'payload'.
        """
        idx = self._get_tenant_index(tenant_id)
        parsed_docs = [
            BM25Document(
                doc_id=d["id"],
                content=d["content"],
                payload=d.get("payload", {})
            )
            for d in documents
        ]
        idx.update_index(parsed_docs)
        logger.info(f"BM25 index updated for tenant '{tenant_id}' with {len(parsed_docs)} documents.")

    def search(self, tenant_id: str, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Search tenant sparse index with BM25."""
        idx = self._get_tenant_index(tenant_id)
        return idx.search(query=query, top_k=top_k)

# Global singleton
bm25_service = BM25Service()
