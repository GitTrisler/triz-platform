"""
PDF merging — phase 2 of the publishing pipeline.

Publishing is expensive (one AutoCAD session per run) and produces one PDF per
sheet. Merging is cheap and happens afterwards on any selection, in any order,
without touching AutoCAD. Keeping the two phases separate means a wrong merge
order costs a re-merge instead of a republish.

No Qt imports here — the engine is callable from a background Job.
"""

import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import List

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    fitz = None
    PYMUPDF_AVAILABLE = False


ARCHIVE_DIR_NAME = "_individual_pdfs"


def natural_key(path: Path):
    """Sort P-2 before P-10 — digit runs compare numerically, not lexically."""
    return [int(token) if token.isdigit() else token.lower()
            for token in re.split(r"(\d+)", path.name)]


def normalize_pdf_name(filename: str) -> str:
    """Ensure the merged output ends in .pdf."""
    name = (filename or "").strip()
    if not name:
        return "Merged.pdf"
    if not name.lower().endswith(".pdf"):
        name = f"{name}.pdf"
    return name


def collect_pdfs(folder: Path, recurse: bool = False) -> List[Path]:
    """List PDFs in a folder, in natural sheet order.

    The archive subfolder is skipped when recursing so a merge does not pick up
    its own leftovers — but if the user browses directly into the archive, those
    PDFs are exactly what they asked for, so nothing is filtered.
    """
    folder = Path(folder)
    if not folder.is_dir():
        return []

    pattern = "**/*.pdf" if recurse else "*.pdf"
    inside_archive = folder.name == ARCHIVE_DIR_NAME

    found = [
        p for p in folder.glob(pattern)
        if p.is_file()
        and (inside_archive or ARCHIVE_DIR_NAME not in p.relative_to(folder).parts)
    ]
    return sorted(found, key=natural_key)


def merge_pdfs(pdf_paths: List[Path], output_path: Path, write) -> Path:
    """Merge PDFs in the supplied order and return the combined path.

    Writes to a temp file and verifies the page count before replacing anything,
    because a silently truncated merge is the failure that reaches the client.
    """
    if not PYMUPDF_AVAILABLE:
        raise RuntimeError(
            "PyMuPDF is not installed. Install it with: pip install PyMuPDF")

    source_paths = [Path(p) for p in pdf_paths]
    if not source_paths:
        raise RuntimeError("No PDFs selected to merge")

    missing = [p for p in source_paths if not p.exists()]
    if missing:
        raise RuntimeError(f"PDF not found: {missing[0]}")

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_resolved = output_path.resolve()
    if any(p.resolve() == output_resolved for p in source_paths):
        raise RuntimeError(
            "The merged filename matches one of the source PDFs")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    temp_path = output_path.with_name(f".{output_path.stem}_{stamp}.tmp.pdf")
    merged = None

    write(f"Merging {len(source_paths)} PDF(s)...", "JOB")
    try:
        merged = fitz.open()
        for index, pdf_path in enumerate(source_paths, start=1):
            write(f"  [{index}/{len(source_paths)}] {pdf_path.name}", "INFO")
            with fitz.open(str(pdf_path)) as source:
                merged.insert_pdf(source)

        expected_pages = merged.page_count
        merged.save(str(temp_path), garbage=4, deflate=True)
        merged.close()
        merged = None

        with fitz.open(str(temp_path)) as check:
            actual_pages = check.page_count
        if actual_pages != expected_pages:
            raise RuntimeError(
                f"Page count mismatch: expected {expected_pages}, "
                f"got {actual_pages}. Nothing was overwritten.")

        temp_path.replace(output_path)
        size_kb = output_path.stat().st_size / 1024
        write(f"[OK] Merged PDF created: {output_path.name} "
              f"({actual_pages} pages, {size_kb:.1f} KB)", "SUCCESS")
        return output_path

    except Exception as e:
        raise RuntimeError(
            f"Could not create merged PDF. Close it if it is open in a "
            f"viewer. Error: {e}")
    finally:
        if merged is not None:
            try:
                merged.close()
            except Exception:
                pass
        try:
            if temp_path.exists():
                temp_path.unlink()
        except Exception:
            pass


def archive_source_pdfs(pdf_paths: List[Path], write) -> List[str]:
    """Move source sheets into an archive subfolder after a merge.

    These PDFs cost an AutoCAD session to produce, so they are moved rather
    than deleted.
    """
    errors = []
    moved = 0

    paths = [Path(p) for p in pdf_paths if Path(p).exists()]
    if not paths:
        return errors

    archive_dir = paths[0].parent / ARCHIVE_DIR_NAME
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        write(f"Could not create archive folder: {e}", "WARNING")
        return [f"archive folder: {e}"]

    for path in paths:
        try:
            target = archive_dir / path.name
            if target.exists():
                stamp = datetime.now().strftime("%H%M%S")
                target = archive_dir / f"{path.stem}_{stamp}{path.suffix}"
            shutil.move(str(path), str(target))
            moved += 1
        except Exception as e:
            errors.append(f"{path.name}: {e}")
            write(f"Could not move {path.name}: {e}", "WARNING")

    write(f"Archived {moved} source PDF(s) to {ARCHIVE_DIR_NAME}\\", "SUCCESS")
    return errors
