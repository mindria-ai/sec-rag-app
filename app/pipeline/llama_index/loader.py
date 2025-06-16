from core.parser import parse_sec_doc
from llama_index.core.schema import Document

def load_document(file_path: str) -> list[Document]:
  full_text, metadata = parse_sec_doc(file_path)
  
  return [Document(text=full_text, metadata=metadata)]