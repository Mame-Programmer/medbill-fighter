"""Command line: python -m app.cli samples/sample_bill.txt [--provider anthropic]"""
import argparse
import json
import sys

from .analyzer import analyze
from .letters import build_letter
from .llm import get_provider


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Analyze a medical bill or denial for possible problems.")
    p.add_argument("file", help="Text file containing the bill or EOB/denial text")
    p.add_argument("--provider", default=None, help="offline (default) or anthropic")
    p.add_argument("--json", action="store_true", help="Print raw JSON")
    args = p.parse_args(argv)

    text = open(args.file, encoding="utf-8").read()
    analysis = analyze(text)
    letter = build_letter(analysis, get_provider(args.provider))

    if args.json:
        print(json.dumps({"analysis": analysis.to_dict(), "letter": letter}, indent=2))
        return 0

    print(f"Parsed {len(analysis.items)} line items; computed total ${analysis.computed_total:,.2f}")
    if analysis.stated_total is not None:
        print(f"Stated total: ${analysis.stated_total:,.2f}")
    print(f"\n{len(analysis.findings)} finding(s):")
    for f in analysis.findings:
        print(f"  [{f.severity.upper():6}] {f.title}\n           {f.detail}")
    if letter["letter"]:
        print("\n--- DRAFT LETTER ---\n")
        print(letter["letter"])
        print(f"\n({letter['disclaimer']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
