"""
RAG retriever module.

Provides a FAISS-backed `FAISSVectorStore` when FAISS is available,
and falls back to a dependency-free `SimpleVectorStore` otherwise.

Usage:
    from appshell.core.rag_service import get_default_store
    store = get_default_store()
    store.add('doc1', 'This is some text', {'title':'Doc 1'})
    results = store.search('some query', k=3)
"""
from typing import List, Dict, Any, Optional
import math
import re
import hashlib
import logging
try:
        import numpy as np
except Exception:
        np = None

try:
        import faiss
except Exception:
        faiss = None

logger = logging.getLogger(__name__)


def _tokenize(text: str) -> List[str]:
    text = text.lower()
    return [t for t in re.split(r"\W+", text) if t]


def _hash_vector(text: str, dim: int = 256) -> List[float]:
    tokens = _tokenize(text)
    vec = [0.0] * dim
    for tok in tokens:
        # stable hash via sha256
        h = int(hashlib.sha256(tok.encode('utf-8')).hexdigest(), 16)
        idx = h % dim
        vec[idx] += 1.0
    # normalize
    norm = math.sqrt(sum(v * v for v in vec))
    if norm == 0:
        return vec
    return [v / norm for v in vec]


class FAISSVectorStore:
    """FAISS-backed vector store using the same hashing embedding.

    Falls back to an in-memory index if faiss is not available.
    """

    def __init__(self, dim: int = 256):
        self.dim = dim
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._doc_to_id: Dict[str, int] = {}
        self._id_to_doc: Dict[int, str] = {}
        self._next_id = 1

        if faiss and np is not None:
            self._index = faiss.IndexIDMap(faiss.IndexFlatIP(dim))
            logger.info("FAISS index initialized")
        else:
            self._index = None
            logger.warning("FAISS not available — FAISSVectorStore will use an in-memory fallback")

    def add(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        vec = _hash_vector(text, self.dim)
        self._docs[doc_id] = {'text': text, 'metadata': metadata or {}}
        assigned_id = self._next_id
        self._doc_to_id[doc_id] = assigned_id
        self._id_to_doc[assigned_id] = doc_id
        self._next_id += 1

        if self._index is not None and np is not None:
            arr = np.array([vec], dtype='float32')
            self._index.add_with_ids(arr, np.array([assigned_id], dtype='int64'))

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        qv = _hash_vector(query, self.dim)
        results: List[Dict[str, Any]] = []
        if self._index is not None and np is not None:
            arr = np.array([qv], dtype='float32')
            D, I = self._index.search(arr, k)
            for score, idx in zip(D[0].tolist(), I[0].tolist()):
                if idx == -1:
                    continue
                doc_id = self._id_to_doc.get(int(idx))
                entry = self._docs.get(doc_id, {})
                results.append({
                    'doc_id': doc_id,
                    'score': float(score),
                    'text': entry.get('text', ''),
                    'metadata': entry.get('metadata', {}),
                })
            return results
        else:
            # Fallback to brute-force search
            scores = []
            for doc_id, entry in self._docs.items():
                vec = _hash_vector(entry.get('text', ''), self.dim)
                score = sum(x * y for x, y in zip(qv, vec))
                scores.append((score, doc_id))
            scores.sort(reverse=True, key=lambda x: x[0])
            for score, doc_id in scores[:k]:
                entry = self._docs.get(doc_id, {})
                results.append({
                    'doc_id': doc_id,
                    'score': float(score),
                    'text': entry.get('text', ''),
                    'metadata': entry.get('metadata', {}),
                })
            return results


class SimpleVectorStore:
    def __init__(self, dim: int = 256):
        self.dim = dim
        self._docs: Dict[str, Dict[str, Any]] = {}
        self._vectors: Dict[str, List[float]] = {}

    def add(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """Add a document to the store."""
        vec = _hash_vector(text, self.dim)
        self._docs[doc_id] = {'text': text, 'metadata': metadata or {}}
        self._vectors[doc_id] = vec

    def _cosine(self, a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Return top-k documents matching the query as a list of dicts with score."""
        qv = _hash_vector(query, self.dim)
        scores = []
        for doc_id, vec in self._vectors.items():
            score = self._cosine(qv, vec)
            scores.append((score, doc_id))
        scores.sort(reverse=True, key=lambda x: x[0])
        results = []
        for score, doc_id in scores[:k]:
            entry = self._docs.get(doc_id, {})
            results.append({
                'doc_id': doc_id,
                'score': float(score),
                'text': entry.get('text', ''),
                'metadata': entry.get('metadata', {}),
            })
        return results


__all__ = ["SimpleVectorStore"]


_DEFAULT_STORE: Optional[object] = None


def get_default_store() -> object:
    """Return a singleton vector store (FAISS if available, else simple fallback)."""
    global _DEFAULT_STORE
    if _DEFAULT_STORE is None:
        if faiss and np is not None:
            _DEFAULT_STORE = FAISSVectorStore(dim=256)
        else:
            _DEFAULT_STORE = SimpleVectorStore(dim=256)
    return _DEFAULT_STORE
