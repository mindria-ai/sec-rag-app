import logging
from pathlib import Path
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html

logger = logging.getLogger(__name__)

def parse_sec_doc(file_path: str) -> tuple[str, dict]:
    raw_html = Path(file_path).read_text(encoding='utf-8', errors='replace')
    soup = BeautifulSoup(raw_html, 'lxml')
    
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()

    # Partition into semantic elements (paragraphs, tables, etc.)
    elements = partition_html(text=str(soup))
    # Gather and filter text segments
    texts = [el.text.strip() for el in elements if el.text and len(el.text.split()) > 5]
    full_text = ' '.join(texts)

    metadata = {
        "source": str(file_path),
        "filing_type": Path(file_path).stem.upper(),
        "char_length": len(full_text),
        "word_count": len(full_text.split())
    }

    logger.info(f"Loaded and cleaned document: {file_path}")
    return full_text, metadata
