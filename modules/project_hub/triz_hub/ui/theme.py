"""
TRIZ Project Hub — "Drafting" design system.

The UI borrows its language from the drawing sheet itself: a faint blueprint
dot-grid workspace, registration-tick card corners, micro-tracked uppercase
field labels, monospace tags, and one disciplined accent. Layered surfaces
(bg → surface1 cards → surface2 insets → surface3 hover) replace the old
single-panel look; every color routes through PALETTE.

Root fix vs. the previous theme: QWidget no longer gets a global background,
so labels/checkboxes sitting on cards stop painting dark rectangles behind
themselves. Surfaces are opted-in per container.
"""

from __future__ import annotations

PALETTE = {
    # layers
    "bg":         "#0A0F1A",
    "surface1":   "#0F1726",   # cards
    "surface2":   "#131D31",   # inputs, metric cards, insets
    "surface3":   "#1A2740",   # hover
    "console":    "#0A101C",   # log / code surfaces
    # lines
    "border":     "#1E2A40",
    "border_hi":  "#2B3B58",
    # ink
    "text":       "#E8EDF6",
    "secondary":  "#9FB0C8",
    "muted":      "#64748B",
    "faint":      "#3E4C63",
    # brand + status
    "accent":     "#38BDF8",
    "accent_hi":  "#7DD3FC",
    "accent_dim": "#0B2E44",
    "success":    "#22C55E",
    "success_soft": "#86EFAC",
    "warning":    "#F59E0B",
    "warning_soft": "#FCD34D",
    "error":      "#EF4444",
    "error_soft": "#FCA5A5",
    "info":       "#9FB0C8",
    "job":        "#38BDF8",
}
# Legacy keys used across pages — kept as aliases of the new layers.
PALETTE.update({
    "panel": PALETTE["surface1"],
    "panel_hi": PALETTE["surface3"],
    "metric_bg": PALETTE["surface2"],
})

TYPE_COLORS = {
    "equipment":  "#38BDF8",
    "line":       "#22C55E",
    "valve":      "#F59E0B",
    "instrument": "#A78BFA",
    "drawing":    "#94A3B8",
    "nozzle":     "#2DD4BF",
}

SEVERITY_COLORS = {"error": PALETTE["error"], "warning": PALETTE["warning"],
                   "info": PALETTE["muted"], "success": PALETTE["success"],
                   "job": PALETTE["job"]}

SOFT_SEVERITY = {"error": PALETTE["error_soft"], "warning": PALETTE["warning_soft"],
                 "success": PALETTE["success_soft"], "job": PALETTE["accent_hi"],
                 "info": "#B9C6DB"}

DOC_CLASS_COLORS = {
    "pid":          "#38BDF8",
    "isometric":    "#22C55E",
    "pfd":          "#2DD4BF",
    "datasheet":    "#A78BFA",
    "vendor":       "#F59E0B",
    "arrangement":  "#FB923C",
    "model_export": "#2DD4BF",
    "register":     "#94A3B8",
    "scan":         "#94A3B8",
    "general":      "#94A3B8",
}

MONO = "'Cascadia Code', 'Consolas', monospace"


