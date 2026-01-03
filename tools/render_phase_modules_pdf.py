#!/usr/bin/env python3
"""Render docs/phase_modules.md into docs/phase_modules.pdf.

This script uses a minimal, dependency-free PDF writer to keep the repo
self-contained and avoid extra runtime dependencies.
"""
from __future__ import annotations

from pathlib import Path
import textwrap

PAGE_WIDTH = 612
PAGE_HEIGHT = 792
LEFT_MARGIN = 72
TOP_MARGIN = 72
FONT_SIZE = 12
LINE_HEIGHT = 14
MAX_LINE_WIDTH = 90


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in text.splitlines():
        if not raw.strip():
            lines.append("")
            continue
        wrapped = textwrap.wrap(raw, width=MAX_LINE_WIDTH, replace_whitespace=False)
        lines.extend(wrapped or [""])
    return lines


def paginate(lines: list[str]) -> list[list[str]]:
    lines_per_page = int((PAGE_HEIGHT - 2 * TOP_MARGIN) / LINE_HEIGHT)
    pages: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        current.append(line)
        if len(current) >= lines_per_page:
            pages.append(current)
            current = []
    if current:
        pages.append(current)
    return pages


def build_content_stream(lines: list[str]) -> bytes:
    parts = ["BT", f"/F1 {FONT_SIZE} Tf", f"{LEFT_MARGIN} {PAGE_HEIGHT - TOP_MARGIN} Td"]
    for line in lines:
        safe = escape_pdf_text(line)
        parts.append(f"({safe}) Tj")
        parts.append(f"0 -{LINE_HEIGHT} Td")
    parts.append("ET")
    content = "\n".join(parts) + "\n"
    return content.encode("utf-8")


def render_pdf(text: str, out_path: Path) -> None:
    lines = wrap_lines(text)
    pages = paginate(lines)

    catalog_id = 1
    pages_id = 2
    next_id = 3
    page_ids = []
    content_ids = []

    for _ in pages:
        page_ids.append(next_id)
        content_ids.append(next_id + 1)
        next_id += 2

    font_id = next_id
    max_id = font_id

    objects: dict[int, bytes] = {}

    objects[catalog_id] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode("utf-8")
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)
    objects[pages_id] = f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode("utf-8")

    for idx, page_lines in enumerate(pages):
        page_id = page_ids[idx]
        content_id = content_ids[idx]
        content = build_content_stream(page_lines)
        objects[content_id] = b"<< /Length %d >>\nstream\n" % len(content) + content + b"endstream"
        page_obj = (
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_WIDTH} {PAGE_HEIGHT}] "
            f"/Contents {content_id} 0 R /Resources << /Font << /F1 {font_id} 0 R >> >> >>"
        )
        objects[page_id] = page_obj.encode("utf-8")

    objects[font_id] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"

    # Write PDF
    offsets: list[int] = [0]
    pdf = bytearray()
    pdf.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    for obj_id in range(1, max_id + 1):
        offsets.append(len(pdf))
        pdf.extend(f"{obj_id} 0 obj\n".encode("utf-8"))
        pdf.extend(objects[obj_id])
        pdf.extend(b"\nendobj\n")

    xref_offset = len(pdf)
    pdf.extend(f"xref\n0 {max_id + 1}\n".encode("utf-8"))
    pdf.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        pdf.extend(f"{offset:010d} 00000 n \n".encode("utf-8"))

    trailer = f"<< /Size {max_id + 1} /Root {catalog_id} 0 R >>"
    pdf.extend(b"trailer\n")
    pdf.extend(trailer.encode("utf-8"))
    pdf.extend(b"\nstartxref\n")
    pdf.extend(f"{xref_offset}\n".encode("utf-8"))
    pdf.extend(b"%%EOF\n")

    out_path.write_bytes(pdf)


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    md_path = base / "docs" / "phase_modules.md"
    pdf_path = base / "docs" / "phase_modules.pdf"
    text = md_path.read_text(encoding="utf-8")
    render_pdf(text, pdf_path)
    print(f"Wrote {pdf_path}")


if __name__ == "__main__":
    main()
