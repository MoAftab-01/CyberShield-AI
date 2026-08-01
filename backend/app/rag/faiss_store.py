import pickle
from pathlib import Path

import faiss
import numpy as np


class FAISSStore:

    INDEX_PATH = Path("vector_db/faiss.index")
    META_PATH = Path("vector_db/documents.pkl")

    _index = None
    _documents = None

    @classmethod
    def build_index(
        cls,
        embeddings,
        documents,
    ):

        embeddings = np.asarray(
            embeddings,
            dtype="float32",
        )

        dimension = embeddings.shape[1]

        index = faiss.IndexFlatL2(dimension)

        index.add(embeddings)

        cls.INDEX_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        faiss.write_index(
            index,
            str(cls.INDEX_PATH),
        )

        with open(
            cls.META_PATH,
            "wb",
        ) as f:

            pickle.dump(
                documents,
                f,
            )

        cls._index = index
        cls._documents = documents

        print(f"Indexed {index.ntotal} chunks.")

    @classmethod
    def load(cls):

        if cls._index is not None:

            return cls._index, cls._documents

        cls._index = faiss.read_index(
            str(cls.INDEX_PATH)
        )

        with open(
            cls.META_PATH,
            "rb",
        ) as f:

            cls._documents = pickle.load(f)

        return cls._index, cls._documents