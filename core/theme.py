try:
    from ui.design_system import Colors, Fonts
except ModuleNotFoundError:
    from pathlib import Path
    import sys

    ROOT = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(ROOT))

    from ui.design_system import Colors, Fonts


STYLE = f"""
QMainWindow {{
    background-color: {Colors.BG};
}}

QWidget {{
    font-family: {Fonts.FAMILY};
}}

QFrame#Sidebar {{
    background-color: {Colors.SURFACE};
    border-right: 1px solid {Colors.BORDER};
}}

QFrame#Header {{
    background-color: {Colors.BG};
    border-bottom: 1px solid {Colors.BORDER};
}}

QFrame#Card {{
    background-color: {Colors.SURFACE_2};
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
}}

QFrame#MetricCard {{
    background-color: {Colors.SURFACE};
    border: 1px solid {Colors.BORDER};
    border-radius: 8px;
}}

QLabel {{
    color: {Colors.TEXT};
}}

QLabel#Muted {{
    color: {Colors.MUTED};
}}

QLabel#Title {{
    color: {Colors.TEXT};
    font-size: {Fonts.TITLE};
    font-weight: 800;
}}

QLabel#Subtitle {{
    color: {Colors.MUTED};
    font-size: {Fonts.BODY};
}}

QLabel#TRIZBadge {{
    background-color: {Colors.BLUE};
    color: #001018;
    font-weight: 900;
    padding: 6px 12px;
    border-radius: 4px;
}}

QLineEdit {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    border-radius: 6px;
    padding: 8px 12px;
    font-size: {Fonts.BODY};
}}

QPushButton {{
    background-color: {Colors.BLUE};
    color: #001018;
    border: none;
    padding: 9px 14px;
    font-weight: 800;
    border-radius: 5px;
}}

QPushButton:hover {{
    background-color: {Colors.BLUE_HOVER};
}}

QPushButton#GhostButton {{
    background-color: {Colors.SURFACE_2};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
}}

QPushButton#GhostButton:hover {{
    background-color: {Colors.SURFACE_3};
}}

QTreeWidget {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: none;
    font-size: {Fonts.BODY};
}}

QTreeWidget::item {{
    padding: 7px 6px;
}}

QTreeWidget::item:selected {{
    background-color: {Colors.SURFACE_2};
    border-left: 4px solid {Colors.BLUE};
}}

QTextEdit {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border: 1px solid {Colors.BORDER};
    font-family: Consolas;
    font-size: 12px;
}}

QTabWidget::pane {{
    border: 1px solid {Colors.BORDER};
    background-color: {Colors.SURFACE};
}}

QTabBar::tab {{
    background-color: {Colors.SURFACE_2};
    color: {Colors.MUTED};
    padding: 7px 14px;
    border: 1px solid {Colors.BORDER};
}}

QTabBar::tab:selected {{
    background-color: {Colors.SURFACE};
    color: {Colors.TEXT};
    border-bottom: 2px solid {Colors.BLUE};
}}

QSplitter::handle {{
    background-color: {Colors.BORDER};
}}

QStatusBar {{
    background-color: {Colors.SURFACE};
    color: {Colors.MUTED};
    border-top: 1px solid {Colors.BORDER};
}}
"""
