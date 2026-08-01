from app.rag.retriever import HybridRetriever

results = HybridRetriever.search(
    "How to prevent SQL Injection?"
)

print()

print(
    f"Results: {len(results)}"
)

print()

for i, doc in enumerate(results, start=1):

    print("=" * 80)

    print(f"Result {i}")

    print(doc.metadata)

    print()

    print(doc.page_content[:300])