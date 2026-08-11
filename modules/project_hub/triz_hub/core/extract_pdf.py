"""
TRIZ Project Hub — PDF extractor (PyMuPDF).

Per page: full text goes to FTS, tags become occurrences with page + context.
Title block extraction is heuristic and layered:

  1. lower-right region of page 1 — inline labeled fields (DWG NO: X)
  2. same region — label-ABOVE-value layout (label on one line, value below),
     the other common real-world title block style
  3. full-width bottom strip — for title blocks that run across the sheet
  4. filename parsing (PID-001_Rev2.pdf) as last resort

Encrypted PDFs are flagged as issues instead of crashing; scanned PDFs (no
text layer) are flagged as OCR candidates. inspect_titleblock() exposes the
raw region text + parse result so tuning on a new client border is a
five-minute job, not guesswork (Tools → Title Block Inspector).
"""

from __future__ import annotations

import re
from pathlib import Path

import pymupdf

from .patterns import TagMatcher, context_snippet, parse_filename_doc
from .util import winsafe

# Inline labeled fields: "DWG NO: PID-001"
_DOC_RE = re.compile(r'(?:DWG|DRAWING|DOC|DOCUMENT)\s*(?:NO|NUMBER|#)?\s*[:.\s]\s*'
                     r'([A-Z0-9][A-Z0-9\-._/]{2,30})', re.I)
_REV_RE = re.compile(r'\bREV(?:ISION)?\s*[:.\s]\s*([A-Z0-9]{1,3})\b', re.I)
_TITLE_RE = re.compile(r'\bTITLE\s*[:.\s]\s*(.{3,80})', re.I)

# Label-above-value: a line that IS the label, value on the next line
_DOC_LABEL_LINE = re.compile(r'^(?:DWG|DRAWING|DOC|DOCUMENT)\.?\s*'
                             r'(?:NO|NUMBER|#)?\.?\s*:?\s*$', re.I)
_REV_LABEL_LINE = re.compile(r'^REV(?:ISION)?\.?\s*(?:NO)?\.?\s*:?\s*$', re.I)
_TITLE_LABEL_LINE = re.compile(r'^(?:TITLE|DRAWING TITLE)\.?\s*:?\s*$', re.I)
_DOC_VALUE = re.compile(r'^[A-Z0-9][A-Z0-9\-._/]{2,30}$')
_REV_VALUE = re.compile(r'^[A-Z0-9]{1,3}$')


def _parse_tb_text(text: str):
    """Parse (doc_number, revision, title) out of a title block text region.
    Tries inline labels first, then label-above-value lines."""
    doc = rev = title = None
    m = _DOC_RE.search(text)
    if m:
        doc = m.group(1).strip().upper().rstrip(".")
    m = _REV_RE.search(text)
    if m:
        rev = m.group(1).strip().upper()
    m = _TITLE_RE.search(text)
    if m:
        title = m.group(1).strip().splitlines()[0].strip()

    if doc and rev:
        return doc, rev, title

    lines = [ln.strip() for ln in text.splitlines()]
    for i, ln in enumerate(lines[:-1]):
        nxt = next((l for l in lines[i + 1:i + 3] if l), "")
        if doc is None and _DOC_LABEL_LINE.match(ln) and _DOC_VALUE.match(nxt.upper()):
            doc = nxt.upper()
        elif rev is None and _REV_LABEL_LINE.match(ln) and _REV_VALUE.match(nxt.upper()):
            rev = nxt.upper()
        elif title is None and _TITLE_LABEL_LINE.match(ln) and len(nxt) >= 3:
            title = nxt
    return doc, rev, title


def _regions(page):
    """Candidate title block regions, most-likely first."""
    r = page.rect
    return [
        ("lower right", pymupdf.Rect(r.x0 + r.width * 0.55,
                                     r.y0 + r.height * 0.70, r.x1, r.y1)),
        ("bottom strip", pymupdf.Rect(r.x0, r.y0 + r.height * 0.82, r.x1, r.y1)),
    ]


def inspect_titleblock(pdf_path: str) -> dict:
    """Diagnostic used by the Title Block Inspector tool: returns the raw text
    of every candidate region plus the final parse, so a failing client
    border can be diagnosed by eye."""
    out = {"regions": [], "doc_number": None, "revision": None, "title": None,
           "source": None, "encrypted": False}
    doc = pymupdf.open(winsafe(pdf_path))
    try:
        if doc.needs_pass:
            out["encrypted"] = True
            return out
        if len(doc) == 0:
            return out
        page = doc[0]
        for name, clip in _regions(page):
            text = page.get_text(clip=clip)
            out["regions"].append({"name": name, "text": text})
            if out["doc_number"] is None:
                d, r, t = _parse_tb_text(text)
                if d:
                    out.update({"doc_number": d, "revision": r, "title": t,
                                "source": f"titleblock ({name})"})
        if out["doc_number"] is None:
            fn_doc, fn_rev = parse_filename_doc(Path(pdf_path).stem)
            if fn_doc:
                out.update({"doc_number": fn_doc, "revision": fn_rev,
                            "source": "filename"})
        return out
    finally:
        doc.close()


def extract_pdf(abs_path: Path, file_id: int, db, matcher: TagMatcher, log=None):
    doc = pymupdf.open(winsafe(abs_path))
    text_chars = 0
    tag_hits = 0
    try:
        if doc.needs_pass:
            db.set_file_flags(file_id, parsed=0)
            return {"pages": len(doc), "tags": 0, "scanned": 0,
                    "doc_number": None, "rev": None, "status": "encrypted"}

        if len(doc) == 0:
            db.set_file_flags(file_id, parsed=0)
            return {"pages": 0, "tags": 0, "scanned": 0, "doc_number": None,
                    "rev": None, "status": "error: PDF contains 0 pages"}

        for pno in range(len(doc)):
            page = doc[pno]
            text = page.get_text()
            text_chars += len(text.strip())
            db.add_page_text(file_id, pno + 1, text)
            for tm in matcher.find(text):
                oid = db.get_or_create_object(tm.tag, tm.object_type)
                db.add_occurrence(oid, file_id, pno + 1, f"page {pno + 1}",
                                  context_snippet(text, tm.start, tm.end))
                tag_hits += 1

        scanned = 1 if text_chars < 20 and len(doc) > 0 else 0
        db.set_file_flags(file_id, parsed=1, scanned_pdf=scanned)

        doc_number = rev = title = None
        source = None
        if not scanned and len(doc) > 0:
            page = doc[0]
            for name, clip in _regions(page):
                d, r, t = _parse_tb_text(page.get_text(clip=clip))
                if d:
                    doc_number, source = d, "titleblock"
                    rev = rev or r
                    title = title or t
                    break
                rev = rev or r
                title = title or t

        if not doc_number:
            fn_doc, fn_rev = parse_filename_doc(abs_path.stem)
            if fn_doc:
                doc_number, source = fn_doc, "filename"
                rev = rev or fn_rev
        elif rev is None:
            _, fn_rev = parse_filename_doc(abs_path.stem)
            rev = fn_rev

        if doc_number:
            db.add_document(file_id, doc_number, title, rev, source)

        return {"pages": len(doc), "tags": tag_hits, "scanned": scanned,
                "doc_number": doc_number, "rev": rev}
    finally:
        doc.close()
