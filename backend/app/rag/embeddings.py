import hashlib
import re

import numpy as np


class EmbeddingService:
    DIMENSION = 384
    TOKEN_PATTERN = re.compile(r"[a-z0-9_]+")
    STOP_WORDS = {
        "a", "an", "and", "are", "as", "at", "be", "by", "can", "could",
        "do", "for", "from", "how", "i", "in", "is", "it", "of", "on",
        "or", "should", "that", "the", "this", "to", "what", "when",
        "where", "which", "who", "why", "with", "would", "you",
    }

    @classmethod
    def _embed(cls, text: str) -> np.ndarray:
        vector = np.zeros(cls.DIMENSION, dtype=np.float32)
        tokens = [
            token
            for token in cls.TOKEN_PATTERN.findall(text.lower())
            if token not in cls.STOP_WORDS
        ]
        tokens += [
            f"phrase:{left}_{right}"
            for left, right in zip(tokens, tokens[1:])
        ]

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