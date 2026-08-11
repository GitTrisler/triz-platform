"""
TRIZ Project Hub — platform utilities.

Two Windows realities that bite on real projects:

1. Long paths. Nested job folders blow past the legacy 260-char MAX_PATH and
   plain open() fails unless the machine has long paths enabled. The extended
   \\\\?\\ prefix bypasses the limit; winsafe() applies it when needed.

2. Cloud placeholders. Desktop Connector / OneDrive show files that are not
   actually on disk. Reading one triggers a hydration download — slow at best,
   a hang or failure at worst. is_cloud_placeholder() detects the reparse
   attributes so the indexer can record the file by name and move on instead
   of accidentally pulling gigabytes out of ACC.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# File attribute flags (winnt.h)
FILE_ATTRIBUTE_OFFLINE = 0x00001000
FILE_ATTRIBUTE_RECALL_ON_OPEN = 0x00040000
FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS = 0x00400000
_PLACEHOLDER_MASK = (FILE_ATTRIBUTE_OFFLINE
                     | FILE_ATTRIBUTE_RECALL_ON_OPEN
                     | FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS)

_LONG_PATH_THRESHOLD = 248  # conservative; prefix well before 260


def winsafe(path, platform: str | None = None) -> str:
    """Return a string path safe to open on Windows regardless of length.

    Applies the extended-length prefix (\\\\?\\ or \\\\?\\UNC\\) to long absolute
    paths on Windows; returns the plain string everywhere else. Absolute-path
    detection is pure string logic (drive letter / UNC) so it is unit-testable
    on any OS via the `platform` override; only genuinely relative paths fall
    back to os.path.abspath, and only when actually running on Windows.
    """
    import re as _re
    p = str(path)
    plat = platform if platform is not None else sys.platform
    if not plat.startswith("win"):
        return p
    if p.startswith("\\\\?\\"):
        return p
    if len(p) < _LONG_PATH_THRESHOLD:
        return p
    q = p.replace("/", "\\")  # \\?\ paths require backslashes
    if _re.match(r"^[A-Za-z]:\\", q):
        return "\\\\?\\" + q
    if q.startswith("\\\\"):  # UNC: \\server\share\... -> \\?\UNC\server\share\...
        return "\\\\?\\UNC\\" + q.lstrip("\\")
    if sys.platform.startswith("win"):  # relative path on a real Windows box
        return winsafe(os.path.abspath(q), plat)
    return p


def is_cloud_placeholder(path: Path) -> bool:
    """True if the file is a cloud-only stub (OneDrive / Desktop Connector)
    whose content is not hydrated locally. Always False on non-Windows."""
    if not sys.platform.startswith("win"):
        return False
    try:
        st = os.stat(path)
        attrs = getattr(st, "st_file_attributes", 0)
        return bool(attrs & _PLACEHOLDER_MASK)
    except OSError:
        return False
