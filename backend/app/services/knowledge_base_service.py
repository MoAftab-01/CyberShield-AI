"""Knowledge-base index lifecycle.

Startup responsibilities:

1. Decide whether the index on disk is still valid.
2. Rebuild it when it is not - including when the *embedding backend changed*,
   which the provenance stamp in :mod:`app.rag.index_meta` detects. Without
   that check a deploy could leave a hash-built index on disk that the new
   semantic encoder would search, silently degrading every answer instead of
   failing.
3. Keep the public knowledge base and user uploads in one index while tagging
   each chunk with its scope and owner, so retrieval can enforce visibility.

Rebuilding re-indexes uploads found on disk, so a rebuild triggered by a
configuration change does not silently drop documents a user had uploaded.
"""

import threading
from pathlib import Path

from app.rag import index_meta
from app.rag.bm25_store import BM25Store
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.loader import DocumentLoader


_BASE_DIR = Path(__file__).resolve().parent.parent.parent


class KnowledgeBaseService:
    KNOWLEDGE_BASE_PATH = (
        Path("knowledge_base")
        if Path("knowledge_base").exists()
        else _BASE_DIR / "knowledge_base"
    )
    UPLOAD_PATH = (
        Path("uploads")
        if Path("uploads").exists()
        else _BASE_DIR / "uploads"
    )

    _lock = threading.Lock()


    @classmethod
    def ensure_index(cls, force: bool = False) -> dict[str, int | str]:
        """Build the index if it is missing or stale. Safe to call twice."""

        with cls._lock:

            if not force and cls._index_is_current():
                return {"status": "existing"}

            return cls._rebuild()

    # ------------------------------------------------------------------

    @classmethod
    def _current_stamp(cls) -> dict:
        return index_meta.expected_stamp(
            vector_dimension=EmbeddingService.dimension(),
            backend=EmbeddingService.backend_name(),
            model=EmbeddingService.model_name(),
        )

    @classmethod
    def _index_is_current(cls) -> bool:
        index_files = (
            FAISSStore.INDEX_PATH,
            FAISSStore.META_PATH,
            BM25Store.INDEX_PATH,
            BM25Store.DOCS_PATH,
        )
        if not all(path.exists() for path in index_files):
            return False

        return index_meta.matches(
            cls._current_stamp(),
            index_meta.read_stamp(),
        )

    # ------------------------------------------------------------------

    @classmethod
    def _rebuild(cls) -> dict[str, int | str]:

        documents = DocumentLoader.load_documents(
            str(cls.KNOWLEDGE_BASE_PATH)
        )
        chunks = DocumentChunker.chunk_documents(documents)

        if not chunks:
            return {
                "status": "empty",
                "reason": "No knowledge-base documents were found.",
            }

        embeddings = EmbeddingService.embed_documents(
            [chunk.page_content for chunk in chunks]
        )
        FAISSStore.build_index(embeddings, chunks)
        BM25Store.build_index(chunks)

        upload_count = cls._reindex_uploads()

        index_meta.write_stamp(cls._current_stamp())

        return {
            "status": "built",
            "chunks": len(chunks),
            "uploads_reindexed": upload_count,
            "embedding_backend": EmbeddingService.backend_name(),
        }

    @classmethod
    def _reindex_uploads(cls) -> int:
        """Re-add documents from the uploads directory to the fresh index.

        A rebuild discards whatever was in the index, so uploads that still
        exist on disk are re-indexed here. Their owning user is recovered from
        the ``user_<id>`` directory name.
        """

        from app.services.document_index_service import DocumentIndexService

        if not cls.UPLOAD_PATH.exists():
            return 0

        indexed = 0

        for user_directory in sorted(cls.UPLOAD_PATH.iterdir()):

            if not user_directory.is_dir():
                continue

            try:
                user_id = int(user_directory.name.split("_", 1)[1])
            except (IndexError, ValueError):
                continue

            for file in sorted(user_directory.iterdir()):

                if not file.is_file():
                    continue

                try:
                    DocumentIndexService.index_document(
                        file_path=str(file),
                        filename=file.name,
                        user_id=user_id,
                    )
                    indexed += 1
                except Exception as error:
                    print(f"[index] could not re-index {file}: {error}")

        return indexed
