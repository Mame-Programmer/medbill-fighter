# MedBill Fighter

Find possible errors in medical bills and insurance denials, and generate a ready-to-edit dispute letter.

Americans routinely receive bills with duplicate charges, unbundled codes, totals that don't add up, and denials that can be appealed. Most people never challenge them because the paperwork is confusing. MedBill Fighter turns a pasted bill or EOB into a short list of specific questions to ask, plus a draft letter that asks them.

> **Not legal, medical, or tax advice.** Every finding is a question to put to the provider or insurer, not proof of an error.

## What it does

- Reads a bill from pasted text, a **text PDF**, or a **photo/screenshot** (PNG or JPG, via OCR) and shows the extracted text so you can correct it before analyzing
- Parses itemized bill lines (optional date, CPT/HCPCS code, description, quantity, first money column as the charge)
- Flags: duplicate charges, unbundled panel components, multiple office-visit codes on one day, total mismatches, unusually large charges
- Explains common denial reason codes (e.g. CO-50 not medically necessary, CO-197 authorization absent) and what to do about each
- Notes possible No Surprises Act protection for out-of-network emergency care
- Writes a dispute letter (template offline, or tailored with Claude)

## Design decisions

- **Rules find problems, the LLM only writes.** Findings come from deterministic, testable rules (`app/analyzer.py`), so they're explainable and don't hallucinate. The model only drafts the letter from those findings.
- **Offline first.** Works with no API keys. Set `MEDBILL_PROVIDER=anthropic` to use Claude for the letter.
- **Uploads are processed in memory and never stored.** File type is decided from the file's first bytes, not its name; size and page limits apply.
- **Privacy by default.** Text is redacted (SSN, phone, email, dates, IDs, addresses) before it is sent to any model provider (`app/redact.py`). Nothing is stored.
- **Honest scope.** Output is framed as questions and requests, with a disclaimer.

```
paste text -> parse items -> rule checks -> findings -> (redact) -> letter
                                            \-> denial-code explainer
```

## Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt

# CLI
python -m app.cli samples/sample_bill.txt
python -m app.cli samples/sample_denial.txt

# Web app
uvicorn app.main:app --reload     # open http://127.0.0.1:8000

# Optional: photo upload (OCR). PDFs work without this.
brew install tesseract            # Ubuntu: sudo apt-get install tesseract-ocr
pip install -r requirements-ocr.txt

# Or run everything, OCR included, in Docker
docker build -t medbill-fighter . && docker run -p 8000:8000 medbill-fighter

# Use Claude for the letter
cp .env.example .env              # add ANTHROPIC_API_KEY, set MEDBILL_PROVIDER=anthropic
export $(grep -v '^#' .env | xargs)
python -m app.cli samples/sample_bill.txt --provider anthropic
```

**Known limits:** photo reading depends on image quality, so the page shows the extracted text for review before analysis. Scanned PDFs with no text layer are rejected with a message asking for a photo instead.

## Tests

```bash
pytest -q
ruff check .
```

## Roadmap

- OCR for scanned PDFs (today: text PDFs and photos only)
- Measure OCR accuracy on real, de-identified bills
- Payer-specific appeal deadlines and templates by state
- Price benchmarking against published rates (hospital price transparency files)
- Account system, case tracking, reminders for appeal deadlines
- Evaluation set of real (de-identified) bills to measure precision of each rule

See [docs/BUSINESS.md](docs/BUSINESS.md) for the business plan and validation steps.

## License

MIT
