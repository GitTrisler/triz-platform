"""
TRIZ Project Hub — database layer.

One SQLite database per project, stored at <project_root>/.triz/hub.db so the
index travels with the project folder. Schema is object-centric: files are
indexed, tags become objects, and every place a tag appears becomes an
occurrence row. FTS5 gives instant full-text search over extracted PDF/DXF
text.
"""

from __future__ import annotations

import os
import re
import sqlite3
import time
from pathlib import Path

DB_DIRNAME = ".triz"
DB_FILENAME = "hub.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,          -- relative to project root
    name TEXT NOT NULL,
    ext TEXT NOT NULL,
    size INTEGER,
    mtime REAL,
    sha1 TEXT,
    parsed INTEGER DEFAULT 0,           -- 1 if a content extractor ran
    scanned_pdf INTEGER DEFAULT 0,      -- 1 if PDF had no extractable text
    doc_class TEXT,                     -- pid / isometric / datasheet / vendor / register / model_export / general
    status TEXT,                        -- ok / encrypted / error: <detail>  (persists across reindexes)
    indexed_at REAL
);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    doc_number TEXT,
    title TEXT,
    revision TEXT,
    source TEXT                         -- titleblock / filename / excel_register / dwg_attrib
);

CREATE TABLE IF NOT EXISTS objects (
    id INTEGER PRIMARY KEY,
    tag TEXT UNIQUE NOT NULL,
    type TEXT NOT NULL,
    in_model INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS occurrences (
    id INTEGER PRIMARY KEY,
    object_id INTEGER NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
    file_id INTEGER NOT NULL REFERENCES files(id) ON DELETE CASCADE,
    page INTEGER,                       -- PDF page (1-based); NULL for filename/excel hits
    location TEXT,                      -- 'page 3' / 'Sheet1!B4' / 'filename' / 'modelspace'
    context TEXT
);

CREATE TABLE IF NOT EXISTS issues (
    id INTEGER PRIMARY KEY,
    severity TEXT NOT NULL,             -- error / warning / info
    category TEXT NOT NULL,
    message TEXT NOT NULL,
    file_id INTEGER REFERENCES files(id) ON DELETE CASCADE,
    object_id INTEGER REFERENCES objects(id) ON DELETE CASCADE,
    created_at REAL
);

CREATE TABLE IF NOT EXISTS tag_patterns (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    regex TEXT NOT NULL,
    priority INTEGER DEFAULT 50,
    enabled INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_occ_object ON occurrences(object_id);
CREATE INDEX IF NOT EXISTS idx_occ_file ON occurrences(file_id);
CREATE INDEX IF NOT EXISTS idx_doc_number ON documents(doc_number);
CREATE INDEX IF NOT EXISTS idx_obj_tag ON objects(tag);
"""

FTS_SCHEMA = """
CREATE VIRTUAL TABLE IF NOT EXISTS page_text USING fts5(
    content,
    file_id UNINDEXED,
    page UNINDEXED
);
"""


def rev_sort_key(rev: str | None):
    """Order revisions per common IFC practice: letter revs (A, B, C — preliminary)
    sort before numeric revs (0, 1, 2 — issued). Within each group, natural order.
    Returns a tuple usable as a sort key; higher = newer."""
    if rev is None or str(rev).strip() == "":
        return (-1, 0, "")
    r = str(rev).strip().upper()
    if r.isdigit():
        return (1, int(r), "")
    m = re.match(r"^([A-Z]+)(\d*)$", r)
    if m:
        return (0, int(m.group(2) or 0), m.group(1))
    return (0, 0, r)


class Database:
    """Thin wrapper around sqlite3 with all Project Hub queries in one place."""

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.db_dir = self.root / DB_DIRNAME
        self.db_dir.mkdir(exist_ok=True)
        self.path = self.db_dir / DB_FILENAME
        self.con = sqlite3.connect(str(self.path))
        self.con.row_factory = sqlite3.Row
        self.con.execute("PRAGMA foreign_keys = ON")
        self.con.execute("PRAGMA journal_mode = WAL")
        self.con.execute("PRAGMA synchronous = NORMAL")
        self.con.executescript(SCHEMA)
        self.con.executescript(FTS_SCHEMA)
        self._migrate()
        self.con.commit()

    def _migrate(self):
        """Add columns introduced after a database was first created, so
        opening an old .triz index with a newer build never crashes."""
        cols = {r["name"] for r in self.con.execute("PRAGMA table_info(files)")}
        if "status" not in cols:
            self.con.execute("ALTER TABLE files ADD COLUMN status TEXT")

    def close(self):
        self.con.close()

    # ------------------------------------------------------------------ meta
    def set_meta(self, key: str, value: str):
        self.con.execute(
            "INSERT INTO meta(key, value) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )
        self.con.commit()

    def get_meta(self, key: str, default=None):
        row = self.con.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    # ----------------------------------------------------------------- files
    def get_file_by_path(self, rel_path: str):
        return self.con.execute("SELECT * FROM files WHERE path = ?", (rel_path,)).fetchone()

    def upsert_file(self, rel_path: str, name: str, ext: str, size: int,
                    mtime: float, sha1: str) -> int:
        row = self.get_file_by_path(rel_path)
        if row:
            self.con.execute(
                "UPDATE files SET name=?, ext=?, size=?, mtime=?, sha1=?, indexed_at=? WHERE id=?",
                (name, ext, size, mtime, sha1, time.time(), row["id"]),
            )
            return row["id"]
        cur = self.con.execute(
            "INSERT INTO files(path, name, ext, size, mtime, sha1, indexed_at) "
            "VALUES(?,?,?,?,?,?,?)",
            (rel_path, name, ext, size, mtime, sha1, time.time()),
        )
        return cur.lastrowid

    def set_file_flags(self, file_id: int, parsed: int | None = None,
                       scanned_pdf: int | None = None, doc_class: str | None = None,
                       status: str | None = None):
        if parsed is not None:
            self.con.execute("UPDATE files SET parsed=? WHERE id=?", (parsed, file_id))
        if scanned_pdf is not None:
            self.con.execute("UPDATE files SET scanned_pdf=? WHERE id=?", (scanned_pdf, file_id))
        if doc_class is not None:
            self.con.execute("UPDATE files SET doc_class=? WHERE id=?", (doc_class, file_id))
        if status is not None:
            self.con.execute("UPDATE files SET status=? WHERE id=?", (status, file_id))

    def clear_file_data(self, file_id: int):
        """Remove derived data before re-extracting a changed file."""
        self.con.execute("DELETE FROM occurrences WHERE file_id=?", (file_id,))
        self.con.execute("DELETE FROM documents WHERE file_id=?", (file_id,))
        self.con.execute("DELETE FROM page_text WHERE file_id=?", (file_id,))

    def remove_missing_files(self, existing_rel_paths: set[str]) -> int:
        rows = self.con.execute("SELECT id, path FROM files").fetchall()
        gone = [r["id"] for r in rows if r["path"] not in existing_rel_paths]
        for fid in gone:
            self.con.execute("DELETE FROM page_text WHERE file_id=?", (fid,))
            self.con.execute("DELETE FROM files WHERE id=?", (fid,))
        return len(gone)

    # ------------------------------------------------------------- documents
    def add_document(self, file_id: int, doc_number: str | None, title: str | None,
                     revision: str | None, source: str):
        self.con.execute(
            "INSERT INTO documents(file_id, doc_number, title, revision, source) VALUES(?,?,?,?,?)",
            (file_id, doc_number, title, revision, source),
        )

    # --------------------------------------------------------------- objects
    def get_or_create_object(self, tag: str, obj_type: str) -> int:
        row = self.con.execute("SELECT id FROM objects WHERE tag=?", (tag,)).fetchone()
        if row:
            return row["id"]
        cur = self.con.execute(
            "INSERT INTO objects(tag, type) VALUES(?,?)", (tag, obj_type)
        )
        return cur.lastrowid

    def mark_in_model(self, tag: str, obj_type: str = "equipment"):
        oid = self.get_or_create_object(tag, obj_type)
        self.con.execute("UPDATE objects SET in_model=1 WHERE id=?", (oid,))
        return oid

    def add_occurrence(self, object_id: int, file_id: int, page: int | None,
                       location: str, context: str):
        self.con.execute(
            "INSERT INTO occurrences(object_id, file_id, page, location, context) "
            "VALUES(?,?,?,?,?)",
            (object_id, file_id, page, location, context[:300] if context else ""),
        )

    def prune_orphan_objects(self) -> int:
        cur = self.con.execute(
            "DELETE FROM objects WHERE in_model=0 AND id NOT IN "
            "(SELECT DISTINCT object_id FROM occurrences)"
        )
        return cur.rowcount

    # -------------------------------------------------------------- fulltext
    def add_page_text(self, file_id: int, page: int, text: str):
        if text and text.strip():
            self.con.execute(
                "INSERT INTO page_text(content, file_id, page) VALUES(?,?,?)",
                (text, file_id, page),
            )

    # ---------------------------------------------------------------- issues
    def clear_issues(self):
        self.con.execute("DELETE FROM issues")

    def add_issue(self, severity: str, category: str, message: str,
                  file_id: int | None = None, object_id: int | None = None):
        self.con.execute(
            "INSERT INTO issues(severity, category, message, file_id, object_id, created_at) "
            "VALUES(?,?,?,?,?,?)",
            (severity, category, message, file_id, object_id, time.time()),
        )

    # -------------------------------------------------------------- patterns
    def seed_patterns(self, defaults):
        count = self.con.execute("SELECT COUNT(*) c FROM tag_patterns").fetchone()["c"]
        if count == 0:
            for name, obj_type, regex, priority, enabled in defaults:
                self.con.execute(
                    "INSERT INTO tag_patterns(name, object_type, regex, priority, enabled) "
                    "VALUES(?,?,?,?,?)",
                    (name, obj_type, regex, priority, enabled),
                )
            self.con.commit()

    def get_patterns(self, enabled_only=True):
        q = "SELECT * FROM tag_patterns"
        if enabled_only:
            q += " WHERE enabled=1"
        q += " ORDER BY priority DESC"
        return self.con.execute(q).fetchall()

    def save_patterns(self, rows):
        """rows: list of dicts with name/object_type/regex/priority/enabled."""
        self.con.execute("DELETE FROM tag_patterns")
        for r in rows:
            self.con.execute(
                "INSERT INTO tag_patterns(name, object_type, regex, priority, enabled) "
                "VALUES(?,?,?,?,?)",
                (r["name"], r["object_type"], r["regex"], int(r["priority"]), int(r["enabled"])),
            )
        self.con.commit()

    # ---------------------------------------------------------------- search
    def search_objects(self, q: str, limit=50):
        like = f"%{q.upper()}%"
        return self.con.execute(
            "SELECT o.*, COUNT(oc.id) AS hits FROM objects o "
            "LEFT JOIN occurrences oc ON oc.object_id = o.id "
            "WHERE o.tag LIKE ? GROUP BY o.id "
            "ORDER BY (o.tag = ?) DESC, hits DESC LIMIT ?",
            (like, q.upper(), limit),
        ).fetchall()

    def search_documents(self, q: str, limit=50):
        like = f"%{q}%"
        return self.con.execute(
            "SELECT d.*, f.path, f.name FROM documents d JOIN files f ON f.id = d.file_id "
            "WHERE d.doc_number LIKE ? OR d.title LIKE ? "
            "ORDER BY d.doc_number LIMIT ?",
            (like, like, limit),
        ).fetchall()

    def fts_search(self, q: str, limit=40):
        # FTS5 treats -, " etc. as syntax; quote each token for literal matching.
        tokens = [t for t in re.split(r"\s+", q.strip()) if t]
        if not tokens:
            return []
        match = " ".join('"' + t.replace('"', '""') + '"' for t in tokens)
        try:
            return self.con.execute(
                "SELECT pt.file_id, pt.page, "
                "snippet(page_text, 0, '[', ']', ' … ', 10) AS snip, f.path, f.name "
                "FROM page_text pt JOIN files f ON f.id = pt.file_id "
                "WHERE page_text MATCH ? ORDER BY rank LIMIT ?",
                (match, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []

    # ----------------------------------------------------------- object view
    def object_by_tag(self, tag: str):
        return self.con.execute("SELECT * FROM objects WHERE tag=?", (tag,)).fetchone()

    def object_occurrences(self, object_id: int):
        return self.con.execute(
            "SELECT oc.*, f.path, f.name, f.ext, f.doc_class FROM occurrences oc "
            "JOIN files f ON f.id = oc.file_id WHERE oc.object_id=? "
            "ORDER BY f.doc_class, f.name, oc.page",
            (object_id,),
        ).fetchall()

    def related_objects(self, object_id: int, limit=12):
        """Objects that co-occur on the same file+page — the cheap relationship
        engine. Two tags that keep showing up on the same P&ID sheet are
        related, no semantic parsing required."""
        return self.con.execute(
            "SELECT o2.tag, o2.type, COUNT(*) AS strength "
            "FROM occurrences a "
            "JOIN occurrences b ON b.file_id = a.file_id "
            "  AND IFNULL(b.page,-1) = IFNULL(a.page,-1) AND b.object_id != a.object_id "
            "JOIN objects o2 ON o2.id = b.object_id "
            "WHERE a.object_id = ? "
            "GROUP BY o2.id ORDER BY strength DESC LIMIT ?",
            (object_id, limit),
        ).fetchall()

    # --------------------------------------------------------------- listing
    def documents_list(self, filter_text: str = ""):
        like = f"%{filter_text}%"
        return self.con.execute(
            "SELECT d.*, f.path, f.name, f.doc_class FROM documents d "
            "JOIN files f ON f.id = d.file_id "
            "WHERE d.doc_number LIKE ? OR d.title LIKE ? OR f.name LIKE ? "
            "ORDER BY d.doc_number, d.revision",
            (like, like, like),
        ).fetchall()

    def latest_documents(self):
        """Newest revision per doc number (see rev_sort_key for ordering rules)."""
        rows = self.con.execute(
            "SELECT d.*, f.path, f.name, f.doc_class FROM documents d "
            "JOIN files f ON f.id = d.file_id WHERE d.doc_number IS NOT NULL"
        ).fetchall()
        best = {}
        for r in rows:
            key = r["doc_number"]
            if key not in best or rev_sort_key(r["revision"]) > rev_sort_key(best[key]["revision"]):
                best[key] = r
        return sorted(best.values(), key=lambda r: r["doc_number"])

    def class_breakdown(self):
        """Latest documents grouped by class — feeds the dashboard composition bar."""
        from collections import Counter
        c = Counter((d["doc_class"] or "general") for d in self.latest_documents())
        return c.most_common()

    def type_breakdown(self):
        return [(r["type"], r["c"]) for r in self.con.execute(
            "SELECT type, COUNT(*) c FROM objects GROUP BY type ORDER BY c DESC")]

    def issues_list(self, severity: str | None = None):
        q = ("SELECT i.*, f.path, f.name, o.tag FROM issues i "
             "LEFT JOIN files f ON f.id = i.file_id "
             "LEFT JOIN objects o ON o.id = i.object_id ")
        args = ()
        if severity:
            q += "WHERE i.severity = ? "
            args = (severity,)
        q += "ORDER BY CASE i.severity WHEN 'error' THEN 0 WHEN 'warning' THEN 1 ELSE 2 END, i.category"
        return self.con.execute(q, args).fetchall()

    def objects_list(self, filter_text: str = "", obj_type: str | None = None):
        like = f"%{filter_text.upper()}%"
        q = ("SELECT o.*, COUNT(oc.id) AS hits FROM objects o "
             "LEFT JOIN occurrences oc ON oc.object_id = o.id WHERE o.tag LIKE ? ")
        args = [like]
        if obj_type:
            q += "AND o.type = ? "
            args.append(obj_type)
        q += "GROUP BY o.id ORDER BY o.type, o.tag"
        return self.con.execute(q, args).fetchall()

    def stats(self):
        g = lambda q: self.con.execute(q).fetchone()[0]
        return {
            "files": g("SELECT COUNT(*) FROM files"),
            "documents": g("SELECT COUNT(DISTINCT doc_number) FROM documents WHERE doc_number IS NOT NULL"),
            "objects": g("SELECT COUNT(*) FROM objects"),
            "occurrences": g("SELECT COUNT(*) FROM occurrences"),
            "issues": g("SELECT COUNT(*) FROM issues"),
            "errors": g("SELECT COUNT(*) FROM issues WHERE severity='error'"),
        }

    def commit(self):
        self.con.commit()
