import re
import logging
from typing import List, Dict, Any, Optional
from app.db.tenant_guard import validate_tenant_id, TenantIsolationError

logger = logging.getLogger("backend.services.bm25")

def tokenize_text(text: str) -> List[str]:
    """Tokenizes alphanumeric words lowercased for BM25 ranking."""
    if not text:
        return []
    return re.findall(r"\b\w+\b", text.lower())

class BM25SearchService:
    """Provides sparse BM25 retrieval strictly scoped to a specific tenant."""

    def __init__(self):
        # In-memory index cache: { tenant_id: { "docs": [...], "bm25": BM25, "tokenized": [...] } }
        self._tenant_indices: Dict[str, Dict[str, Any]] = {}

    def update_tenant_index(self, tenant_id: str, documents: List[Dict[str, Any]]):
        """Builds or refreshes the BM25 index for a specific tenant."""
        clean_tenant_id = validate_tenant_id(tenant_id)

        # Ensure zero cross-tenant contamination in corpus
        tenant_docs = []
        for doc in documents:
            doc_tenant = doc.get("tenant_id")
            if doc_tenant and str(doc_tenant) != clean_tenant_id:
                raise TenantIsolationError(
                    f"Security Alert: Document {doc.get('id')} belongs to tenant {doc_tenant}, "
                    f"attempted to index under {clean_tenant_id}."
                )
            tenant_docs.append(doc)

        try:
            from rank_bm25 import BM25Plus, BM25Okapi
            tokenized_corpus = [
                tokenize_text(f"{d.get('title', '')} {d.get('content', '')}")
                for d in tenant_docs
            ]
            bm25 = BM25Plus(tokenized_corpus) if tokenized_corpus else None
            self._tenant_indices[clean_tenant_id] = {
                "docs": tenant_docs,
                "bm25": bm25,
                "tokenized": tokenized_corpus
            }
        except ImportError:
            logger.warning("rank-bm25 not installed; BM25 index caching disabled.")
            self._tenant_indices[clean_tenant_id] = {
                "docs": tenant_docs,
                "bm25": None,
                "tokenized": []
            }

    async def search(
        self,
        tenant_id: str,
        query: str,
        top_k: int = 10,
        project_id: Optional[str] = None,
        corpus_docs: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Executes sparse BM25 retrieval strictly isolated to the specified tenant.
        Under NO circumstance will documents outside this tenant be searched or returned.
        """
        clean_tenant_id = validate_tenant_id(tenant_id)

        # If explicit corpus_docs supplied, filter strictly
        if corpus_docs is not None:
            active_docs = [
                d for d in corpus_docs
                if str(d.get("tenant_id", clean_tenant_id)) == clean_tenant_id
                and (not project_id or not d.get("project_id") or str(d.get("project_id")) == str(project_id))
            ]
        else:
            cached = self._tenant_indices.get(clean_tenant_id)
            if not cached or not cached.get("docs"):
                return []
            active_docs = [
                d for d in cached["docs"]
                if not project_id or not d.get("project_id") or str(d.get("project_id")) == str(project_id)
            ]

        if not active_docs:
            return []

        tokenized_query = tokenize_text(query)
        if not tokenized_query:
            return []

        try:
            try:
                from rank_bm25 import BM25Plus as BM25Model
            except ImportError:
                from rank_bm25 import BM25Okapi as BM25Model

            tokenized_corpus = [
                tokenize_text(f"{d.get('title', '')} {d.get('content', '')}")
                for d in active_docs
            ]
            bm25 = BM25Model(tokenized_corpus)

            # Guard against negative IDF for small corpora in standard BM25
            if hasattr(bm25, "idf"):
                for term in bm25.idf:
                    if bm25.idf[term] < 0:
                        bm25.idf[term] = 0.25

            scores = bm25.get_scores(tokenized_query)
            query_set = set(tokenized_query)

            results = []
            for idx, score in enumerate(scores):
                doc_tokens = set(tokenized_corpus[idx])
                # Ensure the document actually matches at least one query term
                if query_set.intersection(doc_tokens) and score > 0:
                    doc = active_docs[idx]
                    results.append({
                        "doc_id": str(doc.get("id") or doc.get("doc_id")),
                        "score": float(score),
                        "title": doc.get("title", ""),
                        "content": doc.get("content", ""),
                        "project_id": doc.get("project_id"),
                        "metadata": doc.get("meta_info") or doc.get("metadata", {}),
                        "tenant_id": clean_tenant_id
                    })

            results.sort(key=lambda x: x["score"], reverse=True)
            return results[:top_k]

        except Exception as e:
            logger.warning(f"BM25 search execution error: {e}")
            return []

bm25_service = BM25SearchService()
