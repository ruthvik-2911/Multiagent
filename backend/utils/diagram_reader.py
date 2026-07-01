"""
diagram_reader.py
------------------
Reader for image files (.png, .jpg, .jpeg, .webp, .bmp).

Uses EasyOCR for fast text extraction from images.
The vision model (qwen2.5vl:3b) is available but NOT used during indexing
because it takes 5-10 minutes per image on CPU. EasyOCR extracts text in seconds.

If you have a GPU and want vision-based analysis, call read_diagram_with_vision().
"""

import numpy as np
from PIL import Image


# Lazy-load the OCR reader to avoid slow startup
_ocr_reader = None

def _get_reader():
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    return _ocr_reader


def read_diagram(path: str) -> str:
    """Extract text from an image using EasyOCR (fast, CPU-friendly)."""
    img = Image.open(path)
    img_array = np.array(img.convert("RGB"))

    reader = _get_reader()
    results = reader.readtext(img_array, detail=1, paragraph=False)

    # Sort by vertical position then left to right
    results.sort(key=lambda r: (round(r[0][0][1] / 15), r[0][0][0]))

    lines = []
    current_y = -1
    current_line = []

    for bbox, text, conf in results:
        if conf < 0.2:
            continue
        y = round(bbox[0][1] / 15)
        if y != current_y and current_line:
            lines.append(", ".join(current_line))
            current_line = []
        current_y = y
        current_line.append(text)

    if current_line:
        lines.append(", ".join(current_line))

    extracted = "\n".join(lines)

    parts = [
        "IMAGE DOCUMENT (text extracted via OCR)",
        f"SOURCE FILE: {path}",
        "",
        extracted if extracted.strip() else "[No readable text found in image]",
    ]
    return "\n".join(parts)


# Quick standalone test:  python backend/utils/diagram_reader.py <image_path>
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python diagram_reader.py <image_path>")
        raise SystemExit(1)
    print(read_diagram(sys.argv[1]))
