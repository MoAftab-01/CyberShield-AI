from app.rag.loader import DocumentLoader
from app.rag.chunker import DocumentChunker
from app.rag.embeddings import EmbeddingService

docs = DocumentLoader.load_documents(
    "knowledge_base"
)

chunks = DocumentChunker.chunk_documents(
    docs
)

vectors = EmbeddingService.embed_documents(
    chunks
)

print(f"Chunks: {len(chunks)}")

print(f"Embedding Shape: {vectors.shape}")

print(vectors[0][:10])