"""Small builders for test files, so tests need no binary fixtures or extra libraries."""
from __future__ import annotations


def make_pdf(lines: list[str]) -> bytes:
    """Build a minimal valid one-page PDF with a text layer."""

    def esc(s: str) -> str:
        return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")

    content = "BT /F1 11 Tf 40 760 Td 14 TL\n" + "\n".join(f"({esc(line)}) Tj T*" for line in lines) + "\nET"
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
            "/Resources << /Font << /F1 5 0 R >> >> >>"
        ),
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += f"{i} 0 obj\n{body}\nendobj\n".encode("latin-1")
    xref_at = len(out)
    out += f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode()
    for off in offsets:
        out += f"{off:010d} 00000 n \n".encode()
    out += f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref_at}\n%%EOF\n".encode()
    return bytes(out)


BILL_LINES = [
    "SAMPLE HOSPITAL STATEMENT (fictional)",
    "Date        Code   Description                    Qty  Charge",
    "03/14/2026  80053  Comprehensive metabolic panel  1    $210.00",
    "03/14/2026  84132  Potassium, serum               1    $48.00",
    "03/14/2026  85025  CBC with differential          1    $95.00",
    "03/14/2026  85025  CBC with differential          1    $95.00",
    "TOTAL CHARGES: $448.00",
]
