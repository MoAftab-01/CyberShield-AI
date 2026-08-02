import faiss
import numpy as np


class VectorStore:

    def __init__(self):

        self.index = None

        self.documents = []

    def create_index(
        self,
        embeddings,
        documents,
    ):

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatL2(
            dimension
        )

        self.index.add(
            embeddings.astype(np.float32)
        )

        self.documents = documents

    def search(
        self,
        embedding,
        k=5,
    ):

        distances, indices = self.index.search(
            embedding.astype(np.float32),
            k,
        )

        results = []

        for index in indices[0]:

            if index < len(self.documents):

                results.append(
                    self.documents[index]
                )

        return results