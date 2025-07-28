import openai
from dotenv import load_dotenv
import os

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

def embed_chunks(chunks: list[dict]) -> list[dict]:
    for chunk in chunks:
        response = openai.Embedding.create(
            input=chunk["text"],
            model="text-embedding-ada-002"
        )
        chunk["embedding"] = response['data'][0]['embedding']
    return chunks