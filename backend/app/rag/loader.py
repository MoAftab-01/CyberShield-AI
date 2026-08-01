from pathlib import Path

from langchain_core.documents import Document
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
)


class DocumentLoader:

    SUPPORTED_EXTENSIONS = {
        ".pdf",
        ".txt",
        ".md",
    }

    @classmethod
    def load_documents(
        cls,
        knowledge_base: str,
    ):

        documents = []

        root = Path(knowledge_base)

        for file in root.rglob("*"):

            if not file.is_file():
                continue

            if file.suffix.lower() not in cls.SUPPORTED_EXTENSIONS:
                continue

            try:

                if file.suffix.lower() == ".pdf":

                    loader = PyPDFLoader(str(file))

                else:

                    loader = TextLoader(
                        str(file),
                        encoding="utf-8",
                    )

                docs = loader.load()

                for doc in docs:

                    doc.metadata["filename"] = file.name

                    doc.metadata["source_folder"] = (
                        file.parent.name
                    )

                documents.extend(docs)

            except Exception as e:

                print(
                    f"Failed to load {file}: {e}"
                )

        return documents