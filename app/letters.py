"""Appeal / dispute letter generation. Template first, LLM polish optional."""
from __future__ import annotations

from .analyzer import Analysis
from .llm import SYSTEM_PROMPT, Provider

DISCLAIMER = (
    "This draft is informational and not legal or medical advice. Review every statement "
    "for accuracy before sending, and keep copies of everything you send."
)


def _template(a: Analysis) -> str:
    lines = [
        "[Your name]",
        "[Your address]",
        "[Date]",
        "",
        "[Provider billing department / Insurance appeals department]",
        "Re: Account/Claim [number], Patient [name], Date(s) of service [dates]",
        "",
        "To whom it may concern,",
        "",
        (
            "I am writing to dispute the charges and/or denial referenced above and to request a review. "
            "After reviewing my statement, I have the following questions and requests:"
        ),
        "",
    ]
    for n, f in enumerate(a.findings, 1):
        lines.append(f"{n}. {f.title}")
        lines.append(f"   {f.detail}")
        lines.append(f"   Request: {f.ask}")
        lines.append("")
    lines += [
        (
            "Please send me a fully itemized statement with CPT/HCPCS codes, a written response to each item above, "
            "and the specific plan provisions or clinical criteria relied upon for any denial. "
            "Please also place my account on hold and do not send it to collections while this review is pending."
        ),
        "",
        "I also request information about my right to an internal appeal and external review.",
        "",
        "Sincerely,",
        "[Your name]",
        "[Phone / email]",
    ]
    return "\n".join(lines)


def build_letter(a: Analysis, provider: Provider) -> dict:
    template = _template(a)
    if not a.findings:
        return {"letter": "", "disclaimer": DISCLAIMER, "source": "none"}
    prompt = (
        "Write a dispute letter using these findings. Keep every numbered request.\n\n"
        + template
    )
    drafted = provider.complete(SYSTEM_PROMPT, prompt)
    if drafted:
        return {"letter": drafted, "disclaimer": DISCLAIMER, "source": "llm"}
    return {"letter": template, "disclaimer": DISCLAIMER, "source": "template"}
