from sentence_transformers import SentenceTransformer


class EmbeddingService:

    _model = SentenceTransformer(
        "all-MiniLM-L6-v2"
    )

    @staticmethod
    def embed_documents(texts):

        return EmbeddingService._model.encode(
            texts,
            convert_to_numpy=True,
            show_progress_bar=False,
        )

    @staticmethod
    def embed_query(query):

        return EmbeddingService._model.encode(
            query,
            convert_to_numpy=True,
        )