"""Turn an uploaded bill (PDF or photo) into plain text.

- PDFs with a text layer are read directly with pypdf (fast, accurate, offline).
- Photos and screenshots go through Tesseract OCR when it is installed.
- Scanned PDFs (no text layer) are not supported yet; the error says what to do.

Files are processed in memory and never written to disk or stored.
The file type is decided from the file's first bytes, not its name or the
Content-Type header, because those are controlled by whoever uploads the file.
"""
from __future__ import annotations

import io
import shutil

MAX_BYTES = 8 * 1024 * 1024  # 8 MB
MAX_PDF_PAGES = 20
MAX_IMAGE_PIXELS = 25_000_000
MIN_PDF_TEXT_CHARS = 30  # below this we assume the PDF is a scan with no text layer

_PNG = b"\x89PNG\r\n\x1a\n"
_JPEG = b"\xff\xd8\xff"


class ExtractionError(ValueError):
    """A problem the user can understand and fix. The message is safe to show."""


def sniff_type(data: bytes) -> str | None:
    if data.startswith(b"%PDF-"):
        return "pdf"
    if data.startswith((_PNG, _JPEG)):
        return "image"
    return None


def extract_text(data: bytes) -> str:
    if not data:
        raise ExtractionError("The file is empty.")
    if len(data) > MAX_BYTES:
        raise ExtractionError(f"The file is too large. The limit is {MAX_BYTES // (1024 * 1024)} MB.")
    kind = sniff_type(data)
    if kind == "pdf":
        return _pdf_text(data)
    if kind == "image":
        return _image_text(data)
    raise ExtractionError("Unsupported file. Upload a PDF, PNG or JPG, or paste the bill text instead.")


def _pdf_text(data: bytes) -> str:
    from pypdf import PdfReader
    from pypdf.errors import PyPdfError

    try:
        reader = PdfReader(io.BytesIO(data))
        if reader.is_encrypted:
            raise ExtractionError("This PDF is password protected. Remove the password and try again.")
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ExtractionError(f"This PDF has more than {MAX_PDF_PAGES} pages. Upload only the pages with charges.")
        text = "\n".join((page.extract_text() or "") for page in reader.pages)
    except ExtractionError:
        raise
    except (PyPdfError, ValueError, KeyError, OSError, RecursionError) as exc:
        raise ExtractionError("Could not read this PDF. Try a photo of the bill, or paste the text.") from exc

    if len(text.strip()) < MIN_PDF_TEXT_CHARS:
        raise ExtractionError(
            "This PDF looks like a scan with no readable text. "
            "Take a clear photo or screenshot of the bill and upload that instead."
        )
    return text


def ocr_available() -> bool:
    if shutil.which("tesseract") is None:
        return False
    try:
        import pytesseract  # noqa: F401
        from PIL import Image  # noqa: F401
    except ImportError:
        return False
    return True


def _image_text(data: bytes) -> str:
    if not ocr_available():
        raise ExtractionError(
            "Photo reading is not enabled on this server. Upload a text PDF or paste the bill text."
        )
    import pytesseract
    from PIL import Image, ImageOps, UnidentifiedImageError

    try:
        Image.MAX_IMAGE_PIXELS = MAX_IMAGE_PIXELS
        img = Image.open(io.BytesIO(data))
        img.load()
        img = ImageOps.exif_transpose(img)  # phone photos are often rotated by metadata
        img = ImageOps.autocontrast(img.convert("L"))
        # --psm 6: treat the page as a uniform block of text, which suits itemized tables.
        text = pytesseract.image_to_string(img, config="--psm 6")
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise ExtractionError("Could not read this image. Try a sharper, well-lit photo.") from exc
    except pytesseract.TesseractError as exc:
        raise ExtractionError("Photo reading failed. Try a clearer image or paste the text.") from exc

    if len(text.strip()) < MIN_PDF_TEXT_CHARS:
        raise ExtractionError("No readable text found. Retake the photo closer, flat and well lit.")
    return text
