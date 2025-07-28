from core.vectorstore import VectorStore
from core.embedder import Embedder

class Retriever:
    def __init__(self, vector_store: VectorStore, embedder: Embedder):
        self.vector_store = vector_store
        self.embedder = embedder

    def retrieve_chunks(self, query: str, n_results: int = 5) -> list[dict]:
        query_embedding = self.embedder.embed_chunks([{"text": query}])
        results = self.vector_store.query_collection(query_embedding[0]["embedding"], n_results=n_results)
        return results