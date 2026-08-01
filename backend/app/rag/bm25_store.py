import pickle
from pathlib import Path

from rank_bm25 import BM25Okapi


class BM25Store:

    INDEX_PATH = Path("vector_db/bm25.pkl")

    _bm25 = None

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

        cls._bm25 = bm25

        print(
            f"Indexed {len(corpus)} chunks."
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