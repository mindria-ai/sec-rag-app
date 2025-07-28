from openai import OpenAI
from dotenv import load_dotenv
import os
from chromadb.utils import embedding_functions

load_dotenv()

class Embedder:
    def __init__(self):
        self.client = OpenAI()
        self._openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )

    def embed_chunks(self, chunks: list[dict]) -> list[dict]:
        # This method is still needed for embedding individual chunks before adding to ChromaDB
        for chunk in chunks:
            response = self.client.embeddings.create(
                input=chunk["text"],
                model="text-embedding-ada-002"
            )
            chunk["embedding"] = response.data[0].embedding
        return chunks

    def get_embedding_function(self):
        return self._openai_ef