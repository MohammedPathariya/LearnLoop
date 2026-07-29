from io import BytesIO


MAX_PDF_BYTES = 20 * 1024 * 1024


def extract_pdf_text(pdf_bytes: bytes) -> str:
    if not pdf_bytes:
        raise ValueError("PDF is empty")
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("PDF must be 20 MB or smaller")

    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "PDF support is not installed. Run: python3.11 -m pip install -r backend/requirements.txt"
        ) from exc

    try:
        reader = PdfReader(BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ValueError("The uploaded file is not a readable PDF") from exc

    text = "\n\n".join(page.strip() for page in pages if page.strip()).strip()
    if not text:
        raise ValueError("This PDF does not contain selectable text")
    return text
