from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

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
