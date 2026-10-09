from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from app.resources import resource_path
from app.version import APP_NAME, AUTHOR, AUTHOR_URL, __version__


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Créditos")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setSpacing(10)

        logo = resource_path("assets/logo.png")
        if logo.is_file():
            img = QLabel(alignment=Qt.AlignCenter)
            img.setPixmap(QPixmap(str(logo)).scaledToHeight(64, Qt.SmoothTransformation))
            lay.addWidget(img)

        ver = QLabel(f"Versión {__version__}", alignment=Qt.AlignCenter)
        ver.setObjectName("muted")
        lay.addWidget(ver)

        txt = QLabel(
            f"Desarrollado por <b>{AUTHOR}</b>.<br>"
            "¿Ideas, mejoras o un sistema a medida? ¡Contáctame!",
            alignment=Qt.AlignCenter, wordWrap=True)
        lay.addWidget(txt)

        link = QLabel(f'<a href="{AUTHOR_URL}">{AUTHOR_URL}</a>', alignment=Qt.AlignCenter)
        link.setOpenExternalLinks(True)
        lay.addWidget(link)

        row = QHBoxLayout()
        row.addStretch(1)
        btn_web = QPushButton("Contactar")
        btn_web.setObjectName("primary")
        btn_web.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(AUTHOR_URL)))
        btn_close = QPushButton("Cerrar")
        btn_close.clicked.connect(self.accept)
        row.addWidget(btn_web)
        row.addWidget(btn_close)
        row.addStretch(1)
        lay.addLayout(row)
        self.setWindowTitle(f"Créditos · {APP_NAME}")
