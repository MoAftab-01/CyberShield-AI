"""Text embedding for retrieval.

History matters here. The original implementation produced 384-dimensional
vectors by hashing tokens into buckets with blake2b (the "hashing trick"). That
is a *lexical* representation, not a semantic one: "how do I stop SQL
injection" and "preventing database query tampering" share almost no hashed
tokens, so the vector arm could not retrieve what BM25 missed. The baseline
harness measured the consequence - the vector-only arm scored 0.3889 Recall@5
against BM25's 0.6667, i.e. it was actively worse than the lexical arm it was
supposed to complement, and hybrid fusion gained only +0.055 over BM25 alone.

This module now fronts a real sentence encoder (all-MiniLM-L6-v2, 384-d, ONNX
runtime via ``fastembed``) which is small enough to run on free-tier CPU
hosting and needs no PyTorch. Two constraints shaped the design:

* **It must never be able to break the app.** If ``fastembed`` is not
  installed, the model cannot be downloaded, or inference raises, the service
  falls back to the original hashed representation and reports which backend
  is live via :meth:`EmbeddingService.backend_name`. Search degrades in
  quality; it does not stop working. The active backend is also recorded in
  the retrieval metrics so an evaluation run can never silently mix backends.
* **Query and document vectors must come from the same model.** The backend is
  resolved once and cached, so an index built with one encoder is never
  searched with another.
"""

import hashlib
import os
import re
import threading

import numpy as np

#: Preferred model: 384-d, ~90MB ONNX, CPU-friendly, no PyTorch dependency.
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

#: Kept identical to the historical hash dimension so a stale index remains
#: loadable rather than crashing at startup.
HASH_DIMENSION = 384

BACKEND_AUTO = "auto"
BACKEND_FASTEMBED = "fastembed"
BACKEND_HASH = "hash"

#: Minimum container memory, in megabytes, for `auto` to choose the semantic
#: model. Loading the ONNX runtime plus a 384-d sentence encoder costs roughly
#: 250-300MB resident on top of the interpreter, NumPy, FAISS and SQLAlchemy -
#: measured, not guessed: on a 512MB Render instance the previous `auto` default
#: loaded the model and was OOM-killed seconds later, before uvicorn could bind
#: a port. A floor of 900MB means anything at or below the 512MB free tier
#: picks hashing, and a 1GB+ instance still gets semantic search.
#:
#: `EMBEDDING_BACKEND=fastembed` overrides this, because a hard request from an
#: operator who knows their instance is the one case where guessing is wrong.
EMBEDDING_MEMORY_FLOOR_MB = 900


