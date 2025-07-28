from .vectorstore import query_vectorstore
from .embedder import embed_chunks

def retrieve_chunks(query: str, n_results: int = 5) -> list[dict]:
    query_embedding = embed_chunks([{"text": query}])
    results = query_vectorstore(query_embedding[0]["embedding"], n_results=n_results)
    return results