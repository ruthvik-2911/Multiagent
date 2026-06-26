"""
diagram_reader.py
------------------
Vision-based reader for workflow / flowchart diagrams.

It sends a diagram image to a LOCAL Ollama vision model and returns a
structured TEXT description of the workflow (swimlanes, nodes, arrows,
decision branches, pass/fail paths). That text is then embedded and indexed
exactly like any PDF/DOCX/XLSX, so the existing RAG chat can answer questions
about the flow with no changes to the query side.

Big / dense diagrams: vision models downsample the image internally, so fine
text gets lost on large diagrams. To handle this we do TWO passes:
  1. A full-image pass to capture the overall graph structure.
  2. A tiled pass (overlapping crops) to OCR the fine text the global pass
     missed, appended as a DETAIL section.

No new dependencies beyond Pillow (`pip install pillow`); uses `requests`,
matching the rest of the project.
"""

import base64
import io
import requests
from PIL import Image

# ----------------------------------------------------------------------
# CONFIG
# ----------------------------------------------------------------------
OLLAMA_URL = "http://localhost:11434/api/generate"

# Best for dense/structured diagrams. If unavailable or too heavy on your
# machine, change to "llava:7b" (lighter, more widely tested).
VISION_MODEL = "qwen2.5vl:3b"

# Tiling kicks in when the image is larger than this on either side (pixels).
LARGE_SIDE_PX = 900
TILE_GRID = 2
TILE_OVERLAP = 0.12    # fractional overlap so arrows/boxes aren't cut at seams

# How long to wait for the vision model per call (CPU inference can be slow).
REQUEST_TIMEOUT = 600

# ----------------------------------------------------------------------
# PROMPTS
# ----------------------------------------------------------------------
STRUCTURE_PROMPT = """You are analyzing a workflow / flowchart diagram.
Extract its COMPLETE structure as text. Be exhaustive and precise.
Read the EXACT text inside every box. Follow every arrow in its direction.

Use this exact format:

TITLE: <title text, or "none">

SWIMLANES / DEPARTMENTS (the left-side horizontal bands, if any):
- <lane name>

NODES:
- TYPE=<start|process|decision|end|success|fail> | LANE=<lane or "?"> | TEXT="<exact text in the shape>"

CONNECTIONS (one line per arrow):
- "<from text>" --[<arrow label, or empty>]--> "<to text>"

DECISIONS (for every diamond / branch point):
- At "<decision text>": <label1> -> "<target1>"; <label2> -> "<target2>"

Rules:
- Do NOT invent nodes or arrows. Only report what is visible.
- If text is unreadable, write [unreadable].
- Capture pass/fail and yes/no branches explicitly.
"""

TILE_PROMPT = """This is a CROPPED region of a larger workflow diagram.
List ONLY the exact text you can read inside boxes/shapes, plus any text
written on arrows. One item per line. Do not describe. Do not invent text."""


# ----------------------------------------------------------------------
# INTERNALS
# ----------------------------------------------------------------------
def _b64(img: Image.Image) -> str:
    """Encode a PIL image as base64 PNG for the Ollama images[] field."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _ask_vision(prompt: str, img: Image.Image) -> str:
    """Single call to the local Ollama vision model with one image."""
    resp = requests.post(
        OLLAMA_URL,
        json={
            "model": VISION_MODEL,
            "prompt": prompt,
            "images": [_b64(img)],
            "stream": False,
            # low temperature = less hallucinated structure;
            # larger context so big diagram descriptions aren't truncated.
            "options": {"temperature": 0.1, "num_ctx": 8192},
        },
        timeout=REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def _tiles(img: Image.Image, grid: int, overlap: float):
    """Yield overlapping crops of the image in a grid x grid layout."""
    w, h = img.size
    tw, th = w / grid, h / grid
    ox, oy = tw * overlap, th * overlap
    for r in range(grid):
        for c in range(grid):
            left = max(0, int(c * tw - ox))
            upper = max(0, int(r * th - oy))
            right = min(w, int((c + 1) * tw + ox))
            lower = min(h, int((r + 1) * th + oy))
            yield img.crop((left, upper, right, lower))


# ----------------------------------------------------------------------
# PUBLIC API
# ----------------------------------------------------------------------
def read_diagram(path: str) -> str:
    """Return a structured text description of a workflow diagram image."""
    img = Image.open(path)
    w, h = img.size

    # Pass 1: overall graph structure from the full image.
    structure = _ask_vision(STRUCTURE_PROMPT, img)

    parts = [
        "WORKFLOW DIAGRAM (extracted by a vision model)",
        f"SOURCE FILE: {path}",
        "",
        structure,
    ]

    # Pass 2: tiled detail pass for large/dense diagrams.
    if max(w, h) >= LARGE_SIDE_PX:
        detail = []
        for i, tile in enumerate(_tiles(img, TILE_GRID, TILE_OVERLAP), 1):
            try:
                txt = _ask_vision(TILE_PROMPT, tile)
                if txt:
                    detail.append(f"[region {i}]\n{txt}")
            except Exception as e:  # one bad tile shouldn't kill the whole doc
                detail.append(f"[region {i}] failed: {e}")
        if detail:
            parts += ["", "DETAIL TEXT (zoomed regions):", *detail]

    return "\n".join(parts)


# Quick standalone test:  python backend/utils/diagram_reader.py <image_path>
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python diagram_reader.py <image_path>")
        raise SystemExit(1)
    print(read_diagram(sys.argv[1]))
