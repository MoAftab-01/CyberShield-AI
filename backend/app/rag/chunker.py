from langchain_text_splitters import RecursiveCharacterTextSplitter

class DocumentChunker:

    @staticmethod
    def chunk_documents(documents):

        splitter = RecursiveCharacterTextSplitter(

            chunk_size=800,

            chunk_overlap=150,

            separators=[
                "\n\n",
                "\n",
                ". ",
                " ",
                "",
            ],
        )

        chunks = splitter.split_documents(documents)

        for index, chunk in enumerate(chunks):
            chunk.metadata = {
                **chunk.metadata,
                "chunk_index": index,
                "chunk_id": f"{chunk.metadata.get('filename', 'document')}:{index}",
            }

        return chunks