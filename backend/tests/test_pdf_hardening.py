import pytest
import base64
from fastapi import HTTPException
from pydantic import ValidationError
from routers.resume import ExtractTextRequest, ATSCheckRequest
from services.pdf_service import extract_text_from_pdf_base64, MAX_PDF_PAGES


def test_oversized_base64_rejected_by_pydantic_schema():
    """Verify that payload exceeding MAX_BASE64_PDF_LEN fails validation with 422."""
    huge_str = "A" * (8 * 1024 * 1024)  # 8MB base64 exceeds 5MB * 1.4 + 1000
    with pytest.raises(ValidationError):
        ExtractTextRequest(pdf_base64=huge_str)

    with pytest.raises(ValidationError):
        ATSCheckRequest(resume_pdf=huge_str, job_description="Python developer")


def test_non_pdf_magic_bytes_rejected():
    """Verify that decoded content without %PDF- magic bytes raises ValueError."""
    fake_pdf = b"NOT_A_REAL_PDF_JUST_TEXT"
    b64 = base64.b64encode(fake_pdf).decode("utf-8")
    with pytest.raises(ValueError, match="Invalid file format"):
        extract_text_from_pdf_base64(b64)


def test_pdf_page_cap_respected():
    """Verify that a synthetic PDF with many pages is parsed up to MAX_PDF_PAGES."""
    import fitz
    doc = fitz.open()
    for i in range(15):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i + 1} test content with enough words to be counted")
    pdf_bytes = doc.tobytes()
    doc.close()

    b64 = base64.b64encode(pdf_bytes).decode("utf-8")
    extracted = extract_text_from_pdf_base64(b64)
    assert "Page 1" in extracted
    assert "Page 10" in extracted
    # Page 11 and above should not be included due to MAX_PDF_PAGES = 10
    assert "Page 11" not in extracted
    assert "Page 15" not in extracted
