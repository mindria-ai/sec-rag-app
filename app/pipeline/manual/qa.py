# app/pipeline_manual/qa.py
def answer_question(doc_path: str, question: str) -> str:
    return f"(Manual pipeline) Answer to: '{question}' based on {doc_path}"
