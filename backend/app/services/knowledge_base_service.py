from pathlib import Path

from app.rag.bm25_store import BM25Store
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.loader import DocumentLoader


class KnowledgeBaseService:
    KNOWLEDGE_BASE_PATH = Path("knowledge_base")

    @classmethod
    def ensure_index(cls) -> dict[str, int | str]:
        index_files = (
            FAISSStore.INDEX_PATH,
            FAISSStore.META_PATH,
            BM25Store.INDEX_PATH,
            BM25Store.DOCS_PATH,
        )
        if all(path.exists() for path in index_files):
            return {"status": "existing"}

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
        return {"status": "built", "chunks": len(chunks)}
