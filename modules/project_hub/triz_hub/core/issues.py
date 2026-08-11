"""
TRIZ Project Hub — issue engine.

Rules run after every index and rebuild the issues table from scratch, so
issues are always a live picture of the project, never a stale backlog. Add a
rule by writing a function that takes the Database and calls db.add_issue —
each one is a few lines of SQL over the indexed data.
"""

from __future__ import annotations

from collections import defaultdict

from .db import Database, rev_sort_key


def check_missing_revision(db: Database):
    rows = db.con.execute(
        "SELECT d.id, d.doc_number, f.id AS fid, f.name FROM documents d "
        "JOIN files f ON f.id = d.file_id "
        "WHERE d.doc_number IS NOT NULL AND (d.revision IS NULL OR d.revision = '') "
        "AND d.source != 'excel_register'"
    ).fetchall()
    for r in rows:
        db.add_issue("warning", "missing revision",
                     f"{r['doc_number']} ({r['name']}) has no revision detected",
                     file_id=r["fid"])


def check_duplicates_and_superseded(db: Database):
    rows = db.con.execute(
        "SELECT d.doc_number, d.revision, f.id AS fid, f.name FROM documents d "
        "JOIN files f ON f.id = d.file_id "
        "WHERE d.doc_number IS NOT NULL AND d.source != 'excel_register'"
    ).fetchall()
    by_doc = defaultdict(list)
    for r in rows:
        by_doc[r["doc_number"]].append(r)
    for doc, items in by_doc.items():
        if len(items) < 2:
            continue
        by_rev = defaultdict(list)
        for r in items:
            by_rev[(r["revision"] or "").upper()].append(r)
        for rev, dupes in by_rev.items():
            if len(dupes) > 1:
                names = ", ".join(d["name"] for d in dupes)
                db.add_issue("error", "duplicate document",
                             f"{doc} rev {rev or '?'} exists in multiple files: {names}",
                             file_id=dupes[0]["fid"])
        newest = max(items, key=lambda r: rev_sort_key(r["revision"]))
        for r in items:
            if r["fid"] != newest["fid"] and rev_sort_key(r["revision"]) < rev_sort_key(newest["revision"]):
                db.add_issue("info", "superseded revision",
                             f"{doc} rev {r['revision'] or '?'} ({r['name']}) is superseded "
                             f"by rev {newest['revision']} ({newest['name']})",
                             file_id=r["fid"])


def check_index_errors(db: Database):
    """Files that failed to read/parse. Status persists in the files table, so
    these issues survive incremental reindexes that skip the unchanged file."""
    rows = db.con.execute(
        "SELECT id, path, status FROM files WHERE status LIKE 'error%'"
    ).fetchall()
    for r in rows:
        db.add_issue("error", "index failure",
                     f"{r['path']}: {r['status'][6:].strip() or 'unreadable'}",
                     file_id=r["id"])


def check_encrypted(db: Database):
    rows = db.con.execute(
        "SELECT id, name FROM files WHERE status = 'encrypted'"
    ).fetchall()
    for r in rows:
        db.add_issue("warning", "password protected",
                     f"{r['name']} is encrypted — content cannot be indexed",
                     file_id=r["id"])


def check_scanned_pdfs(db: Database):
    rows = db.con.execute(
        "SELECT id, name FROM files WHERE scanned_pdf = 1"
    ).fetchall()
    for r in rows:
        db.add_issue("warning", "no text layer",
                     f"{r['name']} has no extractable text (scanned) — OCR candidate",
                     file_id=r["id"])


def check_pid_tags_not_in_model(db: Database):
    """Only meaningful when the project actually contains a model export."""
    has_model = db.con.execute(
        "SELECT COUNT(*) c FROM files WHERE doc_class = 'model_export'"
    ).fetchone()["c"]
    if not has_model:
        return
    rows = db.con.execute(
        "SELECT DISTINCT o.id, o.tag, o.type FROM objects o "
        "JOIN occurrences oc ON oc.object_id = o.id "
        "JOIN files f ON f.id = oc.file_id "
        "WHERE f.doc_class = 'pid' AND o.in_model = 0 "
        "AND o.type IN ('equipment','valve','line','instrument')"
    ).fetchall()
    for r in rows:
        db.add_issue("warning", "not in model",
                     f"{r['tag']} ({r['type']}) appears on P&IDs but not in the model export",
                     object_id=r["id"])


def check_model_tags_not_on_pids(db: Database):
    has_pid = db.con.execute(
        "SELECT COUNT(*) c FROM files WHERE doc_class = 'pid'"
    ).fetchone()["c"]
    if not has_pid:
        return
    rows = db.con.execute(
        "SELECT o.id, o.tag, o.type FROM objects o WHERE o.in_model = 1 AND o.id NOT IN ("
        "  SELECT oc.object_id FROM occurrences oc JOIN files f ON f.id = oc.file_id "
        "  WHERE f.doc_class = 'pid')"
    ).fetchall()
    for r in rows:
        db.add_issue("info", "model only",
                     f"{r['tag']} ({r['type']}) is in the model export but not found on any P&ID",
                     object_id=r["id"])


def check_register_vs_files(db: Database):
    """Docs listed in an Excel register but with no matching file in the project."""
    reg = db.con.execute(
        "SELECT DISTINCT doc_number FROM documents "
        "WHERE source = 'excel_register' AND doc_number IS NOT NULL"
    ).fetchall()
    if not reg:
        return
    have = {r["doc_number"] for r in db.con.execute(
        "SELECT DISTINCT doc_number FROM documents "
        "WHERE source != 'excel_register' AND doc_number IS NOT NULL").fetchall()}
    for r in reg:
        if r["doc_number"] not in have:
            db.add_issue("warning", "register mismatch",
                         f"{r['doc_number']} is listed in the register but no file with "
                         f"that document number was found")


ALL_CHECKS = [
    check_index_errors,
    check_encrypted,
    check_missing_revision,
    check_duplicates_and_superseded,
    check_scanned_pdfs,
    check_pid_tags_not_in_model,
    check_model_tags_not_on_pids,
    check_register_vs_files,
]


def run_all_checks(db: Database, clear: bool = True) -> int:
    """clear=False lets the indexer keep per-file failure issues it
    recorded during the walk (it clears once at the start of the run)."""
    if clear:
        db.clear_issues()
    for check in ALL_CHECKS:
        try:
            check(db)
        except Exception as e:
            db.add_issue("error", "check failed", f"{check.__name__}: {e}")
    db.commit()
    return db.con.execute("SELECT COUNT(*) c FROM issues").fetchone()["c"]
