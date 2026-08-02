from langchain_core.documents import Document

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
    ):

        text = DocumentExtractor.extract_text(
            file_path
        )

        document = Document(
            page_content=text,
            metadata={
                "filename": filename,
                "page": 0,
                "source_folder": "uploads",
            },
        )

        chunks = DocumentChunker.chunk_documents(
            [document]
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