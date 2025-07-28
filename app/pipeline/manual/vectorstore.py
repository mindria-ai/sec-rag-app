import chromadb
from chromadb.utils import embedding_functions

client = chromadb.Client()

default_ef = embedding_functions.DefaultEmbeddingFunction()

collection = client.get_or_create_collection(
    name="sec_filings",
    embedding_function=default_ef
)

def store_chunks(chunks: list[dict]):
    for i, chunk in enumerate(chunks):
        collection.add(
            ids=[str(i)],
            documents=[chunk["text"]],
            metadatas=[chunk["metadata"]]
        )

def query_vectorstore(query_embedding: list[float], n_results: int = 5) -> list[dict]:
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=n_results
    )
    return results
