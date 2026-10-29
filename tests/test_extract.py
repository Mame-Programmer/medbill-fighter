import io

import pytest

from app import extract
from app.analyzer import analyze
from app.extract import (
    MAX_BYTES,
    ExtractionError,
    extract_text,
    ocr_available,
    sniff_type,
)

from .helpers import BILL_LINES, make_pdf


def test_sniff_type_uses_content_not_name():
    assert sniff_type(make_pdf(["hello"])) == "pdf"
    assert sniff_type(b"\x89PNG\r\n\x1a\n" + b"0" * 20) == "image"
    assert sniff_type(b"\xff\xd8\xff\xe0" + b"0" * 20) == "image"
    assert sniff_type(b"MZ\x90\x00 executable") is None
    assert sniff_type(b"<html><script>alert(1)</script>") is None


def test_pdf_text_is_extracted_and_analyzed():
    text = extract_text(make_pdf(BILL_LINES))
    assert "85025" in text and "$448.00" in text
    titles = [f.title.lower() for f in analyze(text).findings]
    assert any("duplicate" in t for t in titles)
    assert any("unbundling" in t for t in titles)


def test_empty_file_rejected():
    with pytest.raises(ExtractionError, match="empty"):
        extract_text(b"")


def test_oversize_file_rejected():
    with pytest.raises(ExtractionError, match="too large"):
        extract_text(b"%PDF-" + b"0" * MAX_BYTES)


def test_unsupported_type_rejected():
    with pytest.raises(ExtractionError, match="Unsupported"):
        extract_text(b"MZ\x90\x00 this is not a bill" * 5)


def test_corrupt_pdf_gives_friendly_error():
    with pytest.raises(ExtractionError):
        extract_text(b"%PDF-1.4\nthis is not really a pdf at all, no objects here\n%%EOF")


def test_pdf_without_text_is_reported_as_scan():
    with pytest.raises(ExtractionError, match="scan"):
        extract_text(make_pdf(["x"]))


def test_pdf_page_limit(monkeypatch):
    monkeypatch.setattr(extract, "MAX_PDF_PAGES", 0)
    with pytest.raises(ExtractionError, match="pages"):
        extract_text(make_pdf(BILL_LINES))


def test_image_without_ocr_gives_clear_message(monkeypatch):
    monkeypatch.setattr(extract, "ocr_available", lambda: False)
    with pytest.raises(ExtractionError, match="not enabled"):
        extract_text(b"\x89PNG\r\n\x1a\n" + b"0" * 64)


@pytest.mark.skipif(not ocr_available(), reason="Tesseract not installed")
def test_photo_ocr_reads_bill_lines():
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (1500, 420), "white")
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default(size=34)
    for i, line in enumerate(BILL_LINES[2:6]):
        draw.text((30, 20 + i * 70), line, fill="black", font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    text = extract_text(buf.getvalue())
    assert "85025" in text and "210.00" in text


@pytest.mark.skipif(not ocr_available(), reason="Tesseract not installed")
def test_blank_photo_reports_no_text():
    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (300, 200), "white").save(buf, format="PNG")
    with pytest.raises(ExtractionError, match="No readable text"):
        extract_text(buf.getvalue())
