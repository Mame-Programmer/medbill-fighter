"""Strip obvious personal identifiers before any text leaves the machine.

This is a best-effort safety net, not a guarantee. Always tell users what is
sent to the model provider.
"""
import re

_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[SSN]"),
    (re.compile(r"\b(?:\+?1[\s.-]?)?\(?\d{3}\)?[\s.-]\d{3}[\s.-]\d{4}\b"), "[PHONE]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b(0?[1-9]|1[0-2])/(0?[1-9]|[12]\d|3[01])/(19|20)\d{2}\b"), "[DATE]"),
    (re.compile(r"(?i)\b(member|subscriber|policy|claim|account|patient)\s*(id|number|no\.?|#)?\s*[:#]?\s*[A-Z0-9-]{6,}\b"), r"\1 [REDACTED-ID]"),
    (re.compile(r"\b\d{1,5}\s+[A-Za-z0-9.\s]{2,30}\b(?:St|Street|Ave|Avenue|Rd|Road|Blvd|Dr|Drive|Ln|Lane|Ct|Court)\b\.?", re.I), "[ADDRESS]"),
]


def redact(text: str) -> str:
    for pattern, repl in _PATTERNS:
        text = pattern.sub(repl, text)
    return text
