from core.parser import parse_sec_doc

def load_document(file_path: str) -> tuple[str, dict]:
  return parse_sec_doc(file_path)