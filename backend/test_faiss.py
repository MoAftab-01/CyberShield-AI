from app.rag.loader import DocumentLoader
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService
from app.rag.faiss_store import FAISSStore

docs = DocumentLoader.load_documents(
    "knowledge_base"
)

chunks = DocumentChunker.chunk_documents(
    docs
)

vectors = EmbeddingService.embed_documents(
    chunks
)

FAISSStore.build_index(
    vectors,
    chunks,
)