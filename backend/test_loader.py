from app.rag.loader import DocumentLoader
from app.rag.chunker import DocumentChunker

docs = DocumentLoader.load_documents(
    "knowledge_base"
)

print(f"Documents Loaded: {len(docs)}")

chunks = DocumentChunker.chunk_documents(docs)

print(f"Chunks Created: {len(chunks)}")

if chunks:
    print(chunks[0].metadata)
    print()
    print(chunks[0].page_content[:300])
else:
    print("No chunks created.")