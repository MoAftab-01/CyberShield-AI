from app.services.rag_service import RAGService

response = RAGService.ask(

    "How do I prevent SQL Injection?"

)

print()

print(response["answer"])

print()

print("Sources")

for source in response["sources"]:

    print(source)