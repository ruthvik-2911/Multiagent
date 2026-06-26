"""
pdf_smart_reader.py  (v2 - shape-anchored)
------------------------------------------
Cascade reader for PDFs. The diagram path reconstructs structure by anchoring to
the VECTOR SHAPES (boxes and diamonds) rather than to loose text blocks, which
fixes the two big sources of noise:

  * adjacent boxes no longer merge into one node - each shape is one node, and
    only the text that falls INSIDE a shape becomes that node's label;
  * floating edge labels (Yes / No / Option 1) are no longer treated as nodes;
    instead they are attached to the nearest connector as the arrow label.

Cascade, per file:
  1. VECTOR DIAGRAM  -> shape-anchored node + edge reconstruction (local, no heat)
  2. TEXT DOCUMENT   -> plain extracted text
  3. SCAN / IMAGE    -> vision render pipeline (pdf_diagram_reader)

HONEST LIMIT: reconstruction is geometric and heuristic. Far cleaner than the
text-block approach, and cleaner still on real tool-exported PDFs, but not
guaranteed exact on very dense pages. For exact structure use the .drawio source.

Dependency: PyMuPDF (fitz), pypdf.
"""

import math
import fitz
from pypdf import PdfReader

TEXT_THRESHOLD = 200
MIN_LINES_FOR_DIAGRAM = 8
ENDPOINT_MAX_DIST = 90
EDGE_LABEL_MAX_WORDS = 3
EDGE_LABEL_MAX_DIST = 60


def _pypdf_text(path):
    try:
        r = PdfReader(path)
        return "\n".join((p.extract_text() or "") for p in r.pages)
    except Exception:
        return ""


def _word_center(w):
    return ((w[0] + w[2]) / 2, (w[1] + w[3]) / 2)


def _node_shapes(page):
    shapes = []
    for d in page.get_drawings():
        xs, ys = [], []
        for it in d["items"]:
            if it[0] == "re":
                r = it[1]; xs += [r.x0, r.x1]; ys += [r.y0, r.y1]
            elif it[0] == "l":
                for p in (it[1], it[2]):
                    xs.append(p.x); ys.append(p.y)
            elif it[0] == "c":
                for p in it[1:]:
                    try:
                        xs.append(p.x); ys.append(p.y)
                    except Exception:
                        pass
        if not xs:
            continue
        bb = fitz.Rect(min(xs), min(ys), max(xs), max(ys))
        w, h = bb.width, bb.height
        if 25 < w < 400 and 12 < h < 140 and (w / max(h, 1)) < 12:
            shapes.append(bb)

    uniq = []
    for s in shapes:
        dup = False
        for u in uniq:
            inter = s & u
            if inter.is_valid and inter.get_area() > 0.5 * min(s.get_area(), u.get_area()):
                dup = True
                break
        if not dup:
            uniq.append(s)
    return uniq


def _segments(page):
    segs = []
    for d in page.get_drawings():
        for it in d["items"]:
            if it[0] == "l":
                segs.append(((it[1].x, it[1].y), (it[2].x, it[2].y)))
    return segs


def _reconstruct_page(page, page_no):
    shapes = _node_shapes(page)
    words = page.get_text("words")

    nodes = []
    inside_idx = set()
    for r in shapes:
        ws = []
        for wi, w in enumerate(words):
            cx, cy = _word_center(w)
            if r.contains(fitz.Point(cx, cy)):
                ws.append(w); inside_idx.add(wi)
        if not ws:
            continue
        ws.sort(key=lambda w: (round(w[1] / 6), w[0]))
        label = " ".join(w[4] for w in ws).strip()
        nodes.append({"label": label, "c": ((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)})

    edge_labels = []
    leftover = [w for wi, w in enumerate(words) if wi not in inside_idx]
    for w in leftover:
        txt = w[4].strip()
        if txt and len(txt.split()) <= EDGE_LABEL_MAX_WORDS:
            edge_labels.append((_word_center(w), txt))

    def nearest_node(pt):
        best, bd = None, 1e9
        for n in nodes:
            d = math.hypot(pt[0] - n["c"][0], pt[1] - n["c"][1])
            if d < bd:
                bd, best = d, n
        return best, bd

    def nearest_edge_label(mid):
        best, bd = None, EDGE_LABEL_MAX_DIST
        for (lc, txt) in edge_labels:
            d = math.hypot(mid[0] - lc[0], mid[1] - lc[1])
            if d < bd:
                bd, best = d, txt
        return best

    edges = set()
    for a, b in _segments(page):
        na, da = nearest_node(a)
        nb, db = nearest_node(b)
        if na and nb and na is not nb and da < ENDPOINT_MAX_DIST and db < ENDPOINT_MAX_DIST:
            mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
            lbl = nearest_edge_label(mid) or ""
            edges.add((na["label"], lbl, nb["label"]))

    out = [f"=== PAGE {page_no} ===", "NODES:"]
    for n in nodes:
        out.append(f'- "{n["label"]}"')
    out.append("")
    out.append("CONNECTIONS (reconstructed from geometry; direction approximate):")
    for a, lbl, b in sorted(edges):
        tag = f"[{lbl}]" if lbl else "[]"
        out.append(f'- "{a}" --{tag}--> "{b}"')
    return "\n".join(out)


def read_pdf_smart(path):
    doc = fitz.open(path)
    total_lines = sum(
        1 for page in doc for d in page.get_drawings()
        for it in d["items"] if it[0] == "l"
    )
    text = _pypdf_text(path)

    if total_lines >= MIN_LINES_FOR_DIAGRAM:
        header = [
            "WORKFLOW DIAGRAM PDF (structure reconstructed from vector geometry)",
            f"SOURCE FILE: {path}",
            "NOTE: connections inferred from line coordinates; approximate on dense "
            "diagrams. For exact structure use the .drawio source if available.",
            "",
        ]
        body = [_reconstruct_page(page, i) for i, page in enumerate(doc, 1)]
        return "\n".join(header) + "\n\n".join(body)

    if len(text.strip()) >= TEXT_THRESHOLD:
        return text

    from backend.utils.pdf_diagram_reader import read_pdf_diagram
    return read_pdf_diagram(path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python pdf_smart_reader.py <file.pdf>")
        raise SystemExit(1)
    print(read_pdf_smart(sys.argv[1]))
