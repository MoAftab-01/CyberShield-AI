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
    ):

        if file_path.lower().endswith(".pdf"):
            pdf = fitz.open(file_path)
            documents = [
                Document(
                    page_content=page.get_text(),
                    metadata={
                        "filename": filename,
                        "page": page_number,
                        "source_folder": "uploads",
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
                        "filename": filename,
                        "page": 0,
                        "source_folder": "uploads",
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