def build_qss() -> str:
    p = PALETTE
    return f"""
/* ---------- base: no global widget background (labels stay clean) -------- */
QMainWindow, QDialog {{ background: {p['bg']}; }}
QWidget {{
    color: {p['text']};
    font-family: 'Segoe UI', 'Inter', sans-serif;
    font-size: 13px;
    background: transparent;
}}
QStackedWidget {{ background: transparent; }}
QFrame#Workspace {{ background-color: {p['bg']}; }}

/* ---------- typography ---------- */
QLabel#Title {{ font-size: 21px; font-weight: 700; letter-spacing: -0.2px; }}
QLabel#Subtitle {{ color: {p['secondary']}; font-size: 12.5px; }}
QLabel#Kicker {{
    color: {p['faint']}; font-family: {MONO};
    font-size: 9.5px; font-weight: 700; letter-spacing: 2.5px;
}}
QLabel#Muted {{ color: {p['muted']}; }}
QLabel#H2 {{ font-size: 15px; font-weight: 700; }}
QLabel#TagHeader {{
    font-size: 26px; font-weight: 700; font-family: {MONO};
}}
QLabel#EmptyState {{ color: {p['muted']}; font-size: 13.5px; padding: 34px; }}

/* ---------- shell ---------- */
QFrame#Sidebar {{ background: {p['surface1']}; border-right: 1px solid {p['border']}; }}
QFrame#Header  {{ background: {p['surface1']}; border-bottom: 1px solid {p['border']}; }}
QFrame#HairlineH {{ background: {p['border']}; border: none; max-height: 1px; min-height: 1px; }}

QListWidget#Nav {{ background: transparent; border: none; outline: none;
    font-size: 12.5px; font-weight: 600; }}
QListWidget#Nav::item {{
    padding: 8px 12px; border-radius: 6px; margin: 1px 10px;
    color: {p['muted']}; border-left: 2px solid transparent;
}}
QListWidget#Nav::item:hover {{ background: {p['surface2']}; color: {p['secondary']}; }}
QListWidget#Nav::item:selected {{
    background: {p['surface2']}; color: {p['accent']};
    border-left: 2px solid {p['accent']};
}}

/* ---------- cards & panels ---------- */
QFrame#Card {{
    background: {p['surface1']};
    border: 1px solid {p['border']};
    border-radius: 10px;
}}
QFrame#Card:hover {{ border-color: {p['border_hi']}; }}
QFrame#MetricCard {{
    background: {p['surface2']};
    border: 1px solid {p['border']};
    border-radius: 9px;
}}
QFrame#MetricCard:hover {{ border-color: {p['border_hi']}; }}
QFrame#ProgressPanel {{
    background: {p['surface2']};
    border: 1px solid {p['border']};
    border-radius: 9px;
}}

/* ---------- inputs ---------- */
QLineEdit {{
    background: {p['surface2']};
    border: 1px solid {p['border']};
    border-radius: 7px;
    padding: 7px 11px;
    selection-background-color: {p['accent_dim']};
    color: {p['text']};
}}
QLineEdit:hover {{ border-color: {p['border_hi']}; }}
QLineEdit:focus {{ border-color: {p['accent']}; }}
QLineEdit:read-only {{ color: {p['secondary']}; }}

QCheckBox {{ spacing: 8px; color: {p['secondary']}; background: transparent; }}
QCheckBox::indicator {{
    width: 15px; height: 15px;
    border: 1px solid {p['border_hi']};
    border-radius: 4px;
    background: {p['surface2']};
}}
QCheckBox::indicator:hover {{ border-color: {p['accent']}; }}
QCheckBox::indicator:checked {{ background: {p['accent']}; border-color: {p['accent']}; }}

QComboBox {{
    background: {p['surface2']}; border: 1px solid {p['border']};
    border-radius: 7px; padding: 6px 10px;
}}
QComboBox QAbstractItemView {{
    background: {p['surface1']}; border: 1px solid {p['border_hi']};
    selection-background-color: {p['accent_dim']};
}}

/* ---------- buttons ---------- */
QPushButton {{
    background: {p['surface2']};
    border: 1px solid {p['border']};
    border-radius: 7px;
    padding: 7px 16px;
    color: {p['text']};
    font-weight: 600;
}}
QPushButton:hover {{ background: {p['surface3']}; border-color: {p['border_hi']}; }}
QPushButton:pressed {{ background: {p['surface1']}; }}
QPushButton:disabled {{ color: {p['faint']}; border-color: {p['border']}; }}
QPushButton#GhostButton {{
    background: transparent; border: 1px solid {p['border']};
    color: {p['secondary']};
}}
QPushButton#GhostButton:hover {{ border-color: {p['accent']}; color: {p['accent']}; }}
QPushButton#Chip {{
    background: transparent; border: 1px solid {p['border']};
    border-radius: 12px; padding: 3px 13px;
    color: {p['muted']}; font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
}}
QPushButton#Chip:hover {{ border-color: {p['border_hi']}; color: {p['secondary']}; }}
QPushButton#Chip:checked {{
    background: {p['accent_dim']}; border-color: {p['accent']};
    color: {p['accent_hi']};
}}

/* ---------- tables ---------- */
QTableWidget {{
    background: {p['surface1']};
    border: 1px solid {p['border']};
    border-radius: 10px;
    gridline-color: transparent;
    color: {p['text']};
}}
QTableWidget::item {{ padding: 7px 10px; border-bottom: 1px solid {p['border']}; }}
QTableWidget::item:hover {{ background: {p['surface2']}; }}
QTableWidget::item:selected {{ background: {p['accent_dim']}; color: {p['text']}; }}
QHeaderView::section {{
    background: {p['surface1']};
    color: {p['muted']};
    border: none;
    border-bottom: 1px solid {p['border_hi']};
    padding: 8px 10px;
    font-size: 10.5px; font-weight: 700; letter-spacing: 1px;
}}
QTableCornerButton::section {{ background: {p['surface1']}; border: none; }}

/* ---------- console / logs ---------- */
QPlainTextEdit, QTextEdit {{
    background: {p['console']};
    border: 1px solid {p['border']};
    border-radius: 9px;
    padding: 8px 10px;
    font-family: {MONO};
    font-size: 11.5px;
    color: {p['secondary']};
    selection-background-color: {p['accent_dim']};
}}

/* ---------- misc ---------- */
QProgressBar {{
    background: {p['surface3']}; border: none; border-radius: 2px;
    max-height: 4px; min-height: 4px; text-align: center; color: transparent;
}}
QProgressBar::chunk {{ background: {p['accent']}; border-radius: 2px; }}
QScrollBar:vertical {{ background: transparent; width: 9px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {p['border_hi']}; border-radius: 4px; min-height: 28px; }}
QScrollBar::handle:vertical:hover {{ background: {p['faint']}; }}
QScrollBar:horizontal {{ background: transparent; height: 9px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {p['border_hi']}; border-radius: 4px; min-width: 28px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QToolTip {{
    background: {p['surface3']}; color: {p['text']};
    border: 1px solid {p['border_hi']}; padding: 5px 9px; font-size: 11.5px;
}}
QStatusBar {{
    background: {p['surface1']}; border-top: 1px solid {p['border']};
    color: {p['muted']}; font-size: 11.5px;
}}
QDialog QLabel {{ background: transparent; }}
"""
