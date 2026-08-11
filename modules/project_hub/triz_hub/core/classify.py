"""
TRIZ Project Hub — document classification.

Cheap heuristics on doc number / title / filename so the object page can group
occurrences the way the concept doc describes (P&IDs, isometrics, datasheets,
vendor docs). Refine per project as naming conventions firm up.
"""

from __future__ import annotations


def classify(doc_number: str | None, title: str | None, filename: str) -> str:
    hay = " ".join(x for x in (doc_number, title, filename) if x).upper()
    if any(k in hay for k in ("P&ID", "PID-", "PID_", " PID", "PIPING AND INSTRUMENT")):
        return "pid"
    if any(k in hay for k in ("ISO-", "ISO_", "ISOMETRIC")):
        return "isometric"
    if any(k in hay for k in ("PFD", "PROCESS FLOW")):
        return "pfd"
    if any(k in hay for k in ("DATA SHEET", "DATASHEET", "DS-")):
        return "datasheet"
    if any(k in hay for k in ("VENDOR", "CUT SHEET", "CUTSHEET", "CATALOG")):
        return "vendor"
    if any(k in hay for k in ("GA-", "GENERAL ARRANGEMENT", "PLOT PLAN", "LAYOUT")):
        return "arrangement"
    if any(k in hay for k in ("REGISTER", "INDEX", "LIST")):
        return "register"
    if any(k in hay for k in ("SCAN", "POINT CLOUD", "RCP", "RCS")):
        return "scan"
    return "general"
