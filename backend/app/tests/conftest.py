import pytest
from app.services.pdf_service import PageContent
from fastapi import UploadFile

class MockFile:
    def __init__(self, filename, content=b'%PDF-', size=1000):
        self.filename = filename
        self.content = content
        self.size = size
    
    def read(self, size=-1):
        return self.content
    
    def seek(self, pos):
        pass

@pytest.fixture
def sample_page_content():
    return PageContent(
        page_number=1,
        text="This is an abstract paragraph.\n\nIt is short.",
        sections=["Abstract"],
        char_count=50,
        is_empty=False
    )

@pytest.fixture
def sample_chunks():
    from app.services.chunking_service import ChunkMetadata
    return [
        ChunkMetadata(
            document_id="doc1", document_name="doc", page_number=1,
            section="Abstract", chunk_index=0, paragraph_index=0, text="This is an abstract paragraph."
        )
    ]

@pytest.fixture
def mock_upload_file():
    file = UploadFile(filename="test.pdf", file=MockFile("test.pdf"))
    file.size = 1000
    return file
