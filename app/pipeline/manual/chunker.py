from unstructured.chunking.title import chunk_by_title
from unstructured.partition.html import partition_html
from core.parser import parse_sec_doc

def chunk_document(file_path: str) -> list[dict]:
    # Use the existing parser to get cleaned text and metadata
    full_text, metadata = parse_sec_doc(file_path)
    
    # Use unstructured's chunk_by_title for semantic chunking
    elements = partition_html(text=full_text)
    chunks = chunk_by_title(elements)
    
    chunked_content = []
    for chunk in chunks:
        chunk_dict = {
            "text": chunk.text,
            "metadata": metadata  # Attach original metadata to each chunk
        }
        chunked_content.append(chunk_dict)
        
    return chunked_content