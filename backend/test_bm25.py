from app.rag.loader import DocumentLoader
from app.rag.chunker import DocumentChunker
from app.rag.bm25_store import BM25Store

docs = DocumentLoader.load_documents(
    "knowledge_base"
)

chunks = DocumentChunker.chunk_documents(
    docs
)

BM25Store.build_index(
    chunks
)