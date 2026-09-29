from langchain_core.documents import Document

from app.rag.chunker import DocumentChunker


def test_chunker_deduplicates_repeated_sections():
    repeated = (
        "# Access Control\n\n"
        "Use MFA for all remote admin access. "
        "Disable unused accounts promptly. "
        "Review privileged access quarterly. "
        "Block dormant accounts automatically. "
    )

    docs = [
        Document(
            page_content=repeated,
            metadata={"filename": "sample-1.pdf", "page": 0},
        ),
        Document(
            page_content=repeated,
            metadata={"filename": "sample-1.pdf", "page": 0},
        ),
        Document(
            page_content=repeated,
            metadata={"filename": "sample-2.pdf", "page": 0},
        ),
    ]

    chunks = DocumentChunker.chunk_documents(docs, chunk_size=200, chunk_overlap=20)

    assert len(chunks) == 2
    assert {chunk.metadata["filename"] for chunk in chunks} == {
        "sample-1.pdf",
        "sample-2.pdf",
    }
