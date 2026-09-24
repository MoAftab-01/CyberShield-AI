import numpy as np

from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.bm25_store import BM25Store


class HybridRetriever:

    @staticmethod
    def search_with_metrics(
        query: str,
        top_k: int = 5,
    ):
        index_files = (
            FAISSStore.INDEX_PATH,
            FAISSStore.META_PATH,
            BM25Store.INDEX_PATH,
            BM25Store.DOCS_PATH,
        )
        if not all(path.exists() for path in index_files):
            return [], {
                "status": "empty",
                "reason": "No RAG index has been built yet.",
                "retrieved_count": 0,
            }

        faiss_index, documents = FAISSStore.load()
        bm25 = BM25Store.load()
        candidate_count = min(len(documents), max(top_k * 4, 10))

        query_vector = np.asarray(
            EmbeddingService.embed_query(query),
            dtype="float32",
        )
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        _, faiss_indices = faiss_index.search(
            query_vector,
            candidate_count,
        )
        bm25_scores = bm25.get_scores(
            BM25Store.tokenize(query)
        )
        bm25_indices = np.argsort(bm25_scores)[::-1][:candidate_count]

        # Reciprocal Rank Fusion makes lexical and semantic evidence contribute
        # equally without comparing scores from different scales.
        ranks: dict[int, float] = {}
        vector_rank: dict[int, int] = {}
        lexical_rank: dict[int, int] = {}
        for rank, index in enumerate(faiss_indices[0], start=1):
            index = int(index)
            if index >= 0:
                vector_rank[index] = rank
                ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)
        for rank, index in enumerate(bm25_indices, start=1):
            index = int(index)
            lexical_rank[index] = rank
            ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)

        selected_indices = sorted(
            ranks,
            key=lambda index: ranks[index],
            reverse=True,
        )[:top_k]
        results = [documents[index] for index in selected_indices]
        for index, document in zip(selected_indices, results):
            document.metadata["retrieval_score"] = round(ranks[index], 6)
            document.metadata["vector_rank"] = vector_rank.get(index)
            document.metadata["lexical_rank"] = lexical_rank.get(index)

        return results, {
            "status": "ok",
            "retrieved_count": len(results),
            "candidate_count": candidate_count,
            "vector_candidates": len(vector_rank),
            "lexical_candidates": len(lexical_rank),
            "fusion": "reciprocal_rank_fusion",
        }

    @staticmethod
    def search(query: str, top_k: int = 5):
        results, _ = HybridRetriever.search_with_metrics(query, top_k)
        return results