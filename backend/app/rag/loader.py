import re
from pathlib import Path

import fitz
from langchain_core.documents import Document
from langchain_community.document_loaders import TextLoader

DASH_NORMALIZATION = re.compile(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]")
SPACE_NORMALIZATION = re.compile(r"[ \t\u00a0\u200b]+")


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
                    doc_pdf = fitz.open(str(file))
                    docs = []
                    for page_num, page in enumerate(doc_pdf):
                        text = page.get_text()
                        if not text or not text.strip():
                            continue
                        text = DASH_NORMALIZATION.sub("-", text)
                        text = SPACE_NORMALIZATION.sub(" ", text)
                        docs.append(
                            Document(
                                page_content=text,
                                metadata={"page": page_num},
                            )
                        )
                    doc_pdf.close()

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

                    # Marks this chunk as public knowledge-base material so
                    # retrieval never has to infer visibility from a folder
                    # name. User uploads are tagged "user_upload" instead.
                    doc.metadata["scope"] = "knowledge_base"

                    doc.metadata["document_title"] = file.stem.replace(
                        "_", " "
                    )

                documents.extend(docs)

            except Exception as e:

                print(
                    f"Failed to load {file}: {e}"
                )

        return documents