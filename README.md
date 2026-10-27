# MedBill Fighter

Find possible errors in medical bills and insurance denials, and generate a ready-to-edit dispute letter.

Americans routinely receive bills with duplicate charges, unbundled codes, totals that don't add up, and denials that can be appealed. Most people never challenge them because the paperwork is confusing. MedBill Fighter turns a pasted bill or EOB into a short list of specific questions to ask, plus a draft letter that asks them.

> **Not legal, medical, or tax advice.** Every finding is a question to put to the provider or insurer, not proof of an error.

## What it does

- Parses itemized bill lines (date, CPT/HCPCS code, description, quantity, amount)
- Flags: duplicate charges, unbundled panel components, multiple office-visit codes on one day, total mismatches, unusually large charges
- Explains common denial reason codes (e.g. CO-50 not medically necessary, CO-197 authorization absent) and what to do about each
- Notes possible No Surprises Act protection for out-of-network emergency care
- Writes a dispute letter (template offline, or tailored with Claude)

## Design decisions

- **Rules find problems, the LLM only writes.** Findings come from deterministic, testable rules (`app/analyzer.py`), so they're explainable and don't hallucinate. The model only drafts the letter from those findings.
- **Offline first.** Works with no API keys. Set `MEDBILL_PROVIDER=anthropic` to use Claude for the letter.
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

# Use Claude for the letter
cp .env.example .env              # add ANTHROPIC_API_KEY, set MEDBILL_PROVIDER=anthropic
export $(grep -v '^#' .env | xargs)
python -m app.cli samples/sample_bill.txt --provider anthropic
```

## Tests

```bash
pytest -q
ruff check .
```

## Roadmap

- PDF and photo upload (OCR) of bills and EOBs
- Payer-specific appeal deadlines and templates by state
- Price benchmarking against published rates (hospital price transparency files)
- Account system, case tracking, reminders for appeal deadlines
- Evaluation set of real (de-identified) bills to measure precision of each rule

See [docs/BUSINESS.md](docs/BUSINESS.md) for the business plan and validation steps.

## License

MIT
