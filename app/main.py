from __future__ import annotations

import ctypes
import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.resources import resource_path
from app.ui.main_window import MainWindow
from app.ui.theme import STYLESHEET


def main() -> int:
    if sys.platform == "win32":  # icono propio en la barra de tareas
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PDFFacil.App")
        except Exception:
            pass
    app = QApplication(sys.argv)
    app.setApplicationName("PDF Fácil")
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)
    icon = resource_path("assets/icon.png")
    if icon.is_file():
        app.setWindowIcon(QIcon(str(icon)))
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
