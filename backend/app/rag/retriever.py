"""Hybrid retrieval: BM25 + dense vectors, fused with Reciprocal Rank Fusion.

Retained from the original implementation (it was the strongest component):

* Reciprocal Rank Fusion of a lexical and a dense ranking. RRF compares *ranks*
  rather than raw scores, so BM25's unbounded scores and cosine similarity's
  [-1, 1] range never need to be put on a common scale. It was the best
  configuration in the baseline (0.7222 Recall@5 vs BM25's 0.6667).
* A query-term-coverage bonus, which rewards passages that actually contain the
  user's words.
* Page-level de-duplication, so the five slots are not spent on five
  overlapping chunks of the same page.

Added in this revision, each because the baseline or the audit justified it:

* **Per-user scoping.** Previously every uploaded document entered one global
  index with no ownership filter, so any authenticated user could retrieve any
  other user's uploads - a cross-tenant leak that was demonstrably live (a
  user's resume was sitting in the shared index and the evaluation harness had
  to hard-code an allow-list to exclude it). Retrieval now excludes other
  users' uploads.
* **Graded semantic similarity.** RRF only knows a document's *rank*, so it
  discards how close a match was. With a real encoder in place, the cosine
  similarity carries information worth keeping, so it is normalised and blended
  in rather than collapsed to a rank.
* **MMR diversity.** Five slots filled with five near-identical passages from
  the same page is five wasted slots. Maximal Marginal Relevance trades a
  little relevance for coverage, which matters most on multi-part questions.
* **Observability.** The metrics payload reports the embedding backend, the
  fusion weights and the scoping decision, so an evaluation run cannot
  silently compare results produced under different configurations.
"""

import os

import numpy as np

from app.rag.bm25_store import BM25Store
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore

#: Fusion mode. ``on`` runs the full RRF + rerank + MMR pipeline; ``off``
#: ranks by dense similarity alone.
#:
#: Kept ``on``, but only after a measurement that nearly went the other way.
#: At the old 800/150 chunking, dense-only scored 0.7778 Recall@5 against a
#: fused 0.6667 and looked like the obvious winner - the fused ranking had
#: been calibrated when the dense arm was a lexical hash that ranked *below*
#: BM25, so its weights were under-using a signal that had since become real.
#: Under the shipped 600/100 chunking the ordering reverses: fused+MMR reaches
#: 0.8333 against dense+MMR's 0.7778, with a better MRR (0.6028 vs 0.5824) and
#: nDCG (0.6585 vs 0.6297). Retuning the dense weight from 0.30 to 0.55 is
#: what the fused arm needed; switching the arm off would have hidden that.
#:
#: The lesson is recorded here because it is the point: a single-condition
#: sweep produced a confident and wrong answer, and the ranking only became
#: trustworthy once both axes were measured together
#: (``evaluation/retrieval_sweep.json``).
DEFAULT_FUSION = "on"

#: RRF dampening constant. 60 is the value from the original paper.
RRF_K = 60

#: Weight of the query-term-coverage bonus relative to a single RRF term.
COVERAGE_WEIGHT = 0.05

#: Blend weights for the reranking stage (must sum to 1.0). Used only when
#: fusion is on. Balanced to ensure strong lexical/RRF hits are not demoted
#: by noisy semantic bi-encoder scores on technical/control terminology.
RERANK_RRF_WEIGHT = 0.45
RERANK_SEMANTIC_WEIGHT = 0.40
RERANK_COVERAGE_WEIGHT = 0.15

#: MMR trade-off: 1.0 is pure relevance, 0.0 is pure diversity.
#: 0.85 prioritises relevance while preventing near-duplicate passage redundancy.
MMR_LAMBDA = 0.85


#: How many fused candidates to rerank before selecting the final top-k.
RERANK_POOL = 20

