"""
TRIZ Project Hub — project indexer.

Walks the project folder, hashes files, and only re-extracts what changed
(incremental indexing — a nightly or on-open reindex of a big project is
seconds, not minutes). Every file gets a record and a filename tag scan, so
even unparsed formats (DWG without AutoCAD, NWD, RCP, site photos named
"P-101_north.jpg") show up under their object. Parsed formats additionally
get full text + occurrence extraction.

Callbacks (both optional):
    progress(done, total, rel_path)
    log(level, message)          level in {"info","success","warning","error"}
"""

from __future__ import annotations

import hashlib
import re
import time
from pathlib import Path

from .db import Database
from .util import is_cloud_placeholder, winsafe
from .patterns import DEFAULT_PATTERNS, TagMatcher
from . import classify as _classify
from . import extract_pdf, extract_xlsx, extract_dxf, extract_dwg_com
from .issues import run_all_checks

SKIP_DIRS = {".triz", ".git", "__pycache__", "node_modules", "$RECYCLE.BIN"}
SKIP_PREFIXES = ("~$", ".")
# AutoCAD lock/backup/autosave litter and other junk that pollutes an index
SKIP_SUFFIXES = (".bak", ".dwl", ".dwl2", ".ac$", ".sv$", ".tmp", ".err", ".plt")
FULL_HASH_LIMIT = 256 * 1024 * 1024  # above this, fingerprint head+tail instead
COMMIT_EVERY = 25
PARSABLE = {".pdf", ".xlsx", ".xlsm", ".dxf"}
KNOWN_UNPARSED = {".dwg", ".nwd", ".nwc", ".nwf", ".rcp", ".rcs", ".jpg", ".jpeg",
                  ".png", ".docx", ".csv", ".dcf", ".zip", ".msg"}


