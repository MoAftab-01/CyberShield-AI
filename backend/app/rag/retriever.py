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
        candidate_count = min(len(documents), max(top_k * 8, 20))

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
        query_terms = {
            token
            for token in BM25Store.tokenize(query)
            if not token.startswith("phrase:")
        }

        # Reciprocal Rank Fusion makes lexical and semantic evidence contribute
        # equally without comparing scores from different scales.
        ranks: dict[int, float] = {}
        vector_rank: dict[int, int] = {}
        lexical_rank: dict[int, int] = {}
        coverage: dict[int, float] = {}
        for rank, index in enumerate(faiss_indices[0], start=1):
            index = int(index)
            if index >= 0:
                vector_rank[index] = rank
                ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)
        for rank, index in enumerate(bm25_indices, start=1):
            index = int(index)
            lexical_rank[index] = rank
            ranks[index] = ranks.get(index, 0.0) + 1 / (60 + rank)

        for index in ranks:
            document_terms = set(
                token
                for token in BM25Store.tokenize(
                    documents[index].page_content
                )
                if not token.startswith("phrase:")
            )
            coverage[index] = (
                len(query_terms & document_terms) / len(query_terms)
                if query_terms
                else 0.0
            )
            ranks[index] += coverage[index] * 0.05

        ranked_indices = sorted(
            ranks,
            key=lambda index: ranks[index],
            reverse=True,
        )
        top_coverage = (
            coverage[ranked_indices[0]]
            if ranked_indices
            else 0.0
        )
        relevance_floor = (
            max(0.35, top_coverage * 0.5)
            if top_coverage >= 0.5
            else 0.0
        )
        selected_indices = []
        selected_pages = set()
        for index in ranked_indices:
            if (
                relevance_floor
                and coverage[index] < relevance_floor
            ):
                continue
            page_key = (
                documents[index].metadata.get("filename"),
                documents[index].metadata.get("page"),
            )
            if page_key in selected_pages:
                continue
            selected_pages.add(page_key)
            selected_indices.append(index)
            if len(selected_indices) == top_k:
                break
        results = [documents[index] for index in selected_indices]
        for index, document in zip(selected_indices, results):
            document.metadata["retrieval_score"] = round(ranks[index], 6)
            document.metadata["vector_rank"] = vector_rank.get(index)
            document.metadata["lexical_rank"] = lexical_rank.get(index)
            document.metadata["query_term_coverage"] = round(
                coverage[index], 3
            )

        return results, {
            "status": "ok",
            "retrieved_count": len(results),
            "candidate_count": candidate_count,
            "vector_candidates": len(vector_rank),
            "lexical_candidates": len(lexical_rank),
            "fusion": "reciprocal_rank_fusion",
            "top_score": round(
                ranks[selected_indices[0]], 6
            ) if selected_indices else 0.0,
            "top_term_coverage": round(
                coverage[selected_indices[0]], 3
            ) if selected_indices else 0.0,
            "relevance_floor": round(relevance_floor, 3),
        }

    @staticmethod
    def search(query: str, top_k: int = 5):
        results, _ = HybridRetriever.search_with_metrics(query, top_k)
        return results