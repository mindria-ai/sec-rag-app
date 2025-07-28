import chromadb
from chromadb.utils import embedding_functions

class VectorStore:
    def __init__(self, embedding_function):
        self.client = chromadb.Client()
        

        
        self.collection = self.client.get_or_create_collection(
            name="sec_filings",
            embedding_function=embedding_function
        )

    def add_chunks(self, chunks: list[dict]):
        ids = [str(i) for i in range(len(chunks))]
        documents = [chunk["text"] for chunk in chunks]
        metadatas = [chunk["metadata"] for chunk in chunks]
        embeddings = [chunk["embedding"] for chunk in chunks]

        self.collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings
        )

    def query_collection(self, query_embedding: list[float], n_results: int = 5) -> list[dict]:
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return results

    def delete_collection(self):
        self.client.delete_collection(name="sec_filings")
