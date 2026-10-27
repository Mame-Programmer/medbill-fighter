"""LLM provider abstraction.

`offline` works with no keys (template output) so anyone can run the project.
`anthropic` writes a more tailored letter using Claude. Text is redacted first.
"""
from __future__ import annotations

import os
from typing import Protocol

from .redact import redact

DEFAULT_MODEL = "claude-sonnet-5-5"

SYSTEM_PROMPT = (
    "You help patients write clear, polite, factual letters disputing medical bills "
    "and insurance denials. Use ONLY the findings provided. Do not invent facts, "
    "diagnoses, dates, or legal claims. You are not a lawyer or doctor; do not give "
    "legal or medical advice. Keep the letter under 350 words, with placeholders in "
    "[square brackets] for anything personal."
)


class Provider(Protocol):
    def complete(self, system: str, prompt: str) -> str: ...


class OfflineProvider:
    """No network. Returns None-like marker so the caller uses the template letter."""

    def complete(self, system: str, prompt: str) -> str:
        return ""


class AnthropicProvider:
    def __init__(self, model: str | None = None):
        import anthropic  # imported lazily so offline mode needs no SDK

        self.client = anthropic.Anthropic()
        self.model = model or os.getenv("MEDBILL_MODEL", DEFAULT_MODEL)

    def complete(self, system: str, prompt: str) -> str:
        msg = self.client.messages.create(
            model=self.model,
            max_tokens=900,
            system=system,
            messages=[{"role": "user", "content": redact(prompt)}],
        )
        return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text").strip()


def get_provider(name: str | None = None) -> Provider:
    name = (name or os.getenv("MEDBILL_PROVIDER", "offline")).lower()
    if name == "anthropic":
        if not os.getenv("ANTHROPIC_API_KEY"):
            raise RuntimeError("MEDBILL_PROVIDER=anthropic requires ANTHROPIC_API_KEY")
        return AnthropicProvider()
    return OfflineProvider()
