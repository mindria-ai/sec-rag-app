import openai
from core.parser import parse_sec_doc
from .chunker import chunk_document
from core.embedder import Embedder # Import Embedder
from core.vectorstore import VectorStore # Import VectorStore
import json
import os

from .retriever import Retriever

# Initialize Embedder and VectorStore globally or pass them around
embedder_instance = Embedder()
embedding_function = embedder_instance.get_embedding_function()
vector_store = VectorStore(embedding_function)
retriever_instance = Retriever(vector_store, embedder_instance)

# It's better to initialize the client once and reuse it.
# Ensure the OPENAI_API_KEY is set in your environment variables.
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_combined_ipo_recommendation(file_paths: list[str], model: str = "gpt-4o"):
    """
    Analyzes multiple SEC filings to provide a combined IPO purchase recommendation.

    Args:
        file_paths: A list of absolute paths to the SEC filing documents.
        model: The OpenAI model to use for the analysis.

    Yields:
        Chunks of the streamed LLM response.
    """
    # Clear the ChromaDB collection before processing new documents
    try:
        vector_store.delete_collection()
    except Exception as e:
        # Collection might not exist, which is fine.
        pass

    all_metadata = []
    for file_path in file_paths:
        try:
            full_text, metadata = parse_sec_doc(file_path)
            chunks = chunk_document(file_path) # chunk_document now takes file_path
            embedded_chunks = embedder_instance.embed_chunks(chunks)
            vector_store.add_chunks(embedded_chunks) # Store chunks with embeddings
            all_metadata.append(metadata)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue

    # Retrieve relevant information from ChromaDB for the LLM prompt
    # This query should be broad enough to cover revenue and user growth
    retrieved_results = vector_store.query_collection(
        query_embedding=embedder_instance.embed_chunks([{"text": "year-over-year revenue growth, user growth, financial performance, key risks"}])[0]["embedding"],
        n_results=10 # Retrieve top 10 relevant chunks
    )
    
    context_chunks = []
    if retrieved_results and retrieved_results['documents']:
        for doc_list in retrieved_results['documents']:
            context_chunks.extend(doc_list)
    
    context = "\n\n".join(context_chunks)
    print(f"\n--- Retrieved Context for LLM ---\n{context}\n---\n")

    system_prompt = """You are an expert financial analyst specializing in pre-IPO companies. Your task is to analyze the provided SEC filing documents to determine if the company's IPO is a good investment."""

    user_prompt = f"""
    Please analyze the following information extracted from the company's SEC filings and provide a recommendation.

    **Context from SEC Filings:**
    ```
    {context}
    ```

    **Instructions:**

    Based on your analysis of the context provided, return ONLY a valid JSON object with the following structure:

    ```json
    {{
      "score": <A score from 1 to 10, where 1 is a strong 'do not buy' and 10 is a strong 'buy'.>,
      "summary": "<A concise summary of your reasoning for the score. Explain the key factors, both positive and negative, that you considered.>",
      "citations": [
        "<A direct quote from the context that supports your analysis of revenue growth>",
        "<A direct quote from the context that supports your analysis of user growth>",
        "<Any other relevant direct quote from the context>"
      ]
    }}
    ```

    **Crucially, you must place a higher weight on year-over-year growth metrics when determining your score.** Specifically, focus on:
    1.  **Revenue Growth:** How has revenue changed in the last few years?
    2.  **User/Customer Growth:** Is the company acquiring new users or customers at a healthy rate?

    Your analysis should be critical and objective. The `summary` must justify the `score` clearly, and the `citations` must be exact quotes from the provided context.
    """

    try:
        stream = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            stream=True,
        )
        for chunk in stream:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content

    except Exception as e:
        yield json.dumps({"score": 0, "summary": f"An unexpected error occurred: {str(e)}", "citations": []})


def get_ipo_recommendation(file_path: str, model: str = "gpt-4o") -> dict:
    # This function is no longer used in the main flow but kept for compatibility/testing
    full_text, metadata = parse_sec_doc(file_path)

    system_prompt = """You are an expert financial analyst specializing in pre-IPO companies. Your task is to analyze a provided SEC filing document to determine if the company's IPO is a good investment."""

    user_prompt = f"""
    Please analyze the following text from the company's SEC filing and provide a recommendation.

    **Context:**
    ```
    {full_text[:120000]}
    ```

    **Instructions:**

    Based on your analysis of the text provided, return ONLY a valid JSON object with the following structure:

    ```json
    {{
      "score": <A score from 1 to 10, where 1 is a strong 'do not buy' and 10 is a strong 'buy'.>,
      "summary": "<A concise summary of your reasoning for the score. Explain the key factors, both positive and negative, that you considered.>",
      "citations": [
        "<A direct quote from the text that supports your analysis of revenue growth>",
        "<A direct quote from the text that supports your analysis of user growth>",
        "<Any other relevant direct quote>"
      ]
    }}
    ```

    **Crucially, you must place a higher weight on year-over-year growth metrics when determining your score.** Specifically, focus on:
    1.  **Revenue Growth:** How has revenue changed in the last few years?
    2.  **User/Customer Growth:** Is the company acquiring new users or customers at a healthy rate?

    Your analysis should be critical and objective. The `summary` must justify the `score` clearly, and the `citations` must be exact quotes from the provided text.
    """

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        
        response_content = response.choices[0].message.content
        recommendation = json.loads(response_content)
        
        # Add the source of the document to the response
        recommendation['citations'].append(f"Source: {metadata.get('source', 'N/A')}")
        
        return recommendation

    except json.JSONDecodeError:
        return {
            "score": 0,
            "summary": "Error: The model did not return valid JSON.",
            "citations": [f"Raw model output: {response_content}"]
        }
    except Exception as e:
        return {
            "score": 0,
            "summary": f"An unexpected error occurred: {str(e)}",
            "citations": []
        }