import pickle
import re
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

        corpus = [cls.tokenize(doc.page_content) for doc in documents]

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
    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "could",
        "do", "for", "from", "how", "i", "in", "is", "it", "of", "on",
        "or", "should", "that", "the", "this", "to", "what", "when",
        "where", "which", "who", "why", "with", "would", "you",
    }

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        tokens = [
            token
            for token in cls.TOKEN_PATTERN.findall(text.lower())
            if token not in cls.STOP_WORDS
        ]
        bigrams = [
            f"phrase:{left}_{right}"
            for left, right in zip(tokens, tokens[1:])
        ]
        return tokens + bigrams
