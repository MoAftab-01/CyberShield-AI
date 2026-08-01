from sentence_transformers import SentenceTransformer


class EmbeddingService:

    _model = None

    MODEL_NAME = "all-MiniLM-L6-v2"

    @classmethod
    def get_model(cls):

        if cls._model is None:

            print(
                f"Loading embedding model: {cls.MODEL_NAME}"
            )

            cls._model = SentenceTransformer(
                cls.MODEL_NAME
            )

        return cls._model

    @classmethod
    def embed_documents(
        cls,
        documents,
    ):

        model = cls.get_model()

        texts = [
            doc.page_content
            for doc in documents
        ]

        embeddings = model.encode(
            texts,
            show_progress_bar=True,
            convert_to_numpy=True,
        )

        return embeddings

    @classmethod
    def embed_query(
        cls,
        query: str,
    ):

        model = cls.get_model()

        return model.encode(
            query,
            convert_to_numpy=True,
        )