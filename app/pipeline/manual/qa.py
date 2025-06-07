import json

def answer_question(doc_path: str, question: str, params: dict):
  print(f'doc_path: {doc_path} | question: {question} | params: {json.dumps(params, indent=2)}')

  return
#     from pipeline.manual.embedder import embed_document
#     from pipeline.manual.retriever import retrieve_top_k
#     from openai import OpenAI

#     top_k = params.get("top_k", 5)
#     context_window = params.get("context_window", 3000)
#     temperature = params.get("temperature", 0.2)
#     top_p = params.get("top_p", 1.0)
#     max_tokens = params.get("max_tokens", 1024)

#     # Embed + Retrieve
#     chunks = retrieve_top_k(doc_path, question, top_k=top_k, context_limit=context_window)

#     # Construct prompt
#     context = "\n\n".join([chunk["text"] for chunk in chunks])
#     prompt = f"""
# You are a financial assistant analyzing SEC filings. Use only the provided context to answer the question.

# Context:
# {context}

# Question:
# {question}
# """

#     # Run OpenAI chat
#     client = OpenAI()
#     response = client.chat.completions.create(
#         model="gpt-4o",
#         temperature=temperature,
#         top_p=top_p,
#         max_tokens=max_tokens,
#         messages=[
#             {"role": "system", "content": "You are an expert in SEC document analysis."},
#             {"role": "user", "content": prompt}
#         ]
#     )
#     return response.choices[0].message.content
