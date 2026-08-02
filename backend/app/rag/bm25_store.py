import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi


class BM25Store:

    INDEX_PATH = Path("vector_db/bm25.pkl")
    DOCS_PATH = Path("vector_db/bm25_documents.pkl")

    _bm25 = None
    _documents = None

    @classmethod
    def build_index(
        cls,
        documents,
    ):

        corpus = [
            doc.page_content.split()
            for doc in documents
        ]

        bm25 = BM25Okapi(corpus)

        cls.INDEX_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with open(
            cls.INDEX_PATH,
            "wb",
        ) as f:

            pickle.dump(
                bm25,
                f,
            )

        with open(
            cls.DOCS_PATH,
            "wb",
        ) as f:

            pickle.dump(
                documents,
                f,
            )

        cls._bm25 = bm25
        cls._documents = documents

        print(
            f"Indexed {len(corpus)} chunks."
        )

    @classmethod
    def add_documents(
        cls,
        documents,
    ):

        if (
            cls.INDEX_PATH.exists()
            and cls.DOCS_PATH.exists()
        ):

            with open(
                cls.DOCS_PATH,
                "rb",
            ) as f:

                existing_documents = pickle.load(f)

            existing_documents.extend(
                documents
            )

            cls.build_index(
                existing_documents
            )

        else:

            cls.build_index(
                documents
            )

    @classmethod
    def load(cls):

        if cls._bm25 is not None:

            return cls._bm25

        with open(
            cls.INDEX_PATH,
            "rb",
        ) as f:

            cls._bm25 = pickle.load(f)

        return cls._bm25