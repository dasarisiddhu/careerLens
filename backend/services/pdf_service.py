# ============================================================
# CareerLens – PDF Service (Hardened)
# File: backend/services/pdf_service.py
# ============================================================
import base64
import io
import logging
from config import settings

logger = logging.getLogger("careerlens.pdf")

MAX_PDF_PAGES = 10
MAX_OCR_PAGES = 5


def extract_text_from_pdf_base64(pdf_base64: str) -> str:
    """
    Extract plain text from a base64-encoded PDF.
    Validates magic bytes, bounds size, caps processed pages,
    and falls back through PyMuPDF, pdfplumber, PyPDF2, pypdf, pdfminer, and OCR.
    """
    if not pdf_base64 or not isinstance(pdf_base64, str):
        raise ValueError("No PDF data provided.")

    # ── Clean base64 string ──────────────────────────────────
    if "," in pdf_base64:
        pdf_base64 = pdf_base64.split(",", 1)[1]
    pdf_base64 = pdf_base64.strip().replace(" ", "").replace("\n", "").replace("\r", "")

    # Fix base64 padding
    missing_padding = len(pdf_base64) % 4
    if missing_padding:
        pdf_base64 += "=" * (4 - missing_padding)

    # ── Enforce size before decode (F2) ──────────────────────
    max_bytes = settings.MAX_RESUME_SIZE_MB * 1024 * 1024
    if (len(pdf_base64) * 3) // 4 > max_bytes:
        raise ValueError(f"Decoded PDF size exceeds maximum limit of {settings.MAX_RESUME_SIZE_MB}MB.")

    try:
        raw_bytes = base64.b64decode(pdf_base64)
    except Exception as e:
        logger.error(f"Base64 decode failed: {e}")
        raise ValueError("Invalid base64 PDF data.")

    # ── Enforce size and magic bytes ──────────────────────────
    if len(raw_bytes) > max_bytes:
        raise ValueError(f"Decoded PDF size exceeds maximum limit of {settings.MAX_RESUME_SIZE_MB}MB.")

    if not raw_bytes.startswith(b"%PDF-"):
        raise ValueError("Invalid file format. File must be a valid PDF starting with %PDF- header.")

    ocr_unavailable_reason = ""

    # ── Method 1: PyMuPDF (fitz) — best for browser-printed PDFs ──
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        pages = []
        for idx, page in enumerate(doc):
            if idx >= MAX_PDF_PAGES:
                logger.info(f"PyMuPDF page cap reached ({MAX_PDF_PAGES} pages)")
                break
            text = page.get_text("text")
            if text and text.strip():
                pages.append(text.strip())
        doc.close()
        result = "\n\n".join(pages).strip()
        if result and len(result) > 30:
            logger.info(f"PyMuPDF extracted {len(result)} chars")
            return result
        logger.warning("PyMuPDF returned empty text, trying next method")
    except ImportError:
        logger.warning("PyMuPDF (fitz) not installed, trying pdfplumber")
    except Exception as e:
        logger.warning(f"PyMuPDF failed: {e}")

    # ── Method 2: pdfplumber ─────────────────────────────────
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
            pages = []
            for page in pdf.pages[:MAX_PDF_PAGES]:
                text = page.extract_text(x_tolerance=3, y_tolerance=3)
                if text:
                    pages.append(text.strip())
            result = "\n\n".join(pages).strip()
            if result and len(result) > 30:
                logger.info(f"pdfplumber extracted {len(result)} chars")
                return result
            logger.warning("pdfplumber returned empty text, trying next method")
    except ImportError:
        logger.warning("pdfplumber not installed, trying PyPDF2")
    except Exception as e:
        logger.warning(f"pdfplumber failed: {e}")

    # ── Method 3: PyPDF2 ─────────────────────────────────────
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages[:MAX_PDF_PAGES]:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        result = "\n\n".join(pages).strip()
        if result and len(result) > 30:
            logger.info(f"PyPDF2 extracted {len(result)} chars")
            return result
        logger.warning("PyPDF2 returned empty text, trying next method")
    except ImportError:
        logger.warning("PyPDF2 not installed, trying pypdf")
    except Exception as e:
        logger.warning(f"PyPDF2 failed: {e}")

    # ── Method 4: pypdf ───────────────────────────────────────
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(raw_bytes))
        pages = []
        for page in reader.pages[:MAX_PDF_PAGES]:
            text = page.extract_text()
            if text:
                pages.append(text.strip())
        result = "\n\n".join(pages).strip()
        if result and len(result) > 30:
            logger.info(f"pypdf extracted {len(result)} chars")
            return result
        logger.warning("pypdf returned empty text, trying pdfminer")
    except ImportError:
        logger.warning("pypdf not installed, trying pdfminer")
    except Exception as e:
        logger.warning(f"pypdf failed: {e}")

    # ── Method 5: pdfminer ────────────────────────────────────
    try:
        from pdfminer.high_level import extract_text as pdfminer_extract
        result = pdfminer_extract(io.BytesIO(raw_bytes), maxpages=MAX_PDF_PAGES).strip()
        if result and len(result) > 30:
            logger.info(f"pdfminer extracted {len(result)} chars")
            return result
        logger.warning("pdfminer returned empty text")
    except ImportError:
        logger.warning("pdfminer not installed")
    except Exception as e:
        logger.warning(f"pdfminer failed: {e}")

    # ── Method 6: OCR Fallback (capped to MAX_OCR_PAGES) ───────
    try:
        import fitz  # PyMuPDF
        import pytesseract
        from PIL import Image

        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            ocr_unavailable_reason = (
                "OCR is not available because the Tesseract executable is not installed "
                "or is not on PATH."
            )
            raise RuntimeError(ocr_unavailable_reason) from e

        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        pages = []
        for page_number, page in enumerate(doc):
            if page_number >= MAX_OCR_PAGES:
                logger.info(f"OCR page cap reached ({MAX_OCR_PAGES} pages)")
                break
            try:
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                text = pytesseract.image_to_string(img)
                if text and text.strip():
                    pages.append(text.strip())
                else:
                    logger.warning(f"OCR returned empty text for page {page_number + 1}")
            except Exception as page_err:
                logger.warning(f"OCR failed for page {page_number + 1}: {page_err}")
        doc.close()

        result = "\n\n".join(pages).strip()
        if result and len(result) > 30:
            logger.info(f"OCR extracted {len(result)} chars from scanned PDF")
            return result
        logger.warning("OCR fallback returned empty text")
    except ImportError as e:
        ocr_unavailable_reason = f"OCR dependencies missing: {e}"
        logger.warning(ocr_unavailable_reason)
    except Exception as e:
        logger.warning(f"OCR fallback failed: {e}")

    hint = f" {ocr_unavailable_reason}" if ocr_unavailable_reason else ""
    raise ValueError(
        "Could not extract text from this PDF. "
        "It may be a scanned/image-based or password-protected file. "
        f"{hint} Please paste your resume text manually."
    )


# Alias for backwards compatibility
extract_text_from_pdf = extract_text_from_pdf_base64
