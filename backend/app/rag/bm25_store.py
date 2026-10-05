import os
import pickle
import re
from pathlib import Path

from rank_bm25 import BM25Okapi

_BASE_DIR = Path(__file__).resolve().parent.parent.parent
_VECTOR_DB_DIR = (
    Path(os.getenv("VECTOR_DB_DIR"))
    if os.getenv("VECTOR_DB_DIR")
    else (Path("vector_db") if Path("vector_db").exists() else _BASE_DIR / "vector_db")
)


class BM25Store:

    INDEX_PATH = _VECTOR_DB_DIR / "bm25.pkl"
    DOCS_PATH = _VECTOR_DB_DIR / "bm25_documents.pkl"

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
    DASH_PATTERN = re.compile(r"[\u2010\u2011\u2012\u2013\u2014\u2015\u2212]")
    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
    COMPOUND_PATTERN = re.compile(r"\b[a-z0-9]+(?:[-_][a-z0-9]+)+\b")
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "could",
        "do", "for", "from", "how", "i", "in", "is", "it", "of", "on",
        "or", "should", "that", "the", "this", "to", "what", "when",
        "where", "which", "who", "why", "with", "would", "you",
    }

    @classmethod
    def tokenize(cls, text: str) -> list[str]:
        normalised_text = cls.DASH_PATTERN.sub("-", (text or "").lower())
        tokens = [
            token
            for token in cls.TOKEN_PATTERN.findall(normalised_text)
            if token not in cls.STOP_WORDS
        ]
        compounds = [
            f"compound:{compound.replace('-', '_')}"
            for compound in cls.COMPOUND_PATTERN.findall(normalised_text)
        ]
        bigrams = [
            f"phrase:{left}_{right}"
            for left, right in zip(tokens, tokens[1:])
        ]
        return tokens + compounds + bigrams

