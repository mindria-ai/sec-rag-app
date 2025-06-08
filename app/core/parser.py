import re
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
import sec_parser as sp
from unstructured.partition.html import partition_html
from bs4 import BeautifulSoup, Tag, NavigableString
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SectionInfo:
    title: str
    text: str
    start_pos: int
    end_pos: int
    level: int  # 1 for main sections, 2 for subsections
    page_number: Optional[int] = None

class S1ProspectusParser:
    """Enhanced SEC filing parser specifically for S-1, S-1/A, and prospectus documents."""
    
    # Key sections specific to S-1 and prospectus filings
    S1_TARGET_SECTIONS = {
        # Core IPO sections
        'PROSPECTUS SUMMARY': 1,
        'RISK FACTORS': 1,
        'SPECIAL NOTE REGARDING FORWARD-LOOKING STATEMENTS': 1,
        'USE OF PROCEEDS': 1,
        'DIVIDEND POLICY': 1,
        'CAPITALIZATION': 1,
        'DILUTION': 1,
        'SELECTED CONSOLIDATED FINANCIAL DATA': 1,
        'MANAGEMENT\'S DISCUSSION AND ANALYSIS': 1,
        'BUSINESS': 1,
        'MANAGEMENT': 1,
        'EXECUTIVE COMPENSATION': 1,
        'CERTAIN RELATIONSHIPS AND RELATED PARTY TRANSACTIONS': 1,
        'PRINCIPAL STOCKHOLDERS': 1,
        'DESCRIPTION OF CAPITAL STOCK': 1,
        'SHARES ELIGIBLE FOR FUTURE SALE': 1,
        'MATERIAL U.S. FEDERAL INCOME TAX CONSIDERATIONS': 1,
        'UNDERWRITING': 1,
        'LEGAL MATTERS': 1,
        'EXPERTS': 1,
        'WHERE YOU CAN FIND MORE INFORMATION': 1,
        
        # Common subsections
        'THE OFFERING': 2,
        'SUMMARY FINANCIAL DATA': 2,
        'COMPETITIVE STRENGTHS': 2,
        'GROWTH STRATEGY': 2,
        'CORPORATE INFORMATION': 2,
        'IMPLICATIONS OF BEING AN EMERGING GROWTH COMPANY': 2,
    }
    
    def __init__(self):
        self.sections: List[SectionInfo] = []
        self.filing_type: Optional[str] = None
        
    def parse_sec_htm_file(self, file_path: str) -> List[Dict]:
        """Parse S-1/prospectus files with IPO-specific structure detection."""
        try:
            html_content = self._read_file(file_path)
            
            # Determine filing type from content
            self.filing_type = self._detect_filing_type(html_content)
            logger.info(f"Detected filing type: {self.filing_type}")
            
            # Step 1: Clean and preprocess HTML
            cleaned_html = self._clean_html(html_content)
            
            # Step 2: Extract table of contents if present
            toc_sections = self._extract_table_of_contents(cleaned_html)
            
            # Step 3: Extract sections using S-1 specific patterns
            sections = self._extract_s1_sections(cleaned_html, toc_sections)
            
            # Step 4: Parse content into structured chunks
            chunks = self._create_structured_chunks(cleaned_html, sections)
            
            # Step 5: Post-process and validate chunks
            validated_chunks = self._validate_and_clean_chunks(chunks)
            
            logger.info(f"Successfully parsed {len(validated_chunks)} chunks from {len(sections)} sections")
            return validated_chunks
            
        except Exception as e:
            logger.error(f"Failed to parse {file_path}: {str(e)}")
            raise
    
    def _detect_filing_type(self, html_content: str) -> str:
        """Detect the specific type of filing (S-1, S-1/A, or 424B4)."""
        content_upper = html_content.upper()
        
        if 'FORM S-1/A' in content_upper or 'AMENDMENT NO.' in content_upper:
            return 'S-1/A'
        elif 'FORM S-1' in content_upper:
            return 'S-1'
        elif 'FORM 424B4' in content_upper or 'FINAL PROSPECTUS' in content_upper:
            return '424B4'
        elif 'PROSPECTUS' in content_upper:
            return 'PROSPECTUS'
        else:
            return 'UNKNOWN'
    
    def _read_file(self, file_path: str) -> str:
        """Read file with proper encoding handling."""
        encodings = ['utf-8', 'latin1', 'cp1252', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Could not decode file {file_path} with any standard encoding")
    
    def _clean_html(self, html_content: str) -> str:
        """Clean HTML content while preserving structure for S-1 documents."""
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Remove script, style, and meta elements
        for element in soup(["script", "style", "meta", "link"]):
            element.decompose()
        
        # Remove XBRL tags common in SEC filings
        for xbrl_tag in soup.find_all(re.compile(r'^(ix:|us-gaap:|dei:)')):
            xbrl_tag.unwrap()
        
        # Clean up excessive whitespace in text nodes
        for text_node in soup.find_all(text=True):
            if isinstance(text_node, NavigableString):
                cleaned = re.sub(r'\s+', ' ', text_node.strip())
                if cleaned != text_node:
                    text_node.replace_with(cleaned)
        
        return str(soup)
    
    def _extract_table_of_contents(self, html_content: str) -> List[Dict]:
        """Extract table of contents to guide section detection."""
        soup = BeautifulSoup(html_content, 'lxml')
        toc_sections = []
        
        # Look for common TOC patterns in S-1 filings
        toc_patterns = [
            re.compile(r'table\s+of\s+contents', re.IGNORECASE),
            re.compile(r'index', re.IGNORECASE),
        ]
        
        for pattern in toc_patterns:
            # Find elements containing TOC
            toc_elements = soup.find_all(text=pattern)
            
            for toc_element in toc_elements:
                parent = toc_element.parent
                if parent:
                    # Extract section titles and page numbers from TOC
                    toc_content = parent.get_text()
                    sections = self._parse_toc_content(toc_content)
                    toc_sections.extend(sections)
        
        return toc_sections
    
    def _parse_toc_content(self, toc_content: str) -> List[Dict]:
        """Parse table of contents content to extract section information."""
        sections = []
        lines = toc_content.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Match patterns like "Risk Factors ... 15" or "Business ... 45"
            match = re.match(r'^(.+?)\s*\.{2,}\s*(\d+)$', line)
            if match:
                title = match.group(1).strip().upper()
                page_num = int(match.group(2))
                
                if self._is_target_section(title):
                    sections.append({
                        'title': title,
                        'page_number': page_num
                    })
        
        return sections
    
    def _extract_s1_sections(self, html_content: str, toc_sections: List[Dict]) -> List[SectionInfo]:
        """Extract sections using S-1 specific patterns and structure."""
        sections = []
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Method 1: Look for bold/strong section headers
        sections.extend(self._extract_header_sections(soup))
        
        # Method 2: Use regex patterns for section detection
        sections.extend(self._extract_regex_sections(html_content))
        
        # Method 3: Use TOC information to validate sections
        if toc_sections:
            sections = self._validate_with_toc(sections, toc_sections)
        
        # Method 4: Try sec-parser as fallback
        try:
            sp_sections = self._extract_with_sec_parser(html_content)
            sections.extend(sp_sections)
        except Exception as e:
            logger.warning(f"sec-parser failed: {e}")
        
        return self._deduplicate_and_sort_sections(sections)
    
    def _extract_header_sections(self, soup: BeautifulSoup) -> List[SectionInfo]:
        """Extract sections by looking for header elements and bold text."""
        sections = []
        
        # Look for header tags (h1, h2, h3, etc.)
        for header_level, tag_name in enumerate(['h1', 'h2', 'h3', 'h4'], 1):
            headers = soup.find_all(tag_name)
            
            for header in headers:
                title = header.get_text().strip().upper()
                if self._is_target_section(title):
                    # Extract content until next header of same or higher level
                    content = self._extract_section_content(header, tag_name)
                    
                    sections.append(SectionInfo(
                        title=title,
                        text=content,
                        start_pos=0,  # Will be calculated later
                        end_pos=0,
                        level=header_level
                    ))
        
        # Look for bold/strong text that might be section headers
        bold_elements = soup.find_all(['b', 'strong'])
        
        for bold in bold_elements:
            title = bold.get_text().strip().upper()
            if self._is_target_section(title) and len(title) > 5:
                # Extract content after this bold element
                content = self._extract_content_after_element(bold)
                
                if content and len(content) > 100:  # Only if substantial content
                    sections.append(SectionInfo(
                        title=title,
                        text=content,
                        start_pos=0,
                        end_pos=0,
                        level=2
                    ))
        
        return sections
    
    def _extract_regex_sections(self, html_content: str) -> List[SectionInfo]:
        """Extract sections using regex patterns specific to S-1 filings."""
        sections = []
        
        # Common S-1 section patterns
        section_patterns = [
            r'(?:^|\n)\s*([A-Z][A-Z\s&\',.-]{10,80})\s*(?:\n|$)',  # All caps section titles
            r'(?:^|\n)\s*((?:PART|ITEM)\s+[IVX]+[A-Z.\s]*)\s*(?:\n|$)',  # PART I, ITEM 1A, etc.
        ]
        
        for pattern in section_patterns:
            matches = re.finditer(pattern, html_content, re.MULTILINE | re.IGNORECASE)
            
            for match in matches:
                title = match.group(1).strip().upper()
                
                if self._is_target_section(title):
                    start_pos = match.end()
                    
                    # Find the end of this section (next section or end of document)
                    next_match = re.search(pattern, html_content[start_pos:], re.MULTILINE | re.IGNORECASE)
                    end_pos = start_pos + next_match.start() if next_match else len(html_content)
                    
                    content = html_content[start_pos:end_pos].strip()
                    
                    if len(content) > 100:  # Only substantial content
                        sections.append(SectionInfo(
                            title=title,
                            text=content,
                            start_pos=start_pos,
                            end_pos=end_pos,
                            level=1
                        ))
        
        return sections
    
    def _extract_with_sec_parser(self, html_content: str) -> List[SectionInfo]:
        """Try to extract using sec-parser library."""
        sections = []
        
        try:
            # Use appropriate parser based on filing type
            if self.filing_type in ['S-1', 'S-1/A', '424B4']:
                # sec-parser doesn't have specific S-1 parser, so use generic
                elements = sp.Edgar10QParser().parse(html_content)
            else:
                elements = sp.Edgar10QParser().parse(html_content)
            
            tree = sp.TreeBuilder().build(elements)
            
            for node in tree.nodes:
                title = node.text.strip().upper()
                
                if self._is_target_section(title):
                    rendered_text = sp.render(node)
                    
                    sections.append(SectionInfo(
                        title=title,
                        text=rendered_text,
                        start_pos=0,
                        end_pos=0,
                        level=1
                    ))
        
        except Exception as e:
            logger.warning(f"sec-parser extraction failed: {e}")
        
        return sections
    
    def _is_target_section(self, title: str) -> bool:
        """Check if a title matches any of our target S-1 sections."""
        title_clean = re.sub(r'[^\w\s]', '', title.upper()).strip()
        
        # Exact matches
        if title_clean in self.S1_TARGET_SECTIONS:
            return True
        
        # Partial matches for common variations
        partial_matches = [
            ('RISK FACTORS', 'RISK'),
            ('USE OF PROCEEDS', 'USE OF PROCEEDS'),
            ('BUSINESS', 'BUSINESS'),
            ('MANAGEMENT', 'MANAGEMENT'),
            ('DILUTION', 'DILUTION'),
            ('UNDERWRITING', 'UNDERWRITING'),
            ('FINANCIAL DATA', 'FINANCIAL'),
            ('CAPITAL STOCK', 'CAPITAL STOCK'),
            ('EXECUTIVE COMPENSATION', 'COMPENSATION'),
        ]
        
        for full_name, partial in partial_matches:
            if partial in title_clean and len(title_clean) >= len(partial):
                return True
        
        return False
    
    def _extract_section_content(self, header_element: Tag, tag_name: str) -> str:
        """Extract content from header element until next header of same level."""
        content_parts = []
        current = header_element.next_sibling
        
        while current:
            if hasattr(current, 'name') and current.name == tag_name:
                break  # Found next section header
            
            if hasattr(current, 'get_text'):
                text = current.get_text().strip()
                if text:
                    content_parts.append(text)
            elif isinstance(current, NavigableString):
                text = str(current).strip()
                if text:
                    content_parts.append(text)
            
            current = current.next_sibling
        
        return '\n'.join(content_parts)
    
    def _extract_content_after_element(self, element: Tag) -> str:
        """Extract content after a given element until logical break."""
        content_parts = []
        current = element.next_sibling
        content_length = 0
        
        while current and content_length < 10000:  # Limit content length
            if hasattr(current, 'name'):
                if current.name in ['h1', 'h2', 'h3', 'h4']:
                    break  # Stop at next header
                if current.name in ['b', 'strong']:
                    text = current.get_text().strip().upper()
                    if self._is_target_section(text) and len(text) > 5:
                        break  # Stop at next section
            
            if hasattr(current, 'get_text'):
                text = current.get_text().strip()
                if text:
                    content_parts.append(text)
                    content_length += len(text)
            elif isinstance(current, NavigableString):
                text = str(current).strip()
                if text:
                    content_parts.append(text)
                    content_length += len(text)
            
            current = current.next_sibling
        
        return '\n'.join(content_parts)
    
    def _validate_with_toc(self, sections: List[SectionInfo], toc_sections: List[Dict]) -> List[SectionInfo]:
        """Validate extracted sections against table of contents."""
        # This is a placeholder for TOC validation logic
        # In a full implementation, you'd match sections with TOC entries
        return sections
    
    def _deduplicate_and_sort_sections(self, sections: List[SectionInfo]) -> List[SectionInfo]:
        """Remove duplicate sections and sort by importance/order."""
        seen_titles = set()
        unique_sections = []
        
        # Sort by level first (main sections before subsections)
        sections.sort(key=lambda x: (x.level, x.title))
        
        for section in sections:
            if section.title not in seen_titles:
                unique_sections.append(section)
                seen_titles.add(section.title)
        
        return unique_sections
    
    def _create_structured_chunks(self, html_content: str, sections: List[SectionInfo]) -> List[Dict]:
        """Create structured chunks from the extracted sections."""
        chunks = []
        
        if not sections:
            # Fallback: use unstructured to parse the entire document
            return self._fallback_chunking(html_content)
        
        for section in sections:
            # Parse section content with unstructured
            try:
                section_elements = partition_html(text=section.text)
                
                for element in section_elements:
                    text = element.text.strip()
                    
                    if text and len(text) >= 50:  # Minimum chunk size
                        chunks.append({
                            'text': text,
                            'element_type': element.category,
                            'section_title': section.title,
                            'section_level': section.level,
                            'filing_type': self.filing_type,
                            'chunk_length': len(text)
                        })
            
            except Exception as e:
                logger.warning(f"Failed to chunk section {section.title}: {e}")
                # Add the raw section as a single chunk
                if section.text.strip():
                    chunks.append({
                        'text': section.text.strip(),
                        'element_type': 'raw_section',
                        'section_title': section.title,
                        'section_level': section.level,
                        'filing_type': self.filing_type,
                        'chunk_length': len(section.text)
                    })
        
        return chunks
    
    def _fallback_chunking(self, html_content: str) -> List[Dict]:
        """Fallback chunking when section extraction fails."""
        logger.warning("Using fallback chunking method")
        
        try:
            elements = partition_html(text=html_content)
            chunks = []
            
            for element in elements:
                text = element.text.strip()
                
                if text and len(text) >= 50:
                    chunks.append({
                        'text': text,
                        'element_type': element.category,
                        'section_title': 'UNKNOWN',
                        'section_level': 0,
                        'filing_type': self.filing_type,
                        'chunk_length': len(text)
                    })
            
            return chunks
        
        except Exception as e:
            logger.error(f"Fallback chunking failed: {e}")
            return []
    
    def _validate_and_clean_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """Post-process chunks for quality and consistency."""
        validated_chunks = []
        
        for chunk in chunks:
            text = chunk['text']
            
            # Skip very short or very long chunks
            if len(text) < 30 or len(text) > 8000:
                continue
            
            # Skip chunks that are mostly whitespace or special characters
            if len(re.sub(r'[^\w\s]', '', text).strip()) < 20:
                continue
            
            # Clean up text
            cleaned_text = re.sub(r'\s+', ' ', text).strip()
            chunk['text'] = cleaned_text
            chunk['chunk_length'] = len(cleaned_text)
            
            # Add metadata
            chunk['word_count'] = len(cleaned_text.split())
            chunk['has_financial_data'] = bool(re.search(r'\$[\d,]+|\d+%|\d+\.\d+%', cleaned_text))
            
            validated_chunks.append(chunk)
        
        logger.info(f"Validated {len(validated_chunks)} chunks from {len(chunks)} raw chunks")
        return validated_chunks

# Updated main parsing function
def parse_sec_htm_file(file_path: str) -> List[Dict]:
    """Main function to parse S-1, S-1/A, and prospectus files."""
    parser = S1ProspectusParser()
    return parser.parse_sec_htm_file(file_path)