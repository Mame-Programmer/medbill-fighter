"""FastAPI app: POST /api/analyze with pasted bill/denial text."""
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from .analyzer import analyze
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


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")
