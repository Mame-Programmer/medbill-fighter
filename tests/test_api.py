from pathlib import Path

from fastapi.testclient import TestClient

from app.extract import MAX_BYTES
from app.main import app

from .helpers import BILL_LINES, make_pdf

client = TestClient(app)
SAMPLES = Path(__file__).parent.parent / "samples"


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_analyze_sample_bill():
    r = client.post("/api/analyze", json={"text": (SAMPLES / "sample_bill.txt").read_text()})
    assert r.status_code == 200
    body = r.json()
    assert body["analysis"]["findings"]
    assert body["letter"]["source"] == "template"


def test_rejects_unparseable_text():
    r = client.post("/api/analyze", json={"text": "hello this is just some random text with no codes"})
    assert r.status_code == 422


def test_anthropic_provider_requires_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/analyze", json={"text": (SAMPLES / "sample_bill.txt").read_text(), "provider": "anthropic"})
    assert r.status_code == 400


def test_index_served():
    assert client.get("/").status_code == 200


def test_capabilities():
    body = client.get("/api/capabilities").json()
    assert body["pdf"] is True and isinstance(body["photo"], bool) and body["max_mb"] == 8


def test_extract_pdf_then_analyze():
    pdf = make_pdf(BILL_LINES)
    r = client.post("/api/extract", files={"file": ("bill.pdf", pdf, "application/pdf")})
    assert r.status_code == 200
    text = r.json()["text"]
    assert "85025" in text
    r2 = client.post("/api/analyze", json={"text": text})
    assert r2.status_code == 200 and r2.json()["analysis"]["findings"]


def test_extract_ignores_filename_and_content_type():
    r = client.post("/api/extract", files={"file": ("bill.pdf", b"MZ\x90\x00 not a pdf at all", "application/pdf")})
    assert r.status_code == 422
    assert "Unsupported" in r.json()["detail"]


def test_extract_rejects_oversize_file():
    big = b"%PDF-" + b"0" * (MAX_BYTES + 10)
    r = client.post("/api/extract", files={"file": ("big.pdf", big, "application/pdf")})
    assert r.status_code == 422
    assert "too large" in r.json()["detail"]


def test_extract_requires_a_file():
    assert client.post("/api/extract").status_code == 422