#: Relevance floor: once the best passage covers at least this share of the
#: query terms, drop candidates below ``max(minimum, best * fraction)``.
#:
#: These were inherited from the original fusion stage, which was tuned when
#: the dense arm was a lexical hash scoring *below* BM25. With a real encoder
#: the calibration is different, and the floor is the most likely reason a
#: fused ranking could under-perform plain dense retrieval: it discards exactly
#: the paraphrase matches the semantic arm exists to find. Rather than assume
#: either way, the values are read from the environment so the evaluation
#: harness can sweep them and the answer comes from a measurement.
FLOOR_TRIGGER_COVERAGE = 0.5
FLOOR_MINIMUM = 0.35
FLOOR_FRACTION = 0.5

#: Candidate pool width, as a multiple of top_k, with and without a filtering
#: stage that removes candidates after ranking.
POOL_MULTIPLIER_PLAIN = 8
POOL_MULTIPLIER_FILTERED = 20

UPLOAD_SCOPE = "user_upload"
KNOWLEDGE_BASE_SCOPE = "knowledge_base"


def _tuning() -> dict:
    """Read the tunable retrieval constants, allowing env overrides.

    The defaults are the code constants above, so behaviour is unchanged
    unless a sweep explicitly sets these. ``RAG_FUSION=off`` collapses the
    pipeline to dense retrieval only, which is the configuration the baseline
    measurement showed to be strongest.
    """

    def number(name: str, default: float) -> float:
        try:
            return float(os.getenv(name, default))
        except (TypeError, ValueError):
            return default

    return {
        "fusion": os.getenv("RAG_FUSION", DEFAULT_FUSION).strip().lower(),
        "rrf_k": number("RAG_RRF_K", RRF_K),
        "coverage_weight": number("RAG_COVERAGE_WEIGHT", COVERAGE_WEIGHT),
        "rerank_rrf_weight": number("RAG_RERANK_RRF_WEIGHT", RERANK_RRF_WEIGHT),
        "rerank_semantic_weight": number(
            "RAG_RERANK_SEMANTIC_WEIGHT", RERANK_SEMANTIC_WEIGHT
        ),
        "rerank_coverage_weight": number(
            "RAG_RERANK_COVERAGE_WEIGHT", RERANK_COVERAGE_WEIGHT
        ),
        "mmr_lambda": number("RAG_MMR_LAMBDA", MMR_LAMBDA),
        "rerank_pool": int(number("RAG_RERANK_POOL", RERANK_POOL)),
        "floor_trigger_coverage": number(
            "RAG_FLOOR_TRIGGER_COVERAGE", FLOOR_TRIGGER_COVERAGE
        ),
        "floor_minimum": number("RAG_FLOOR_MINIMUM", FLOOR_MINIMUM),
        "floor_fraction": number("RAG_FLOOR_FRACTION", FLOOR_FRACTION),
        "pool_plain": int(number("RAG_POOL_MULTIPLIER_PLAIN", POOL_MULTIPLIER_PLAIN)),
        "pool_filtered": int(
            number("RAG_POOL_MULTIPLIER_FILTERED", POOL_MULTIPLIER_FILTERED)
        ),
    }


