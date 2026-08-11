"""
TRIZ Project Hub — DXF extractor (ezdxf).

Pure-Python drawing text extraction: no AutoCAD license tied up, runs on any
machine, safe to batch overnight. DWG itself needs either the COM extractor
(extract_dwg_com.py, Windows + AutoCAD) or a one-time batch conversion with
the free ODA File Converter (DWG -> DXF), after which this handles everything.

Harvests TEXT/MTEXT/attribute strings for tag matching + FTS, and reads block
attributes for title block data (attribute tags containing DWG/DRAWING/DOC,
REV, TITLE variants).
"""

from __future__ import annotations

import re
from pathlib import Path

import ezdxf

from .patterns import TagMatcher, context_snippet, parse_filename_doc
from .util import winsafe

_DOC_ATTR = re.compile(r"(DWG|DRAWING|DOC).*(NO|NUM)|^DWGNO$|^DOCNO$", re.I)
_REV_ATTR = re.compile(r"^REV(ISION)?(_?NO)?$", re.I)
_TITLE_ATTR = re.compile(r"TITLE", re.I)


def _iter_text(layout):
    for e in layout:
        try:
            t = e.dxftype()
            if t == "TEXT":
                yield e.dxf.text
            elif t == "MTEXT":
                yield e.plain_text()
            elif t == "INSERT":
                for a in e.attribs:
                    yield a.dxf.text
        except Exception:
            continue


def extract_dxf(abs_path: Path, file_id: int, db, matcher: TagMatcher, log=None):
    dxf = ezdxf.readfile(winsafe(abs_path))
    tag_hits = 0
    doc_number = rev = title = None

    layouts = [("modelspace", dxf.modelspace())]
    try:
        layouts += [(name, dxf.layout(name)) for name in dxf.layout_names_in_taborder()
                    if name.lower() != "model"]
    except Exception:
        pass

    for lname, layout in layouts:
        chunks = []
        for txt in _iter_text(layout):
            if not txt:
                continue
            chunks.append(txt)
            for tm in matcher.find(txt.upper()):
                oid = db.get_or_create_object(tm.tag, tm.object_type)
                db.add_occurrence(oid, file_id, None, lname,
                                  context_snippet(txt, tm.start, tm.end))
                tag_hits += 1
        db.add_page_text(file_id, 0, "\n".join(chunks))

        # Title block attributes on block references
        for e in layout:
            if e.dxftype() != "INSERT":
                continue
            try:
                for a in e.attribs:
                    atag, aval = (a.dxf.tag or ""), (a.dxf.text or "").strip()
                    if not aval:
                        continue
                    if _DOC_ATTR.search(atag) and not doc_number:
                        doc_number = aval.upper()
                    elif _REV_ATTR.match(atag) and not rev:
                        rev = aval.upper()
                    elif _TITLE_ATTR.search(atag) and not title:
                        title = aval
            except Exception:
                continue

    source = "dwg_attrib" if doc_number else None
    if not doc_number:
        doc_number, fn_rev = parse_filename_doc(abs_path.stem)
        rev = rev or fn_rev
        source = "filename" if doc_number else None
    if doc_number:
        db.add_document(file_id, doc_number, title, rev, source)

    db.set_file_flags(file_id, parsed=1)
    return {"tags": tag_hits, "doc_number": doc_number, "rev": rev}