def _fingerprint(path: Path, size: int, chunk=1 << 20) -> str:
    """Full SHA-1 for normal files. For very large files (point clouds, NWDs,
    recordings) hash 8 MB head + 8 MB tail + size — change detection without
    reading gigabytes on every index."""
    h = hashlib.sha1()
    target = winsafe(path)
    if size > FULL_HASH_LIMIT:
        sample = 8 * 1024 * 1024
        with open(target, "rb") as f:
            h.update(f.read(sample))
            f.seek(max(0, size - sample))
            h.update(f.read(sample))
        h.update(str(size).encode())
        return "big:" + h.hexdigest()
    with open(target, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


class Indexer:
    def __init__(self, project_root: str, db: Database | None = None,
                 progress=None, log=None, use_dwg_com: bool = False):
        self.root = Path(project_root)
        self.db = db or Database(project_root)
        self.progress = progress or (lambda d, t, p: None)
        self.log = log or (lambda lvl, msg: None)
        self.use_dwg_com = use_dwg_com and extract_dwg_com.available()
        self.db.seed_patterns(DEFAULT_PATTERNS)
        self.matcher = TagMatcher(self.db.get_patterns(enabled_only=True))

    # ------------------------------------------------------------------ walk
    def _collect(self) -> list[Path]:
        out = []
        for p in sorted(self.root.rglob("*")):
            if p.is_dir():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.name.startswith(SKIP_PREFIXES):
                continue
            if p.name.lower().endswith(SKIP_SUFFIXES):
                continue
            out.append(p)
        return out

    # ------------------------------------------------------------------- run
    def run(self) -> dict:
        t0 = time.time()
        files = self._collect()
        total = len(files)
        self.db.clear_issues()
        self.log("info", f"Scanning {total} files under {self.root}")
        seen_rel: set[str] = set()
        changed = skipped = failed = 0

        for i, path in enumerate(files, 1):
            rel = str(path.relative_to(self.root))
            seen_rel.add(rel)
            ext = path.suffix.lower()
            try:
                st = path.stat()
                prev = self.db.get_file_by_path(rel)

                # Cloud-only stub (Desktop Connector / OneDrive): reading the
                # content would trigger a hydration download. Index by name
                # only and tell the user.
                if is_cloud_placeholder(path):
                    marker = f"placeholder:{st.st_size}:{st.st_mtime}"
                    if not (prev and prev["sha1"] == marker):
                        fid = self.db.upsert_file(rel, path.name, ext,
                                                  st.st_size, st.st_mtime, marker)
                        self.db.clear_file_data(fid)
                        fname_text = re.sub(r"[_.]+", " ", path.stem.upper())
                        for tm in self.matcher.find(fname_text):
                            oid = self.db.get_or_create_object(tm.tag, tm.object_type)
                            self.db.add_occurrence(oid, fid, None, "filename", path.name)
                        self.db.add_issue("info", "cloud placeholder",
                                          f"{rel} is cloud-only (not hydrated) — "
                                          "indexed by filename only", file_id=fid)
                        changed += 1
                    else:
                        skipped += 1
                    self.progress(i, total, rel)
                    continue

                sha = _fingerprint(path, st.st_size)
                if prev and prev["sha1"] == sha and prev["parsed"] in (0, 1):
                    skipped += 1
                    self.progress(i, total, rel)
                    continue

                fid = self.db.upsert_file(rel, path.name, ext, st.st_size, st.st_mtime, sha)
                self.db.clear_file_data(fid)
                changed += 1

                # Filename tag scan — links photos/models/scans with zero parsing.
                # Separators become spaces so "P-101_north_side" matches P-101.
                fname_text = re.sub(r"[_.]+", " ", path.stem.upper())
                for tm in self.matcher.find(fname_text):
                    oid = self.db.get_or_create_object(tm.tag, tm.object_type)
                    self.db.add_occurrence(oid, fid, None, "filename", path.name)

                info = {}
                if ext == ".pdf":
                    info = extract_pdf.extract_pdf(path, fid, self.db, self.matcher, self.log)
                elif ext in (".xlsx", ".xlsm"):
                    info = extract_xlsx.extract_xlsx(path, fid, self.db, self.matcher, self.log)
                elif ext == ".dxf":
                    info = extract_dxf.extract_dxf(path, fid, self.db, self.matcher, self.log)
                elif ext == ".dwg" and self.use_dwg_com:
                    info = extract_dwg_com.extract_dwg(path, fid, self.db, self.matcher, self.log)

                # Classify (unless the Excel extractor already decided)
                frow = self.db.get_file_by_path(rel)
                if not frow["doc_class"]:
                    dn = info.get("doc_number")
                    self.db.set_file_flags(fid, doc_class=_classify.classify(dn, None, path.name))

                self.db.set_file_flags(fid, status=info.get("status", "ok"))
                if info.get("tags"):
                    self.log("info", f"{rel}: {info['tags']} tag hits"
                             + (f", doc {info.get('doc_number')} rev {info.get('rev')}"
                                if info.get("doc_number") else ""))
                if changed % COMMIT_EVERY == 0:
                    self.db.commit()
            except Exception as e:  # keep indexing; report the file
                failed += 1
                self.log("error", f"{rel}: {type(e).__name__}: {e}")
                # Persist the failure on the file row so the issue survives
                # incremental reindexes (the rule engine derives it from here).
                try:
                    frow = self.db.get_file_by_path(rel)
                    if frow:
                        fid = frow["id"]
                    else:
                        st = path.stat()
                        fid = self.db.upsert_file(rel, path.name, ext,
                                                  st.st_size, st.st_mtime, "")
                    self.db.set_file_flags(
                        fid, parsed=0,
                        status=f"error: {type(e).__name__}: {e}"[:200])
                except Exception:
                    pass
            self.progress(i, total, rel)

        removed = self.db.remove_missing_files(seen_rel)
        pruned = self.db.prune_orphan_objects()
        self.db.commit()

        self.log("info", "Running issue checks…")
        n_issues = run_all_checks(self.db, clear=False)
        self.db.set_meta("last_indexed", str(time.time()))
        self.db.commit()

        dt = time.time() - t0
        stats = self.db.stats()
        stats.update({"changed": changed, "skipped": skipped, "failed": failed,
                      "removed": removed, "pruned": pruned, "seconds": round(dt, 1)})
        self.log("success",
                 f"Index complete in {dt:.1f}s — {changed} updated, {skipped} unchanged, "
                 f"{failed} failed. {stats['objects']} objects, "
                 f"{stats['occurrences']} occurrences, {n_issues} issues.")
        return stats
