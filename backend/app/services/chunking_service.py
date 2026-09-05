from dataclasses import dataclass
from typing import List
from app.services.pdf_service import PageContent
import re

@dataclass
class ChunkMetadata:
    document_id: str
    document_name: str
    page_number: int
    section: str
    chunk_index: int
    paragraph_index: int
    text: str

def chunk_document(pages: List[PageContent], document_id: str, document_name: str, chunk_size: int, chunk_overlap: int) -> List[ChunkMetadata]:
    chunks = []
    chunk_index = 0
    
    for page in pages:
        if page.is_empty:
            continue
            
        current_section = page.sections[0] if page.sections else "Unknown"
        paragraphs = re.split(r'\n\s*\n', page.text)
        
        paragraph_index = 0
        for para in paragraphs:
            para = para.strip()
            if len(para) < 20:
                continue
                
            if len(para) <= chunk_size:
                chunks.append(ChunkMetadata(
                    document_id=document_id,
                    document_name=document_name,
                    page_number=page.page_number,
                    section=current_section,
                    chunk_index=chunk_index,
                    paragraph_index=paragraph_index,
                    text=para
                ))
                chunk_index += 1
            else:
                sentences = re.split(r'(?<=\.)\s+', para)
                current_chunk_text = ""
                
                for sentence in sentences:
                    if len(current_chunk_text) + len(sentence) > chunk_size and current_chunk_text:
                        chunks.append(ChunkMetadata(
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page.page_number,
                            section=current_section,
                            chunk_index=chunk_index,
                            paragraph_index=paragraph_index,
                            text=current_chunk_text.strip()
                        ))
                        chunk_index += 1
                        # Apply overlap
                        overlap_start = max(0, len(current_chunk_text) - chunk_overlap)
                        current_chunk_text = current_chunk_text[overlap_start:] + " " + sentence
                    else:
                        current_chunk_text += (" " + sentence if current_chunk_text else sentence)
                
                if current_chunk_text:
                    if len(current_chunk_text.strip()) >= 20:
                        chunks.append(ChunkMetadata(
                            document_id=document_id,
                            document_name=document_name,
                            page_number=page.page_number,
                            section=current_section,
                            chunk_index=chunk_index,
                            paragraph_index=paragraph_index,
                            text=current_chunk_text.strip()
                        ))
                        chunk_index += 1
            paragraph_index += 1
            
    return chunks