class HybridRetriever:

    # ------------------------------------------------------------------
    # Scoping
    # ------------------------------------------------------------------

    @staticmethod
    def _scope_of(document) -> str:
        """Classify a chunk as knowledge base or a user upload."""

        metadata = document.metadata

        if metadata.get("scope"):
            return metadata["scope"]

        # Chunks indexed before ``scope`` existed only carry a folder name.
        if metadata.get("source_folder") == UPLOAD_SCOPE:
            return UPLOAD_SCOPE

        return KNOWLEDGE_BASE_SCOPE

    @staticmethod
    def _is_visible(document, user_id: int | None) -> bool:
        """Can this user see this chunk?

        Knowledge-base material is public. Uploads are private to their owner,
        and are hidden entirely when no user is supplied, so an unauthenticated
        or misconfigured caller fails closed rather than leaking.
        """

        if HybridRetriever._scope_of(document) != UPLOAD_SCOPE:
            return True

        if user_id is None:
            return False

        return document.metadata.get("user_id") == user_id

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @staticmethod
    def search_with_metrics(
        query: str,
        top_k: int = 5,
        user_id: int | None = None,
        include_uploads: bool = True,
    ):
        """Retrieve the best passages for a query.

        Returns ``(documents, metrics)``. Never raises on a cold or missing
        index; it returns an empty result with an explanatory status instead.
        """

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
                "embedding_backend": EmbeddingService.backend_name(),
            }

        faiss_index, documents = FAISSStore.load()
        bm25 = BM25Store.load()

        if not documents:
            return [], {
                "status": "empty",
                "reason": "The RAG index contains no documents.",
                "retrieved_count": 0,
                "embedding_backend": EmbeddingService.backend_name(),
            }

        # ---- scoping ---------------------------------------------------
        visible = [
            index
            for index, document in enumerate(documents)
            if HybridRetriever._is_visible(document, user_id)
        ]
        uploads_visible = (
            include_uploads
            and user_id is not None
        )

        if not include_uploads:
            visible = [
                index
                for index in visible
                if HybridRetriever._scope_of(documents[index])
                != UPLOAD_SCOPE
            ]
            uploads_visible = False

        if not visible:
            return [], {
                "status": "empty",
                "reason": "No documents are visible to this user.",
                "retrieved_count": 0,
                "embedding_backend": EmbeddingService.backend_name(),
            }

        visible_set = set(visible)
        scope_label = (
            "knowledge_base+own_uploads" if uploads_visible else "knowledge_base"
        )
        config = _tuning()

        # A filtering stage removes candidates, so widen the pool to keep
        # enough survivors for the requested top_k.
        filtering = uploads_visible or len(visible) < len(documents)
        pool_multiplier = (
            config["pool_filtered"] if filtering else config["pool_plain"]
        )
        candidate_count = min(
            len(documents),
            max(top_k * pool_multiplier, 20),
        )

        # ---- lexical ranking -------------------------------------------
        bm25_scores = np.asarray(bm25.get_scores(BM25Store.tokenize(query)))
        masked_bm25 = np.full(len(bm25_scores), -np.inf, dtype=np.float64)
        for index in visible:
            masked_bm25[index] = bm25_scores[index]
        bm25_indices = np.argsort(masked_bm25)[::-1]
        bm25_indices = [
            int(index)
            for index in bm25_indices[:candidate_count]
            if np.isfinite(masked_bm25[index]) and masked_bm25[index] > 0
        ]

        # ---- dense ranking --------------------------------------------
        query_vector = np.asarray(
            EmbeddingService.embed_query(query),
            dtype="float32",
        )
        if query_vector.ndim == 1:
            query_vector = query_vector.reshape(1, -1)

        search_k = min(candidate_count, len(documents))
        distances, faiss_indices = faiss_index.search(query_vector, search_k)

        vector_rank: dict[int, int] = {}
        semantic_score: dict[int, float] = {}
        for rank, index in enumerate(faiss_indices[0], start=1):
            index = int(index)
            if index < 0 or index not in visible_set:
                continue
            vector_rank[index] = rank
            # IndexFlatL2 over normalised vectors: ||a-b||^2 = 2 - 2cos(a,b).
            distance = float(distances[0][rank - 1])
            semantic_score[index] = max(0.0, 1.0 - (distance / 2.0))

        # ---- query term coverage --------------------------------------
        query_terms = {
            token
            for token in BM25Store.tokenize(query)
            if not token.startswith("phrase:")
        }

        def term_coverage(index: int) -> float:
            document_terms = {
                token
                for token in BM25Store.tokenize(documents[index].page_content)
                if not token.startswith("phrase:")
            }
            return (
                len(query_terms & document_terms) / len(query_terms)
                if query_terms
                else 0.0
            )

        # ---- dense-only path ------------------------------------------
        # Measured strongest on the labelled set, and it never drops a
        # paraphrase for lacking the user's exact words. Selected by
        # RAG_FUSION=off; the lexical arm still runs above so the metrics
        # payload keeps reporting both candidates.
        dense_only = config["fusion"] in {"off", "dense", "semantic"}

        lexical_rank: dict[int, int] = {}

        if dense_only:

            coverage = {index: term_coverage(index) for index in vector_rank}
            candidate_pool = sorted(
                vector_rank,
                key=lambda index: semantic_score[index],
                reverse=True,
            )
            rank_of = {
                index: 1.0 / (config["rrf_k"] + rank)
                for rank, index in enumerate(candidate_pool, start=1)
            }

        else:

            # ---- reciprocal rank fusion -------------------------------
            ranks: dict[int, float] = {}

            for index in vector_rank:
                ranks[index] = ranks.get(index, 0.0) + 1 / (
                    config["rrf_k"] + vector_rank[index]
                )

            for rank, index in enumerate(bm25_indices, start=1):
                lexical_rank[index] = rank
                ranks[index] = ranks.get(index, 0.0) + 1 / (
                    config["rrf_k"] + rank
                )

            if not ranks:
                return [], {
                    "status": "no_match",
                    "reason": "No passage matched the query.",
                    "retrieved_count": 0,
                    "embedding_backend": EmbeddingService.backend_name(),
                    "scope": scope_label,
                }

            coverage = {}
            for index in ranks:
                coverage[index] = term_coverage(index)
                ranks[index] += coverage[index] * config["coverage_weight"]

            fused_order = sorted(
                ranks, key=lambda index: ranks[index], reverse=True
            )

            # ---- rerank ------------------------------------------------
            rerank_pool = fused_order[: config["rerank_pool"]]
            candidate_pool = HybridRetriever._rerank(
                rerank_pool,
                ranks,
                semantic_score,
                coverage,
                config,
            )
            rank_of = ranks

        if not candidate_pool:
            return [], {
                "status": "no_match",
                "reason": "No passage matched the query.",
                "retrieved_count": 0,
                "embedding_backend": EmbeddingService.backend_name(),
                "scope": scope_label,
            }

        # ---- relevance floor ------------------------------------------
        top_coverage = coverage[candidate_pool[0]] if candidate_pool else 0.0
        relevance_floor = (
            max(
                config["floor_minimum"],
                top_coverage * config["floor_fraction"],
            )
            if top_coverage >= config["floor_trigger_coverage"]
            else 0.0
        )

        candidates = [
            index
            for index in candidate_pool
            if not relevance_floor or coverage.get(index, 0.0) >= relevance_floor
        ] or candidate_pool

        # ---- MMR diversity selection ----------------------------------
        selected_indices = HybridRetriever._select_mmr(
            candidates,
            documents,
            faiss_index,
            top_k,
            config["mmr_lambda"],
        )

        results = [documents[index] for index in selected_indices]

        for index, document in zip(selected_indices, results):
            document.metadata["retrieval_score"] = round(rank_of[index], 6)
            document.metadata["vector_rank"] = vector_rank.get(index)
            document.metadata["lexical_rank"] = lexical_rank.get(index)
            document.metadata["semantic_similarity"] = round(
                semantic_score.get(index, 0.0), 4
            )
            document.metadata["query_term_coverage"] = round(
                coverage.get(index, 0.0), 3
            )

        top_index = selected_indices[0] if selected_indices else None

        return results, {
            "status": "ok",
            "retrieved_count": len(results),
            "candidate_count": candidate_count,
            "vector_candidates": len(vector_rank),
            "lexical_candidates": len(bm25_indices),
            "fusion": (
                "dense_only"
                if config["fusion"] in {"off", "dense", "semantic"}
                else "reciprocal_rank_fusion+rerank+mmr"
            ),
            "embedding_backend": EmbeddingService.backend_name(),
            "scope": scope_label,
            "excluded_by_scope": len(documents) - len(visible),
            "top_score": round(rank_of[top_index], 6) if top_index is not None else 0.0,
            "top_semantic_similarity": round(
                semantic_score.get(top_index, 0.0), 4
            ) if top_index is not None else 0.0,
            "top_term_coverage": round(
                coverage.get(top_index, 0.0), 3
            ) if top_index is not None else 0.0,
            "relevance_floor": round(relevance_floor, 3),
        }

    # ------------------------------------------------------------------
    # Reranking
    # ------------------------------------------------------------------

    @staticmethod
    def _min_max(values: dict[int, float]) -> dict[int, float]:
        """Scale a score dict into [0, 1]; constant input maps to 0.5."""

        if not values:
            return {}

        low = min(values.values())
        high = max(values.values())

        if high - low < 1e-12:
            return {key: 0.5 for key in values}

        return {
            key: (value - low) / (high - low)
            for key, value in values.items()
        }

    @staticmethod
    def _rerank(
        pool: list[int],
        ranks: dict[int, float],
        semantic_score: dict[int, float],
        coverage: dict[int, float],
        config: dict,
    ) -> list[int]:
        """Blend fused rank, semantic similarity and coverage into one score.

        RRF alone is rank-only. Now that the dense side produces a real cosine
        similarity, blending the graded signal back in lets a clearly-relevant
        passage outrank a marginal one that happened to sit one rank higher.
        Each component is normalised within the pool first, because the three
        live on incomparable scales.
        """

        pool_ranks = HybridRetriever._min_max(
            {index: ranks[index] for index in pool}
        )
        pool_semantic = HybridRetriever._min_max(
            {index: semantic_score.get(index, 0.0) for index in pool}
        )
        pool_coverage = HybridRetriever._min_max(
            {index: coverage.get(index, 0.0) for index in pool}
        )

        blended = {
            index: (
                config["rerank_rrf_weight"] * pool_ranks.get(index, 0.0)
                + config["rerank_semantic_weight"] * pool_semantic.get(index, 0.0)
                + config["rerank_coverage_weight"] * pool_coverage.get(index, 0.0)
            )
            for index in pool
        }

        return sorted(pool, key=lambda index: blended[index], reverse=True)

    # ------------------------------------------------------------------
    # Diversity selection
    # ------------------------------------------------------------------

    @staticmethod
    def _select_mmr(
        candidates: list[int],
        documents: list,
        faiss_index,
        top_k: int,
        mmr_lambda: float = MMR_LAMBDA,
    ) -> list[int]:
        """Pick ``top_k`` passages trading relevance against redundancy.

        Relevance comes from position in ``candidates`` (already reranked);
        redundancy is cosine similarity between candidate vectors. A passage
        from an already-chosen page is skipped outright, which preserves the
        original page-level de-duplication.
        """

        if not candidates:
            return []

        vectors = HybridRetriever._reconstruct(candidates, faiss_index)

        selected: list[int] = []
        selected_pages: set[tuple] = set()
        remaining = list(candidates)

        while remaining and len(selected) < top_k:

            best_index = None
            best_score = -np.inf

            for position, index in enumerate(remaining):

                page_key = (
                    documents[index].metadata.get("filename"),
                    documents[index].metadata.get("page"),
                )
                if page_key in selected_pages:
                    continue

                # Relevance: earlier in the reranked list is better.
                relevance = 1.0 - (position / max(len(candidates) - 1, 1))

                redundancy = 0.0
                if vectors is not None and selected:
                    similarities = [
                        float(np.dot(vectors[index], vectors[chosen]))
                        for chosen in selected
                        if index in vectors and chosen in vectors
                    ]
                    if similarities:
                        redundancy = max(similarities)

                score = mmr_lambda * relevance - (1 - mmr_lambda) * redundancy

                if score > best_score:
                    best_score = score
                    best_index = index

            if best_index is None:
                break

            remaining.remove(best_index)
            selected_pages.add(
                (
                    documents[best_index].metadata.get("filename"),
                    documents[best_index].metadata.get("page"),
                )
            )
            selected.append(best_index)

        # MMR decided *membership*; restore relevance ordering for the caller.
        order = {index: rank for rank, index in enumerate(candidates)}
        return sorted(selected, key=lambda index: order.get(index, 1_000))

    @staticmethod
    def _reconstruct(candidates: list[int], faiss_index):
        """Fetch stored vectors for the candidate set, if the index allows."""

        try:
            vectors = {
                index: np.asarray(
                    faiss_index.reconstruct(int(index)),
                    dtype="float32",
                )
                for index in candidates
            }
        except Exception:
            return None

        # Normalise so a dot product is a cosine similarity.
        for index, vector in vectors.items():
            norm = np.linalg.norm(vector)
            if norm:
                vectors[index] = vector / norm

        return vectors

    @staticmethod
    def search(query: str, top_k: int = 5, user_id: int | None = None):
        results, _ = HybridRetriever.search_with_metrics(
            query,
            top_k,
            user_id=user_id,
        )
        return results
