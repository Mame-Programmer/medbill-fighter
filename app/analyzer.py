"""Rule-based bill and denial analysis. Deterministic, offline, testable.

The LLM is only used afterwards to *write* the appeal letter. Findings come from
rules a human can audit, which keeps the product explainable.
"""
from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict

from .codes import BUNDLES, DENIAL_CODES, EM_CODES, HIGH_CHARGE_THRESHOLD

# e.g. "03/14/2026  99213  Office visit, established patient  1  $185.00"
LINE_RE = re.compile(
    r"^\s*(?:(?P<date>\d{1,2}/\d{1,2}/\d{2,4})\s+)?"
    r"(?P<code>[A-Z]?\d{4}[A-Z\d])\s+"
    r"(?P<desc>.+?)\s+"
    r"(?:(?P<qty>\d{1,3})\s+)?"
    r"\$?(?P<amount>\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s*$"
)
TOTAL_RE = re.compile(r"(?im)^\s*(?:total(?:\s+charges)?|amount\s+due)\s*[:\-]?\s*\$?(?P<amt>\d{1,3}(?:,\d{3})*(?:\.\d{2}))\s*$")
DENIAL_RE = re.compile(r"(?i)\b(?:CO|PR|OA|PI|CARC|reason\s*code|denial\s*code|remark\s*code)[\s:#-]*(\d{1,3})\b")
OON_RE = re.compile(r"(?i)out[\s-]of[\s-]network")
ER_RE = re.compile(r"(?i)\b(emergency|ER\b|emergency room|ambulance)\b")


@dataclass
class LineItem:
    date: str | None
    code: str
    description: str
    qty: int
    amount: float


@dataclass
class Finding:
    severity: str  # "high" | "medium" | "info"
    title: str
    detail: str
    ask: str  # the specific question or request to send


@dataclass
class Analysis:
    items: list[LineItem] = field(default_factory=list)
    stated_total: float | None = None
    computed_total: float = 0.0
    denial_codes: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _money(s: str) -> float:
    return float(s.replace(",", ""))


def parse_items(text: str) -> list[LineItem]:
    items = []
    for line in text.splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        items.append(
            LineItem(
                date=m.group("date"),
                code=m.group("code"),
                description=m.group("desc").strip(),
                qty=int(m.group("qty") or 1),
                amount=_money(m.group("amount")),
            )
        )
    return items


def analyze(text: str) -> Analysis:
    a = Analysis()
    a.items = parse_items(text)
    a.computed_total = round(sum(i.amount for i in a.items), 2)

    tm = TOTAL_RE.search(text)
    if tm:
        a.stated_total = _money(tm.group("amt"))

    a.denial_codes = sorted(set(DENIAL_RE.findall(text)))

    by_date: dict[str | None, list[LineItem]] = defaultdict(list)
    for it in a.items:
        by_date[it.date].append(it)

    # 1. Exact duplicates (same date + code + amount).
    seen: dict[tuple, int] = defaultdict(int)
    for it in a.items:
        seen[(it.date, it.code, it.amount)] += 1
    for (date, code, amount), n in seen.items():
        if n > 1:
            a.findings.append(Finding(
                "high", f"Possible duplicate charge: {code}",
                f"Code {code} appears {n} times on {date or 'the same date'} for ${amount:,.2f} each.",
                f"Please confirm service {code} on {date or 'this date'} was performed {n} times. If not, remove the duplicate charge(s).",
            ))

    # 2. Unbundling (component billed alongside the panel that already includes it).
    for date, group in by_date.items():
        codes = {i.code for i in group}
        for panel, info in BUNDLES.items():
            if panel in codes:
                extras = sorted(codes & set(info["components"]))
                if extras:
                    names = ", ".join(f"{c} ({info['components'][c]})" for c in extras)
                    a.findings.append(Finding(
                        "high", f"Possible unbundling with {panel}",
                        f"{info['name']} ({panel}) already includes: {names}. These were also billed separately on {date or 'the same date'}.",
                        f"Please explain why {', '.join(extras)} were billed separately from {panel} on {date or 'this date'}, or correct the claim.",
                    ))

    # 3. More than one office-visit E/M code on the same date.
    for date, group in by_date.items():
        em = [i.code for i in group if i.code in EM_CODES]
        if len(set(em)) > 1:
            a.findings.append(Finding(
                "medium", "Multiple office-visit codes on one date",
                f"Visit codes {', '.join(sorted(set(em)))} were billed on {date or 'the same date'}.",
                "Please explain why more than one evaluation & management code applies to a single date of service.",
            ))

    # 4. Stated total vs computed total.
    if a.stated_total is not None and a.items and abs(a.stated_total - a.computed_total) > 0.01:
        a.findings.append(Finding(
            "medium", "Total does not match line items",
            f"Line items add up to ${a.computed_total:,.2f} but the statement says ${a.stated_total:,.2f}.",
            "Please send a fully itemized statement that reconciles to the total billed.",
        ))

    # 5. High charges.
    for it in a.items:
        if it.amount >= HIGH_CHARGE_THRESHOLD:
            a.findings.append(Finding(
                "info", f"High single charge: {it.code} (${it.amount:,.2f})",
                f"{it.description} is a large line item.",
                f"Please provide supporting documentation for {it.code} and the contracted/allowed amount under my plan.",
            ))

    # 6. Denial codes.
    for code in a.denial_codes:
        info = DENIAL_CODES.get(code)
        if info:
            a.findings.append(Finding(
                "high", f"Denial reason {code}: {info['meaning']}",
                f"Your document lists reason code {code}. Appeals that address the stated reason directly are the most effective.",
                info["action"],
            ))

    # 7. Out-of-network + emergency context.
    if OON_RE.search(text) and ER_RE.search(text):
        a.findings.append(Finding(
            "info", "Possible surprise-billing protection",
            "The document mentions emergency care and out-of-network billing. Federal law (No Surprises Act) limits balance billing for most emergency services.",
            "Please confirm whether the No Surprises Act applies and bill me only the in-network cost-sharing amount.",
        ))

    return a
