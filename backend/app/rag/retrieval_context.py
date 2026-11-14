"""Request-local indexes; no disk writes, shared caches, or model loading."""
from dataclasses import dataclass

import faiss
import numpy as np
from rank_bm25 import BM25Okapi

from app.rag.bm25_store import BM25Store
from app.rag.embeddings import EmbeddingService


@dataclass(frozen=True)
class RetrievalContext:
    documents: tuple
    index: object
    bm25: object

    @property
    def embedding_backend(self):
        return "hash"

    def embed_query(self, text):
        return EmbeddingService.hash_vectors([text])

    @classmethod
    def build(cls, documents):
        documents = tuple(documents)
        if not documents or len(documents) > 256:
            raise ValueError("A bounded nonempty corpus is required.")
        vectors = np.asarray(EmbeddingService.hash_vectors(
            [d.page_content for d in documents]), dtype="float32")
        index = faiss.IndexFlatL2(vectors.shape[1])
        index.add(vectors)
        bm25 = BM25Okapi([BM25Store.tokenize(d.page_content) for d in documents])
        return cls(documents, index, bm25)
