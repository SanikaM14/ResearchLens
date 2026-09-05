import pytest
from app.services.pdf_service import validate_pdf

def test_validate_pdf_invalid_file():
    # Test with non-existent file
    result = validate_pdf("nonexistent_file.pdf")
    assert result["is_valid"] is False
    assert result["page_count"] == 0
    assert "No such file or directory" in result["error"]

def test_validate_pdf_not_a_pdf(tmp_path):
    # Test with a text file masquerading as a PDF
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.write_text("This is not a real PDF file")
    result = validate_pdf(str(fake_pdf))
    assert result["is_valid"] is False
    assert result["page_count"] == 0
