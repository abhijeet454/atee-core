"""
FAISS Vector Store — local semantic search over memories.

Uses sentence-transformers for embeddings and FAISS for similarity search.
"""

from __future__ import annotations

import asyncio
import os
import pickle
import uuid
from pathlib import Path
from typing import List, Optional, Tuple

import faiss
import numpy as np
from loguru import logger
from sentence_transformers import SentenceTransformer

from app.core.config import settings


class VectorStore:
    """FAISS-backed vector store for semantic memory search."""

    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatIP] = None  # Inner product (cosine on normalized)
        self._documents: List[dict] = []  # Parallel list: {id, content, metadata}
        self._dimension: int = 0
        self._index_path = Path(settings.faiss_index_path)

    async def initialize(self) -> None:
        """Load the embedding model and existing index."""
        logger.info(f"Loading embedding model: {settings.embedding_model}")
        self._model = await asyncio.to_thread(
            SentenceTransformer, settings.embedding_model
        )
        self._dimension = self._model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self._dimension}")

        # Try to load existing index
        if self._load_from_disk():
            logger.info(f"Loaded FAISS index with {self._index.ntotal} vectors")
        else:
            self._index = faiss.IndexFlatIP(self._dimension)
            logger.info("Created new FAISS index")

    def _embed(self, texts: List[str]) -> np.ndarray:
        """Embed a list of texts and L2-normalize for cosine similarity."""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        # Normalize so inner product == cosine similarity
        faiss.normalize_L2(embeddings)
        return embeddings

    async def add(
        self,
        content: str,
        metadata: Optional[dict] = None,
        doc_id: Optional[str] = None,
    ) -> str:
        """Add a document to the vector store. Returns the document ID."""
        doc_id = doc_id or str(uuid.uuid4())
        embedding = await asyncio.to_thread(self._embed, [content])

        self._index.add(embedding)
        self._documents.append({
            "id": doc_id,
            "content": content,
            "metadata": metadata or {},
        })

        logger.debug(f"Added vector [{doc_id[:8]}...] — total: {self._index.ntotal}")
        return doc_id

    async def search(self, query: str, top_k: int = 5) -> List[Tuple[dict, float]]:
        """
        Search for similar documents.

        Returns:
            List of (document_dict, similarity_score) tuples, sorted by relevance.
        """
        if self._index.ntotal == 0:
            return []

        query_embedding = await asyncio.to_thread(self._embed, [query])
        k = min(top_k, self._index.ntotal)

        scores, indices = await asyncio.to_thread(
            self._index.search, query_embedding, k
        )

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self._documents) and idx >= 0:
                results.append((self._documents[idx], float(score)))

        return results

    async def delete(self, doc_id: str) -> bool:
        """
        Remove a document by ID.
        Note: FAISS doesn't support efficient deletion, so we rebuild the index.
        """
        target_idx = None
        for i, doc in enumerate(self._documents):
            if doc["id"] == doc_id:
                target_idx = i
                break

        if target_idx is None:
            return False

        self._documents.pop(target_idx)

        # Rebuild the index from remaining documents
        if self._documents:
            texts = [d["content"] for d in self._documents]
            embeddings = await asyncio.to_thread(self._embed, texts)
            self._index = faiss.IndexFlatIP(self._dimension)
            self._index.add(embeddings)
        else:
            self._index = faiss.IndexFlatIP(self._dimension)

        logger.debug(f"Deleted vector [{doc_id[:8]}...] — rebuilt index")
        return True

    async def save(self) -> None:
        """Persist index and documents to disk."""
        self._index_path.mkdir(parents=True, exist_ok=True)

        index_file = self._index_path / "index.faiss"
        docs_file = self._index_path / "documents.pkl"

        await asyncio.to_thread(faiss.write_index, self._index, str(index_file))
        with open(docs_file, "wb") as f:
            pickle.dump(self._documents, f)

        logger.info(f"Saved FAISS index ({self._index.ntotal} vectors) to {self._index_path}")

    def _load_from_disk(self) -> bool:
        """Load index and documents from disk. Returns True if successful."""
        index_file = self._index_path / "index.faiss"
        docs_file = self._index_path / "documents.pkl"

        if not index_file.exists() or not docs_file.exists():
            return False

        try:
            self._index = faiss.read_index(str(index_file))
            with open(docs_file, "rb") as f:
                self._documents = pickle.load(f)
            return True
        except Exception as e:
            logger.warning(f"Failed to load FAISS index: {e}")
            return False

    @property
    def count(self) -> int:
        return self._index.ntotal if self._index else 0
