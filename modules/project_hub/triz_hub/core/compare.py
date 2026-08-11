"""
TRIZ Project Hub — PDF revision compare.

Rasterizes both revisions at matched DPI and produces per-page overlay PNGs:
content only in the OLD rev renders red (removed), content only in the NEW rev
renders blue (added), unchanged linework stays dark gray. Returns per-page
change ratios so a "what changed since Rev 3?" query can rank sheets by how
much actually moved.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pymupdf

DPI = 150
INK_THRESHOLD = 200  # grayscale value below this counts as linework


def _page_gray(doc, pno: int) -> np.ndarray:
    page = doc[pno]
    pix = page.get_pixmap(dpi=DPI, colorspace=pymupdf.csGRAY)
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width)
    return arr.copy()


def _pad(a: np.ndarray, h: int, w: int) -> np.ndarray:
    out = np.full((h, w), 255, dtype=np.uint8)
    out[: a.shape[0], : a.shape[1]] = a
    return out


def compare_pdfs(old_path: str, new_path: str, out_dir: str) -> dict:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    d_old = pymupdf.open(old_path)
    d_new = pymupdf.open(new_path)
    pages = max(len(d_old), len(d_new))
    results = []
    try:
        for pno in range(pages):
            g_old = _page_gray(d_old, pno) if pno < len(d_old) else None
            g_new = _page_gray(d_new, pno) if pno < len(d_new) else None
            if g_old is None:
                g_old = np.full_like(g_new, 255)
            if g_new is None:
                g_new = np.full_like(g_old, 255)
            h = max(g_old.shape[0], g_new.shape[0])
            w = max(g_old.shape[1], g_new.shape[1])
            g_old, g_new = _pad(g_old, h, w), _pad(g_new, h, w)

            ink_old = g_old < INK_THRESHOLD
            ink_new = g_new < INK_THRESHOLD
            removed = ink_old & ~ink_new
            added = ink_new & ~ink_old
            same = ink_old & ink_new

            rgb = np.full((h, w, 3), 255, dtype=np.uint8)
            rgb[same] = (70, 74, 82)          # unchanged: dark gray
            rgb[removed] = (214, 69, 69)      # removed: red
            rgb[added] = (58, 116, 235)       # added: blue

            pix = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, w, h), False)
            pix.set_rect(pix.irect, (255, 255, 255))
            # Write raw samples directly for speed
            pix = pymupdf.Pixmap(pymupdf.csRGB, w, h, rgb.tobytes(), False)
            png = out / f"compare_p{pno + 1:03d}.png"
            pix.save(str(png))

            total_ink = int(ink_old.sum() + ink_new.sum())
            changed = int(removed.sum() + added.sum())
            ratio = (changed / total_ink) if total_ink else 0.0
            results.append({"page": pno + 1, "changed_ratio": round(ratio, 4),
                            "png": str(png)})
        return {"pages": results, "out_dir": str(out),
                "old": Path(old_path).name, "new": Path(new_path).name}
    finally:
        d_old.close()
        d_new.close()
