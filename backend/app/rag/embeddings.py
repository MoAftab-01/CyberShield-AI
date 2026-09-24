import hashlib
import re

import numpy as np


class EmbeddingService:
    DIMENSION = 384
    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")

    @classmethod
    def _embed(cls, text: str) -> np.ndarray:
        vector = np.zeros(cls.DIMENSION, dtype=np.float32)
        tokens = cls.TOKEN_PATTERN.findall(text.lower())

        for token in tokens:
            digest = hashlib.blake2b(
                token.encode("utf-8"),
                digest_size=8,
            ).digest()
            index = int.from_bytes(digest[:4], "little") % cls.DIMENSION
            vector[index] += 1.0

        norm = np.linalg.norm(vector)
        if norm:
            vector /= norm

        return vector

    @classmethod
    def embed_documents(cls, texts):
        return np.asarray(
            [cls._embed(text) for text in texts],
            dtype=np.float32,
        )

    @classmethod
    def embed_query(cls, query):
        return cls._embed(query).reshape(1, -1)