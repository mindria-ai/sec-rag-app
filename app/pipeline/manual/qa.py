import openai
from core.parser import parse_sec_doc
import json
import os

# It's better to initialize the client once and reuse it.
# Ensure the OPENAI_API_KEY is set in your environment variables.
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_ipo_recommendation(file_path: str, model: str = "gpt-4o") -> dict:
    """
    Analyzes an SEC filing to provide an IPO purchase recommendation.

    Args:
        file_path: The absolute path to the SEC filing document.
        model: The OpenAI model to use for the analysis.

    Returns:
        A dictionary containing the score, summary, and citations.
    """
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

# This function is kept for other potential uses or for a different mode.
def answer_question(query: str, file_path: str) -> str:
    # This function is not used in the primary IPO recommendation flow
    # but is kept for potential future use.
    from .retriever import retrieve_chunks
    
    chunks = retrieve_chunks(query)
    context = "\n".join([chunk["text"] for chunk in chunks["documents"][0]])
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"}
        ]
    )
    
    return response.choices[0].message.content