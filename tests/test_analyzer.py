from pathlib import Path

from app.analyzer import analyze, parse_items
from app.letters import build_letter
from app.llm import OfflineProvider
from app.redact import redact

SAMPLES = Path(__file__).parent.parent / "samples"


def titles(a):
    return [f.title for f in a.findings]


def test_parses_line_items():
    items = parse_items("03/14/2026  99213  Office visit  1  $185.00")
    assert len(items) == 1
    assert items[0].code == "99213" and items[0].amount == 185.00


def test_detects_duplicate_charge():
    text = "03/14/2026  85025  CBC  1  $95.00\n03/14/2026  85025  CBC  1  $95.00"
    assert any("duplicate" in t.lower() for t in titles(analyze(text)))


def test_same_code_different_dates_is_not_duplicate():
    text = "03/14/2026  85025  CBC  1  $95.00\n04/14/2026  85025  CBC  1  $95.00"
    assert not any("duplicate" in t.lower() for t in titles(analyze(text)))


def test_detects_unbundling():
    text = "03/14/2026  80053  CMP  1  $210.00\n03/14/2026  84132  Potassium  1  $48.00"
    assert any("unbundling" in t.lower() for t in titles(analyze(text)))


def test_total_mismatch():
    text = "03/14/2026  99213  Visit  1  $100.00\nTOTAL: $250.00"
    assert any("total" in t.lower() for t in titles(analyze(text)))


def test_total_match_has_no_flag():
    text = "03/14/2026  99213  Visit  1  $100.00\nTOTAL: $100.00"
    assert not any("total does not match" in t.lower() for t in titles(analyze(text)))


def test_denial_codes_explained():
    a = analyze((SAMPLES / "sample_denial.txt").read_text())
    assert set(a.denial_codes) == {"50", "197"}
    assert any("Denial reason 50" in t for t in titles(a))


def test_surprise_billing_flag():
    a = analyze("Emergency room visit, out-of-network provider.\n03/14/2026  99284  ER visit  1  $1,000.00")
    assert any("surprise" in t.lower() for t in titles(a))


def test_clean_bill_has_no_high_findings():
    a = analyze("03/14/2026  99213  Visit  1  $120.00\nTOTAL: $120.00")
    assert not [f for f in a.findings if f.severity == "high"]


def test_letter_template_offline():
    a = analyze((SAMPLES / "sample_bill.txt").read_text())
    letter = build_letter(a, OfflineProvider())
    assert letter["source"] == "template"
    assert "itemized statement" in letter["letter"]
    assert "not legal or medical advice" in letter["disclaimer"]


def test_no_letter_without_findings():
    a = analyze("03/14/2026  99213  Visit  1  $120.00\nTOTAL: $120.00")
    assert build_letter(a, OfflineProvider())["source"] == "none"


def test_redaction():
    out = redact("SSN 123-45-6789 call 214-555-0199 email a@b.com member id: ABC1234567 on 03/14/2026")
    for secret in ["123-45-6789", "214-555-0199", "a@b.com", "ABC1234567", "03/14/2026"]:
        assert secret not in out
