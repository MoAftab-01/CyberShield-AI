from langchain_core.documents import Document
import fitz

from app.services.document_extractor import DocumentExtractor
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore
from app.rag.bm25_store import BM25Store


class DocumentIndexService:

    @staticmethod
    def index_document(
        file_path: str,
        filename: str,
        user_id: int | None = None,
    ):
        """Chunk and index an uploaded document.

        ``user_id`` is stamped into every chunk's metadata. Retrieval uses it
        to show a chunk only to its owner; without it an upload would be
        readable by every other user, because all uploads share one index.
        """

        shared_metadata = {
            "filename": filename,
            "scope": "user_upload",
            "source_folder": "uploads",
            "user_id": user_id,
            "document_title": filename,
        }

        if file_path.lower().endswith(".pdf"):
            pdf = fitz.open(file_path)
            documents = [
                Document(
                    page_content=page.get_text(),
                    metadata={
                        **shared_metadata,
                        "page": page_number,
                    },
                )
                for page_number, page in enumerate(pdf)
                if page.get_text().strip()
            ]
            pdf.close()
        else:
            documents = [
                Document(
                    page_content=DocumentExtractor.extract_text(file_path),
                    metadata={
                        **shared_metadata,
                        "page": 0,
                    },
                )
            ]

        chunks = DocumentChunker.chunk_documents(
            documents
        )

        embeddings = (
            EmbeddingService.embed_documents(
                [
                    chunk.page_content
                    for chunk in chunks
                ]
            )
        )

        FAISSStore.add_documents(
            embeddings,
            chunks,
        )

        BM25Store.add_documents(
            chunks,
        )