"""Paleta y hoja de estilo global, tomadas del logo (azul marino + turquesa)."""
NAVY = "#0B3A7A"
BLUE = "#1565C0"
TEAL = "#14B8B0"
TEAL_DARK = "#0E918B"
BG = "#EAF2FB"
CARD = "#FFFFFF"
BORDER = "#C5D6EA"

STYLESHEET = f"""
QMainWindow, QDialog {{ background: {BG}; }}
QWidget {{ color: #1B2B40; }}
QLabel#drop {{
    border: 2px dashed {TEAL}; border-radius: 10px; padding: 14px;
    font-size: 15px; color: {NAVY}; background: #F3FBFB;
}}
QPushButton {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 6px;
    padding: 6px 14px; color: {NAVY};
}}
QPushButton:hover {{ background: #DCEBFA; border-color: {BLUE}; }}
QPushButton:pressed {{ background: #C9DFF5; }}
QPushButton:disabled {{ color: #8FA3BA; background: #F1F5FA; }}
QPushButton#primary {{
    background: {TEAL}; color: white; border: none; font-weight: bold; font-size: 15px;
}}
QPushButton#primary:hover {{ background: {TEAL_DARK}; }}
QPushButton#primary:disabled {{ background: #A9DCD9; color: #F2FBFA; }}
QTableView {{
    background: {CARD}; alternate-background-color: #F4F8FD; border: 1px solid {BORDER};
    gridline-color: {BORDER}; selection-background-color: {BLUE}; selection-color: white;
}}
QHeaderView::section {{
    background: {NAVY}; color: white; padding: 5px; border: none;
}}
QProgressBar {{ border: 1px solid {BORDER}; border-radius: 4px; text-align: center; background: {CARD}; }}
QProgressBar::chunk {{ background: {TEAL}; }}
QLabel#count {{ color: {NAVY}; font-weight: bold; }}
"""
