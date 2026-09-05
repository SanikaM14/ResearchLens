import asyncio
import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from dataclasses import dataclass
from typing import List, Dict, Any
import re

@dataclass
class PageContent:
    page_number: int
    text: str
    sections: List[str]
    char_count: int
    is_empty: bool

def _ocr_page(file_path: str, page_num: int) -> str:
    try:
        images = convert_from_path(file_path, first_page=page_num, last_page=page_num, dpi=300)
        if images:
            return pytesseract.image_to_string(images[0])
    except Exception as e:
        print(f"OCR failed for page {page_num}: {e}")
    return ""

async def extract_text_by_page_async(file_path: str) -> List[PageContent]:
    pages_content = []
    
    # Improved regex for section detection (e.g. "1. Introduction", "II. METHODOLOGY")
    section_pattern = re.compile(
        r'^\s*(?:(?:[IVX]+|[0-9]+[\.\)]?)\s*)?'
        r'(abstract|introduction|background|related\s*work|methodology|methods?|'
        r'experimental\s*setup|experiments|results|discussion|conclusion|'
        r'references|limitations|future\s*work|dataset)\b', 
        re.IGNORECASE
    )
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # OCR Fallback for image-based PDFs
            if len(text.strip()) < 50:
                ocr_text = await asyncio.to_thread(_ocr_page, file_path, i + 1)
                text = ocr_text if ocr_text else text
            
            char_count = len(text)
            is_empty = char_count < 50
            
            # Improved section detection
            sections = []
            lines = text.split('\n')
            for line in lines:
                if len(line.strip()) > 3 and len(line.strip()) < 80:
                    if section_pattern.match(line):
                        sections.append(line.strip())

            pages_content.append(PageContent(
                page_number=i + 1,
                text=text,
                sections=sections,
                char_count=char_count,
                is_empty=is_empty
            ))
            
    return pages_content

def validate_pdf(file_path: str) -> Dict[str, Any]:
    try:
        with pdfplumber.open(file_path) as pdf:
            page_count = len(pdf.pages)
        return {"page_count": page_count, "is_valid": True, "error": None}
    except Exception as e:
        return {"page_count": 0, "is_valid": False, "error": str(e)}
