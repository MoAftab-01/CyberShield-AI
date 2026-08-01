import numpy as np

from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.bm25_store import BM25Store


class HybridRetriever:

    @staticmethod
    def search(
        query: str,
        top_k: int = 5,
    ):

        # -------------------------
        # Load Indexes
        # -------------------------

        faiss_index, documents = FAISSStore.load()

        bm25 = BM25Store.load()

        # -------------------------
        # FAISS Search
        # -------------------------

        query_vector = EmbeddingService.embed_query(
            query
        )

        query_vector = np.asarray(
            [query_vector],
            dtype="float32",
        )

        _, faiss_indices = faiss_index.search(
            query_vector,
            top_k,
        )

        # -------------------------
        # BM25 Search
        # -------------------------

        bm25_scores = bm25.get_scores(
            query.split()
        )

        bm25_indices = np.argsort(
            bm25_scores
        )[::-1][:top_k]

        # -------------------------
        # Merge Results
        # -------------------------

        combined = []

        seen = set()

        for idx in list(faiss_indices[0]) + list(bm25_indices):

            if idx in seen:
                continue

            seen.add(idx)

            combined.append(
                documents[idx]
            )

        return combined[:top_k]