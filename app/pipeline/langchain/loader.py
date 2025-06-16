from core.parser import parse_sec_doc
from langchain_core.documents import Document

def load_document(file_path: str) -> list[Document]:
  full_text, metadata = parse_sec_doc(file_path)

  return [Document(page_content=full_text, metadata=metadata)]