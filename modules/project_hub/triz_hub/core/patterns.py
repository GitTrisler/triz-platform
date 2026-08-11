"""
TRIZ Project Hub — tag pattern engine.

Every client numbers things differently, so tag recognition is data, not code.
Patterns live in the project database (tag_patterns table), seeded with the
defaults below, and are editable in the Patterns page. Higher priority wins
when matches overlap (so PT-101 resolves as an instrument, not equipment
"T-101" with a stray P).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# (name, object_type, regex, priority, enabled)
DEFAULT_PATTERNS = [
    ("Line number (size-service-number-spec)", "line",
     r'\b\d{1,2}\s?"-[A-Z]{1,4}-\d{3,5}-[A-Z0-9]{2,10}(?:-[A-Z0-9]{1,6})?\b', 100, 1),
    ("Instrument (ISA prefixes)", "instrument",
     r'\b(?:PT|PI|PIC|PIT|PG|PSV|PSH|PSL|PSHH|PSLL|PDT|PDI|PDIT|'
     r'FT|FI|FIC|FIT|FE|FQ|FQI|FV|FCV|'
     r'LT|LI|LIC|LIT|LG|LSH|LSL|LSHH|LSLL|LCV|LV|'
     r'TT|TI|TIC|TIT|TE|TW|TG|TSH|TSL|TCV|TV|'
     r'AT|AI|AIC|AIT|AE|HS|HV|XV|ZSO|ZSC|SDV|BDV|VT|VI)-\d{2,5}[A-Z]?\b', 90, 1),
    ("Valve", "valve",
     r'\b(?:V|BV|GV|CV|CHV|NV|MOV)-\d{2,5}[A-Z]?\b', 80, 1),
    ("Equipment", "equipment",
     r'\b(?:P|TK|T|E|C|D|R|K|H|F|B|S|X|AG|CP|EX|HX|VS)-\d{2,5}[A-Z]?\b', 70, 1),
    ("Drawing reference", "drawing",
     r'\b(?:DWG|PID|ISO|GA|PFD)-[A-Z0-9]{0,4}-?\d{2,5}(?:-\d{1,4})?\b', 60, 1),
    ("Nozzle (noisy — enable per project)", "nozzle",
     r'\bN-\d{1,3}[A-Z]?\b', 40, 0),
]

# Fallback doc-number extraction from a filename stem, e.g.
# "PID-001_Rev2_Process Flow.pdf" -> doc=PID-001, rev=2
FILENAME_DOC_RE = re.compile(
    r'^(?P<doc>[A-Z]{1,5}-?[A-Z0-9]{0,4}-?\d{2,5}(?:-\d{1,4})?)'
    r'(?:[_\-\s.]+REV[_\-\s.]?(?P<rev>[A-Z0-9]{1,3}))?',
    re.IGNORECASE,
)


@dataclass
class TagMatch:
    tag: str
    object_type: str
    start: int
    end: int
    priority: int


class TagMatcher:
    """Compiles patterns once, finds all tags in a text block, and resolves
    overlapping matches by priority then length."""

    def __init__(self, pattern_rows):
        self.compiled = []
        for row in pattern_rows:
            try:
                rx = re.compile(row["regex"])
            except re.error:
                continue  # bad user regex: skip rather than crash the indexer
            self.compiled.append((rx, row["object_type"], int(row["priority"])))

    def find(self, text: str) -> list[TagMatch]:
        if not text:
            return []
        raw: list[TagMatch] = []
        for rx, obj_type, priority in self.compiled:
            for m in rx.finditer(text):
                tag = re.sub(r"\s+", "", m.group(0)).upper()
                raw.append(TagMatch(tag, obj_type, m.start(), m.end(), priority))
        if not raw:
            return []
        # Overlap resolution: prefer higher priority, then longer match.
        raw.sort(key=lambda t: (t.start, -t.priority, -(t.end - t.start)))
        kept: list[TagMatch] = []
        last_end = -1
        for t in sorted(raw, key=lambda t: (-t.priority, -(t.end - t.start), t.start)):
            if all(t.end <= k.start or t.start >= k.end for k in kept):
                kept.append(t)
        kept.sort(key=lambda t: t.start)
        return kept

    def find_unique(self, text: str) -> dict[str, TagMatch]:
        out: dict[str, TagMatch] = {}
        for t in self.find(text):
            out.setdefault(t.tag, t)
        return out


def context_snippet(text: str, start: int, end: int, radius: int = 45) -> str:
    a, b = max(0, start - radius), min(len(text), end + radius)
    snip = text[a:b].replace("\n", " ")
    return re.sub(r"\s{2,}", " ", snip).strip()


def parse_filename_doc(stem: str):
    """Return (doc_number, revision) parsed from a filename stem, or (None, None)."""
    m = FILENAME_DOC_RE.match(stem.strip().upper())
    if not m:
        return None, None
    return m.group("doc"), m.group("rev")
