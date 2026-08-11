"""
TRIZ Project Hub — native DWG extractor via AutoCAD COM (pywin32).

Windows + AutoCAD only. Untested outside that environment — written against
the standard ActiveX object model you already know from LISP/VLA work
(ThisDrawing.ModelSpace, GetAttributes, TextString). Slower than the DXF path
and ties up an AutoCAD session, so treat it as the fallback when converting
to DXF isn't an option. The indexer only calls this if `available()` is True.
"""

from __future__ import annotations

import sys
from pathlib import Path

from .patterns import TagMatcher, context_snippet, parse_filename_doc


def available() -> bool:
    if sys.platform != "win32":
        return False
    try:
        import win32com.client  # noqa: F401
        return True
    except ImportError:
        return False


def _acad():
    import win32com.client
    try:
        return win32com.client.GetActiveObject("AutoCAD.Application")
    except Exception:
        app = win32com.client.Dispatch("AutoCAD.Application")
        app.Visible = False
        return app


def extract_dwg(abs_path: Path, file_id: int, db, matcher: TagMatcher, log=None):
    acad = _acad()
    doc = acad.Documents.Open(str(abs_path), True)  # read-only
    tag_hits = 0
    doc_number = rev = title = None
    try:
        spaces = [("modelspace", doc.ModelSpace), ("paperspace", doc.PaperSpace)]
        for sname, space in spaces:
            chunks = []
            for ent in space:
                oname = ent.ObjectName
                texts = []
                if oname in ("AcDbText", "AcDbMText"):
                    texts.append(ent.TextString)
                elif oname == "AcDbBlockReference":
                    try:
                        for att in ent.GetAttributes():
                            texts.append(att.TextString)
                            at = (att.TagString or "").upper()
                            av = (att.TextString or "").strip()
                            if av:
                                if ("DWG" in at or "DOC" in at) and ("NO" in at or "NUM" in at) and not doc_number:
                                    doc_number = av.upper()
                                elif at.startswith("REV") and not rev:
                                    rev = av.upper()
                                elif "TITLE" in at and not title:
                                    title = av
                    except Exception:
                        pass
                for txt in texts:
                    if not txt:
                        continue
                    chunks.append(txt)
                    for tm in matcher.find(txt.upper()):
                        oid = db.get_or_create_object(tm.tag, tm.object_type)
                        db.add_occurrence(oid, file_id, None, sname,
                                          context_snippet(txt, tm.start, tm.end))
                        tag_hits += 1
            db.add_page_text(file_id, 0, "\n".join(chunks))
    finally:
        doc.Close(False)

    source = "dwg_attrib" if doc_number else None
    if not doc_number:
        doc_number, fn_rev = parse_filename_doc(abs_path.stem)
        rev = rev or fn_rev
        source = "filename" if doc_number else None
    if doc_number:
        db.add_document(file_id, doc_number, title, rev, source)
    db.set_file_flags(file_id, parsed=1)
    return {"tags": tag_hits, "doc_number": doc_number, "rev": rev}
