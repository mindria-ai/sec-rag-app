# app/pipeline_langchain/chain.py
def answer_question(doc_path: str, question: str) -> str:
    return f"(LangChain pipeline) Answer to: '{question}' based on {doc_path}"
