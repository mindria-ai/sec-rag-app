import re
import logging
from typing import List, Dict
from pathlib import Path

from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chunk configuration
CHUNK_SIZE = 250  # number of words per chunk
OVERLAP = 50      # number of overlapping words between chunks


def parse_sec_htm_file(file_path: str) -> List[Dict]:
    """
    Parse an S-1, S-1/A, or Prospectus HTML file into fixed-size, overlapping chunks for vector embeddings.
    This version ignores section titles and chunks the entire document text.
    """
    # Read and clean HTML
    raw_html = Path(file_path).read_text(encoding='utf-8', errors='replace')
    soup = BeautifulSoup(raw_html, 'lxml')
    for tag in soup(['script', 'style', 'meta', 'link']):
        tag.decompose()

    # Partition into semantic elements (paragraphs, tables, etc.)
    elements = partition_html(text=str(soup))
    # Gather and filter text segments
    texts = [el.text.strip() for el in elements if el.text and len(el.text.split()) > 5]
    full_text = ' '.join(texts)

    # Sliding-window chunking helper
    def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = OVERLAP) -> List[str]:
        words = text.split()
        chunks = []
        step = size - overlap
        for i in range(0, len(words), step):
            chunk_words = words[i : i + size]
            if len(chunk_words) < overlap:
                break
            chunks.append(' '.join(chunk_words))
        return chunks

    # Build final chunk list
    final_chunks: List[Dict] = []
    for chunk_str in chunk_text(full_text):
        financial_flag = bool(re.search(r"\$[\d,]+|\d+%|\d+\.\d+", chunk_str))
        final_chunks.append({
            'text': chunk_str,
            'element_type': 'chunk',
            'filing_type': Path(file_path).stem.upper(),
            'chunk_length': len(chunk_str),
            'word_count': len(chunk_str.split()),
            'has_financial_data': financial_flag
        })

    logger.info(f"Parsed {len(final_chunks)} overlapping chunks from {file_path}")
    return final_chunks
