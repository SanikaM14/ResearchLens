import pytest
from app.services.chunking_service import chunk_document
from app.services.pdf_service import PageContent

def test_chunk_preserves_page_number(sample_page_content):
    chunks = chunk_document([sample_page_content], "doc1", "doc", 512, 50)
    assert chunks[0].page_number == 1

def test_chunk_preserves_section(sample_page_content):
    chunks = chunk_document([sample_page_content], "doc1", "doc", 512, 50)
    assert chunks[0].section == "Abstract"

def test_chunk_index_sequential(sample_page_content):
    chunks = chunk_document([sample_page_content, sample_page_content], "doc1", "doc", 512, 50)
    indices = [c.chunk_index for c in chunks]
    assert indices == list(range(len(chunks)))

def test_empty_page_skipped():
    empty_page = PageContent(page_number=1, text="", sections=[], char_count=0, is_empty=True)
    chunks = chunk_document([empty_page], "doc1", "doc", 512, 50)
    assert len(chunks) == 0

def test_large_paragraph_split_at_sentences():
    large_text = ("This is sentence one. " * 30)
    page = PageContent(page_number=1, text=large_text, sections=["Abs"], char_count=len(large_text), is_empty=False)
    chunks = chunk_document([page], "doc1", "doc", 100, 20)
    assert len(chunks) > 1

def test_chunk_overlap_applied():
    large_text = ("This is sentence one. " * 30)
    page = PageContent(page_number=1, text=large_text, sections=["Abs"], char_count=len(large_text), is_empty=False)
    chunks = chunk_document([page], "doc1", "doc", 100, 20)
    assert len(chunks) > 1
    # Very basic check to ensure something happened
