"""
pdf_diagram_reader.py
---------------------
Smart PDF reader that handles BOTH ordinary text PDFs and diagram/flowchart
PDFs.

How it decides:
  - First it tries normal text extraction (pypdf). If the PDF has a healthy
    amount of real text, it is treated as a normal document and that text is
    returned unchanged (same behaviour as before).
  - If the PDF has little/no extractable text (a diagram exported to PDF, or a
    scanned page), each page is RENDERED to a high-resolution image and passed
    through the vision pipeline in diagram_reader.py - including tiling - so a
    dense 50-node workflow PDF gets read as a diagram, not as empty text.

Why rendering helps: a vector diagram PDF carries crisp text and lines, so a
high-DPI render is far sharper than a screenshot, which gives the vision model
a much better chance on dense diagrams.

New dependency: pypdfium2  ->  pip install pypdfium2
Reuses the vision helpers already in diagram_reader.py (no duplicate prompts).
"""

import pypdfium2 as pdfium
from pypdf import PdfReader

from backend.utils import diagram_reader as dr

# If a PDF yields at least this many characters of text, treat it as a normal
# text document (skip the expensive vision path).
TEXT_THRESHOLD = 200

# Render resolution. 200 is a good balance; 300 is sharper but produces much
# larger images (slower, hotter). Raise only if fine text is being missed.
RENDER_DPI = 200

# Tiling for rendered diagram pages. These are independent of the image
# reader's settings because diagram PDFs are the dense case where tiling pays
# off. 2 => 2x2 tiles per page. Raise to 3 for very dense pages (much hotter).
PDF_TILE_GRID = 2


def _pdf_text(path: str) -> str:
    try:
        reader = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in reader.pages)
    except Exception:
        return ""


def _render_pages(path: str, dpi: int = RENDER_DPI):
    pdf = pdfium.PdfDocument(path)
    scale = dpi / 72.0
    pages = []
    for i in range(len(pdf)):
        pages.append(pdf[i].render(scale=scale).to_pil())
    return pages


def _extract_page(img, page_no: int) -> str:
    """Run the diagram_reader vision passes on one rendered page image."""
    parts = [f"=== PAGE {page_no} ==="]

    # Pass 1: overall structure (reuse diagram_reader's prompt + caller)
    parts.append(dr._ask_vision(dr.STRUCTURE_PROMPT, img))

    # Pass 2: tiled detail. Diagram PDFs are dense, so always tile.
    for j, tile in enumerate(dr._tiles(img, PDF_TILE_GRID, dr.TILE_OVERLAP), 1):
        try:
            txt = dr._ask_vision(dr.TILE_PROMPT, tile)
            if txt:
                parts.append(f"[page {page_no} region {j}]\n{txt}")
        except Exception as e:
            parts.append(f"[page {page_no} region {j}] failed: {e}")

    return "\n".join(parts)


def read_pdf_diagram(path: str) -> str:
    """Text PDF -> return its text. Diagram/scanned PDF -> render + vision."""
    text = _pdf_text(path)
    if len(text.strip()) >= TEXT_THRESHOLD:
        return text  # ordinary document; behave like the old read_pdf

    pages = _render_pages(path)
    header = [
        "WORKFLOW DIAGRAM PDF (rendered at high DPI + vision-extracted)",
        f"SOURCE FILE: {path}",
        f"PAGES: {len(pages)}",
        "",
    ]
    body = [_extract_page(img, i) for i, img in enumerate(pages, 1)]
    return "\n".join(header) + "\n\n".join(body)


# Quick test:  python backend/utils/pdf_diagram_reader.py <file.pdf>
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_diagram_reader.py <file.pdf>")
        raise SystemExit(1)
    print(read_pdf_diagram(sys.argv[1]))
