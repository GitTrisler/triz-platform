try:
    from ui.design_system import Colors, Fonts
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))

    from ui.design_system import Colors, Fonts


STYLE = f"""
/* ---------- base ---------- */
QMainWindow, QDialog {{
    background-color: {Colors.BG};
}}

QWidget {{
    font-family: {Fonts.FAMILY};
    color: {Colors.TEXT};
}}

QFrame#Sidebar {{
    background-color: {Colors.SURFACE};
    border-right: 1px solid {Colors.BORDER};
}}

QFrame#Header {{
    background-color: {Colors.SURFACE};
    border-bottom: 1px solid {Colors.BORDER};
}}

QFrame#Hairline {{
    background-color: {Colors.BORDER};
    border: none;
    max-height: 1px;
    min-height: 1px;
}}

/* ---------- cards ---------- */
QFrame#Card {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: 10px;
}}

QFrame#Card:hover {{
    border-color: {Colors.BORDER_HI};
}}

QFrame#MetricCard {{
    background-color: {Colors.SURFACE_2};
    border: 1px solid {Colors.BORDER};
    border-radius: 9px;
}}

QFrame#MetricCard:hover {{
    border-color: {Colors.BORDER_HI};
}}

QFrame#ProgressPanel {{
    background-color: {Colors.SURFACE_2};
    border: 1px solid {Colors.BORDER};
    border-radius: 9px;
}}

/* ---------- typography ---------- */
QLabel {{
    color: {Colors.TEXT};
    background: transparent;
}}

QLabel#Muted {{
    color: {Colors.MUTED};
}}

QLabel#Kicker {{
    color: {Colors.FAINT};
    font-family: {Colors.MONO};
    font-size: 9.5px;
    font-weight: 700;
    letter-spacing: 2.5px;
}}

QLabel#Title {{
    color: {Colors.TEXT};
    font-size: {Fonts.TITLE};
    font-weight: 700;
    letter-spacing: -0.3px;
}}

QLabel#Subtitle {{
    color: {Colors.SECONDARY};
    font-size: {Fonts.BODY};
}}

QLabel#FieldLabel {{
    color: {Colors.MUTED};
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 1.2px;
}}

QLabel#TRIZBadge {{
    background-color: {Colors.BLUE_DIM};
    color: {Colors.BLUE_HOVER};
    font-family: {Colors.MONO};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1.5px;
    padding: 6px 12px;
    border-radius: 5px;
}}

/* ---------- inputs ---------- */
QLineEdit {{
    min-height: 18px;
    background-color: {Colors.SURFACE_2};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: 7px;
    padding: 8px 12px;
    font-size: {Fonts.BODY};
    selection-background-color: {Colors.BLUE_DIM};
}}

QLineEdit:hover {{
    border-color: {Colors.BORDER_HI};
}}

QLineEdit:focus {{
    border-color: {Colors.BLUE};
}}

QLineEdit:disabled {{
    color: {Colors.FAINT};
}}

QComboBox {{
    min-height: 18px;
    background-color: {Colors.SURFACE_2};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: 7px;
    padding: 7px 11px;
}}

QComboBox:hover {{
    border-color: {Colors.BORDER_HI};
}}

QComboBox QAbstractItemView {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER_HI};
    selection-background-color: {Colors.BLUE_DIM};
    color: {Colors.TEXT};
}}

QCheckBox {{
    color: {Colors.SECONDARY};
    spacing: 8px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 15px;
    height: 15px;
    border: 1px solid {Colors.BORDER_HI};
    border-radius: 4px;
    background-color: {Colors.SURFACE_2};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.BLUE};
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.BLUE};
    border-color: {Colors.BLUE};
}}

QRadioButton {{
    color: {Colors.SECONDARY};
    spacing: 8px;
    background: transparent;
}}

QRadioButton::indicator {{
    width: 14px;
    height: 14px;
    border: 1px solid {Colors.BORDER_HI};
    border-radius: 7px;
    background-color: {Colors.SURFACE_2};
}}

QRadioButton::indicator:checked {{
    background-color: {Colors.BLUE};
    border-color: {Colors.BLUE};
}}

/* ---------- buttons ---------- */
QPushButton {{
    background-color: {Colors.BLUE};
    color: {Colors.INK};
    border: none;
    padding: 9px 16px;
    font-weight: 700;
    font-size: 12.5px;
    letter-spacing: 0.3px;
    border-radius: 7px;
}}

QPushButton:hover {{
    background-color: {Colors.BLUE_HOVER};
}}

QPushButton:disabled {{
    background-color: {Colors.BLUE_DIM};
    color: {Colors.MUTED};
}}

QPushButton#GhostButton {{
    background-color: transparent;
    color: {Colors.SECONDARY};
    border: 1px solid {Colors.BORDER};
    font-weight: 600;
}}

QPushButton#GhostButton:hover {{
    border-color: {Colors.BLUE};
    color: {Colors.BLUE};
}}

QPushButton#GhostButton:disabled {{
    color: {Colors.FAINT};
    border-color: {Colors.BORDER};
}}

/* ---------- navigation ---------- */
QTreeWidget {{
    background-color: transparent;
    color: {Colors.TEXT};
    border: none;
    outline: none;
    font-size: 12.5px;
}}

QTreeWidget::item {{
    padding: 8px 6px;
    border-radius: 6px;
    color: {Colors.SECONDARY};
    border-left: 2px solid transparent;
}}

QTreeWidget::item:hover {{
    background-color: {Colors.SURFACE_2};
    color: {Colors.TEXT};
}}

QTreeWidget::item:selected {{
    background-color: {Colors.SURFACE_2};
    color: {Colors.BLUE};
    border-left: 2px solid {Colors.BLUE};
}}

/* ---------- console / logs ---------- */
QTextEdit, QPlainTextEdit {{
    background-color: {Colors.CONSOLE};
    color: {Colors.SECONDARY};
    border: 1px solid {Colors.BORDER};
    border-radius: 9px;
    padding: 8px 10px;
    font-family: {Colors.MONO};
    font-size: 11.5px;
    selection-background-color: {Colors.BLUE_DIM};
}}

QListWidget {{
    background-color: {Colors.CONSOLE};
    color: {Colors.SECONDARY};
    border: 1px solid {Colors.BORDER};
    border-radius: 9px;
    outline: none;
    font-family: {Colors.MONO};
    font-size: 11.5px;
    padding: 4px;
}}

QListWidget::item {{
    padding: 4px 7px;
    border-radius: 4px;
}}

QListWidget::item:hover {{
    background-color: {Colors.SURFACE_2};
}}

QListWidget::item:selected {{
    background-color: {Colors.BLUE_DIM};
    color: {Colors.TEXT};
}}

/* ---------- tables ---------- */
QTableWidget {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: 10px;
    gridline-color: transparent;
    color: {Colors.TEXT};
}}

QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid {Colors.BORDER};
}}

QTableWidget::item:selected {{
    background-color: {Colors.BLUE_DIM};
    color: {Colors.TEXT};
}}

QHeaderView::section {{
    background-color: {Colors.SURFACE};
    color: {Colors.MUTED};
    border: none;
    border-bottom: 1px solid {Colors.BORDER_HI};
    padding: 8px 10px;
    font-size: 10.5px;
    font-weight: 700;
    letter-spacing: 1px;
}}

/* ---------- tabs, splitters, misc ---------- */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    background-color: {Colors.SURFACE};
    border-radius: 8px;
}}

QTabBar::tab {{
    background-color: transparent;
    color: {Colors.MUTED};
    padding: 8px 15px;
    border: none;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 0.8px;
}}

QTabBar::tab:selected {{
    color: {Colors.BLUE};
    border-bottom: 2px solid {Colors.BLUE};
}}

QSplitter::handle {{
    background-color: {Colors.BORDER};
}}

QProgressBar {{
    background-color: {Colors.SURFACE_3};
    border: none;
    border-radius: 2px;
    max-height: 5px;
    min-height: 5px;
    text-align: center;
    color: transparent;
}}

QProgressBar::chunk {{
    background-color: {Colors.BLUE};
    border-radius: 2px;
}}

QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 2px;
}}

QScrollBar::handle:vertical {{
    background: {Colors.BORDER_HI};
    border-radius: 4px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Colors.FAINT};
}}

QScrollBar:horizontal {{
    background: transparent;
    height: 9px;
    margin: 2px;
}}

QScrollBar::handle:horizontal {{
    background: {Colors.BORDER_HI};
    border-radius: 4px;
    min-width: 28px;
}}

QScrollBar::add-line, QScrollBar::sub-line {{
    width: 0px;
    height: 0px;
}}

QScrollBar::add-page, QScrollBar::sub-page {{
    background: transparent;
}}

QToolTip {{
    background-color: {Colors.SURFACE_3};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER_HI};
    padding: 5px 9px;
    font-size: 11.5px;
}}

QStatusBar {{
    background-color: {Colors.SURFACE};
    color: {Colors.MUTED};
    border-top: 1px solid {Colors.BORDER};
    font-size: 11.5px;
}}
"""
