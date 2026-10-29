"""FastAPI app: POST /api/analyze with pasted bill/denial text."""
from pathlib import Path
from typing import Annotated

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .analyzer import analyze
from .extract import MAX_BYTES, ExtractionError, extract_text, ocr_available
from .letters import build_letter
from .llm import get_provider

STATIC = Path(__file__).parent / "static"
MAX_CHARS = 20_000

app = FastAPI(title="MedBill Fighter", version="0.1.0")


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=20, max_length=MAX_CHARS)
    provider: str | None = None  # "offline" (default) or "anthropic"


@app.post("/api/analyze")
def api_analyze(req: AnalyzeRequest):
    analysis = analyze(req.text)
    if not analysis.items and not analysis.denial_codes:
        raise HTTPException(
            422,
            "Could not find any line items or denial codes. Paste the itemized bill or the EOB text.",
        )
    try:
        provider = get_provider(req.provider)
    except RuntimeError as e:
        raise HTTPException(400, str(e))
    return {"analysis": analysis.to_dict(), "letter": build_letter(analysis, provider)}


@app.post("/api/extract")
def api_extract(file: Annotated[UploadFile, File()]):
    """Read a PDF or photo and return its text so the user can check it before analyzing.

    Declared as a plain `def` so FastAPI runs it in a worker thread; OCR is CPU-heavy.
    """
    data = file.file.read(MAX_BYTES + 1)  # never read more than the limit allows
    try:
        text = extract_text(data)
    except ExtractionError as e:
        raise HTTPException(422, str(e))
    return {"text": text[:MAX_CHARS], "truncated": len(text) > MAX_CHARS}


@app.get("/api/capabilities")
def capabilities():
    return {"pdf": True, "photo": ocr_available(), "max_mb": MAX_BYTES // (1024 * 1024)}


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
