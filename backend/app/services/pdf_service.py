import pdfplumber
import pytesseract
from pdf2image import convert_from_path
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class PageContent:
    page_number: int
    text: str
    sections: List[str]
    char_count: int
    is_empty: bool

def extract_text_by_page(file_path: str) -> List[PageContent]:
    pages_content = []
    academic_sections_keywords = ["abstract", "introduction", "methodology", "methods", "results", "discussion", "conclusion", "references", "limitations", "related work", "future work", "dataset", "experiments"]
    
    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            
            # OCR Fallback for image-based PDFs
            if len(text.strip()) < 50:
                try:
                    # Convert just this specific page to an image (first_page and last_page are 1-indexed)
                    images = convert_from_path(file_path, first_page=i+1, last_page=i+1, dpi=300)
                    if images:
                        ocr_text = pytesseract.image_to_string(images[0])
                        text = ocr_text if ocr_text else text
                except Exception as e:
                    print(f"OCR failed for page {i+1}: {e}")
            
            char_count = len(text)
            is_empty = char_count < 50
            
            # Simple section detection
            sections = []
            lines = text.split('\n')
            for line in lines:
                line_lower = line.strip().lower()
                if len(line_lower) > 3 and len(line_lower) < 40: # likely a heading
                    if any(line_lower.startswith(keyword) or line_lower.endswith(keyword) for keyword in academic_sections_keywords):
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