class EmbeddingService:
    """Embeds documents and queries, preferring a real semantic model."""

    #: Backwards-compatible alias. Retained because the evaluation harness and
    #: older callers import it.
    DIMENSION = HASH_DIMENSION

    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "could",
        "do", "for", "from", "how", "i", "in", "is", "it", "of", "on",
        "or", "should", "that", "the", "this", "to", "what", "when",
        "where", "which", "who", "why", "with", "would", "you",
    }

    _lock = threading.Lock()
    _model = None
    _backend: str | None = None
    _dimension: int | None = None

    # ------------------------------------------------------------------
    # Backend resolution
    # ------------------------------------------------------------------

    @classmethod
    def _configured_backend(cls) -> str:
        return os.getenv("EMBEDDING_BACKEND", BACKEND_AUTO).strip().lower()

    @classmethod
    def _memory_limit_mb(cls) -> float | None:
        """The memory this process is actually allowed to use, or None.

        A container sees the host's total RAM through the usual interfaces, so
        the cgroup limit is read first - it is the number that gets enforced,
        and on a 512MB instance it is the difference between "fits" and
        "OOM-killed". Physical RAM is only a fallback for a bare-metal run.
        """

        for path in (
            "/sys/fs/cgroup/memory.max",  # cgroup v2
            "/sys/fs/cgroup/memory/memory.limit_in_bytes",  # cgroup v1
        ):
            try:
                raw = open(path, encoding="utf-8").read().strip()
            except OSError:
                continue

            if raw == "max":  # v2's "no limit"
                continue

            try:
                limit = int(raw)
            except ValueError:
                continue

            # An unset v1 limit is reported as a huge sentinel, not as absent.
            if 0 < limit < (1 << 62):
                return limit / (1024 * 1024)

        try:
            return (
                os.sysconf("SC_PHYS_PAGES")
                * os.sysconf("SC_PAGE_SIZE")
                / (1024 * 1024)
            )
        except (AttributeError, ValueError, OSError):
            return None

    @classmethod
    def _semantic_fits_in_memory(cls) -> bool:
        floor = float(
            os.getenv("EMBEDDING_MEMORY_FLOOR_MB", EMBEDDING_MEMORY_FLOOR_MB)
        )
        limit = cls._memory_limit_mb()

        if limit is None:
            return True  # cannot tell, so do not block a working setup

        if limit < floor:
            print(
                f"[embeddings] {limit:.0f}MB available, below the {floor:.0f}MB "
                f"needed for {DEFAULT_MODEL}; using the hashed backend. Raise "
                "EMBEDDING_MEMORY_FLOOR_MB only if the instance really has the "
                "memory - the model loads and is OOM-killed later, which takes "
                "the whole service down rather than degrading it."
            )
            return False

        return True

    @classmethod
    def _resolve_backend(cls) -> None:
        """Decide once which encoder is available, and cache the decision."""

        if cls._backend is not None:
            return

        with cls._lock:

            if cls._backend is not None:
                return

            configured = cls._configured_backend()

            # Memory is checked only for `auto`. An explicit request is
            # honoured, because the operator may know something the probe
            # cannot see.
            if configured in (BACKEND_AUTO, BACKEND_FASTEMBED):
                if configured == BACKEND_AUTO and not cls._semantic_fits_in_memory():
                    cls._backend = BACKEND_HASH
                    cls._dimension = HASH_DIMENSION
                    return

                model = cls._try_load_fastembed()
                if model is not None:
                    cls._model = model
                    cls._backend = BACKEND_FASTEMBED
                    cls._dimension = 384
                    print(f"[embeddings] semantic backend ready: {DEFAULT_MODEL}")
                    return

                if configured == BACKEND_FASTEMBED:
                    print(
                        "[embeddings] EMBEDDING_BACKEND=fastembed was requested "
                        "but the model is unavailable; falling back to hashing."
                    )

            cls._backend = BACKEND_HASH
            cls._dimension = HASH_DIMENSION
            print(
                "[embeddings] using hashed lexical backend "
                "(semantic search disabled - install fastembed to enable it)"
            )

    @classmethod
    def _try_load_fastembed(cls):
        """Load the ONNX model, returning None on any failure."""

        try:
            from fastembed import TextEmbedding
        except Exception:
            return None

        try:
            model_name = os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
            # cache_dir keeps the download inside the deploy image when the
            # Dockerfile pre-warms it, instead of re-downloading per boot.
            cache_dir = os.getenv("EMBEDDING_CACHE_DIR") or None
            return TextEmbedding(
                model_name=model_name,
                cache_dir=cache_dir,
            )
        except Exception as error:
            print(f"[embeddings] could not load {DEFAULT_MODEL}: {error}")
            return None

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    @classmethod
    def backend_name(cls) -> str:
        cls._resolve_backend()
        return cls._backend or BACKEND_HASH

    @classmethod
    def is_semantic(cls) -> bool:
        return cls.backend_name() == BACKEND_FASTEMBED

    @classmethod
    def dimension(cls) -> int:
        cls._resolve_backend()
        return cls._dimension or HASH_DIMENSION

    @classmethod
    def model_name(cls) -> str | None:
        """The encoder that built this vector space, or None when hashing.

        Recorded in the index stamp: two indexes can share a dimension while
        living in unrelated vector spaces, so the model - not the width - is
        what makes an index safe to reuse.
        """

        return (
            os.getenv("EMBEDDING_MODEL", DEFAULT_MODEL)
            if cls.is_semantic()
            else None
        )

    # ------------------------------------------------------------------
    # Hashed fallback (unchanged behaviour)
    # ------------------------------------------------------------------

    @classmethod
    def _embed_hashed(cls, text: str) -> np.ndarray:
        vector = np.zeros(HASH_DIMENSION, dtype=np.float32)

        tokens = [
            token
            for token in cls.TOKEN_PATTERN.findall((text or "").lower())
            if token not in cls.STOP_WORDS
        ]
        tokens += [
            f"phrase:{left}_{right}"
            for left, right in zip(tokens, tokens[1:])
        ]

        for token in tokens:
            digest = hashlib.blake2b(
                token.encode("utf-8"),
                digest_size=8,
            ).digest()
            index = int.from_bytes(digest[:4], "little") % HASH_DIMENSION
            vector[index] += 1.0

        norm = np.linalg.norm(vector)
        if norm:
            vector /= norm

        return vector

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @classmethod
    def embed_documents(cls, texts) -> np.ndarray:
        """Embed a batch of passages. Returns shape (n, dimension)."""

        texts = list(texts)

        if not texts:
            return np.zeros((0, cls.dimension()), dtype=np.float32)

        cls._resolve_backend()

        if cls._backend == BACKEND_FASTEMBED:
            try:
                vectors = np.asarray(
                    list(cls._model.embed(texts)),
                    dtype=np.float32,
                )
                if vectors.ndim == 2 and vectors.shape[0] == len(texts):
                    return vectors
                print(
                    "[embeddings] unexpected embedding shape "
                    f"{vectors.shape}; falling back to hashing for this batch"
                )
            except Exception as error:
                print(f"[embeddings] inference failed ({error}); using hashing")

        return np.asarray(
            [cls._embed_hashed(text) for text in texts],
            dtype=np.float32,
        )

    @classmethod
    def embed_query(cls, query: str) -> np.ndarray:
        """Embed a single query. Returns shape (1, dimension).

        Documents and queries share one encoder (all-MiniLM-L6-v2 is
        symmetric), so no instruction prefix is applied.
        """

        return cls.embed_documents([query])

    @classmethod
    def hash_vectors(cls, texts) -> np.ndarray:
        """Embed with the legacy hashed encoder regardless of the live backend.

        Exists so the evaluation harness can still reproduce the pre-change
        baseline numbers on a machine whose index was built by the semantic
        encoder. Without it the old arm would silently measure the new
        representation against old vectors and report a meaningless score.
        """

        return np.asarray(
            [cls._embed_hashed(text) for text in texts],
            dtype=np.float32,
        )
