"""
pdf_ocr_reader.py
-----------------
OCR-based PDF reader for scanned/image-based PDFs (marks cards, invoices,
forms, etc.) that have no extractable text.

Uses EasyOCR with PyMuPDF rendering to extract text from scanned pages.
This is the fallback for PDFs that pdf_smart_reader detects as scanned
documents (many vector lines from table borders, but zero extractable text).
"""

import fitz
import numpy as np

# Lazy-load the OCR reader to avoid slow startup
_ocr_reader = None

def _get_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _ocr_reader


def read_pdf_ocr(path: str) -> str:
    """Render each page of a scanned PDF and OCR the text."""
    doc = fitz.open(path)
    all_text = []

    for page_no, page in enumerate(doc, 1):
        # Render at 300 DPI for good OCR quality
        pix = page.get_pixmap(dpi=300)
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(
            pix.height, pix.width, pix.n
        )
        # EasyOCR expects RGB
        if pix.n == 4:  # RGBA
            img_array = img_array[:, :, :3]

        reader = _get_reader()
        results = reader.readtext(img_array, detail=1, paragraph=False)

        # Sort results by vertical position (top to bottom), then left to right
        # Each result is (bbox, text, confidence)
        results.sort(key=lambda r: (round(r[0][0][1] / 15), r[0][0][0]))

        page_lines = []
        current_y = -1
        current_line = []

        for bbox, text, conf in results:
            if conf < 0.2:  # Skip very low confidence
                continue
            y = round(bbox[0][1] / 15)  # Group by approximate row
            if y != current_y and current_line:
                page_lines.append(" ".join(current_line))
                current_line = []
            current_y = y
            current_line.append(text)

        if current_line:
            page_lines.append(" ".join(current_line))

        if page_lines:
            all_text.append(f"=== PAGE {page_no} ===")
            all_text.extend(page_lines)
            all_text.append("")

    return "\n".join(all_text)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_ocr_reader.py <file.pdf>")
        raise SystemExit(1)
    print(read_pdf_ocr(sys.argv[1]))
