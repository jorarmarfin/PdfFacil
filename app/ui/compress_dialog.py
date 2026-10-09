from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QButtonGroup, QDialog, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMessageBox, QProgressBar, QPushButton, QRadioButton, QVBoxLayout,
)

from app.core.pdf_inspector import PasswordRequired, PdfError, inspect_pdf
from app.services.compress_worker import CompressWorker
from app.services.file_service import format_size
from app.services.settings_service import SettingsService

OPTIONS = [
    ("baja", "Calidad original", "Sin pérdida de calidad. Reduce poco."),
    ("media", "Equilibrada (recomendada)", "Imágenes algo más ligeras; se ve igual en pantalla."),
    ("alta", "Máxima compresión", "Archivo mucho más pequeño; imágenes con menos detalle."),
]


class CompressDialog(QDialog):
    def __init__(self, parent=None, src: Path | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Comprimir PDF")
        self.setMinimumWidth(520)
        self.settings = SettingsService()
        self.worker: CompressWorker | None = None
        self.src: Path | None = None
        self.password: str | None = None

        lay = QVBoxLayout(self)
        row = QHBoxLayout()
        self.src_edit = QLineEdit(readOnly=True)
        self.src_edit.setPlaceholderText("Elige el PDF a comprimir")
        self.btn_pick = QPushButton("Elegir PDF…")
        row.addWidget(self.src_edit, 1)
        row.addWidget(self.btn_pick)
        lay.addLayout(row)
        self.info = QLabel("")
        lay.addWidget(self.info)

        lay.addWidget(QLabel("<b>Nivel de compresión</b>"))
        self.group = QButtonGroup(self)
        self.radios: dict[str, QRadioButton] = {}
        for key, title, desc in OPTIONS:
            rb = QRadioButton(f"{title} — {desc}")
            self.radios[key] = rb
            self.group.addButton(rb)
            lay.addWidget(rb)
        self.radios["media"].setChecked(True)

        self.bar = QProgressBar()
        self.bar.setVisible(False)
        lay.addWidget(self.bar)

        btns = QHBoxLayout()
        btns.addStretch(1)
        self.btn_go = QPushButton("Comprimir")
        self.btn_go.setDefault(True)
        self.btn_close = QPushButton("Cerrar")
        btns.addWidget(self.btn_go)
        btns.addWidget(self.btn_close)
        lay.addLayout(btns)

        self.btn_pick.clicked.connect(self.on_pick)
        self.btn_go.clicked.connect(self.on_compress)
        self.btn_close.clicked.connect(self.close)
        self.btn_go.setEnabled(False)
        if src:
            self.set_source(Path(src))

    def level(self) -> str:
        return next(k for k, rb in self.radios.items() if rb.isChecked())

    def on_pick(self) -> None:
        f, _ = QFileDialog.getOpenFileName(
            self, "Elegir PDF", self.settings.last_dir, "Documentos PDF (*.pdf)")
        if f:
            self.set_source(Path(f))

    def set_source(self, p: Path) -> None:
        self.password = None
        while True:
            try:
                item = inspect_pdf(p, self.password)
                break
            except PasswordRequired:
                pw, ok = QInputDialog.getText(
                    self, "Contraseña", f"«{p.name}» está protegido con contraseña.", QLineEdit.Password)
                if not ok:
                    return
                self.password = pw
            except PdfError as e:
                QMessageBox.warning(self, "PDF Fácil", f"{p.name}: {e}")
                return
        self.src = item.path
        self.src_edit.setText(str(item.path))
        self.info.setText(f"{item.page_count} páginas · {format_size(item.size_bytes)}")
        self.btn_go.setEnabled(True)

    def on_compress(self) -> None:
        if self.worker or not self.src:
            return
        default = self.src.with_name(self.src.stem + "_comprimido.pdf")
        dest_s, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF comprimido", str(default), "Documento PDF (*.pdf)",
            options=QFileDialog.DontConfirmOverwrite)
        if not dest_s:
            return
        dest = Path(dest_s)
        if dest.suffix.lower() != ".pdf":
            dest = dest.with_name(dest.name + ".pdf")
        if dest.exists():
            try:
                same = dest.samefile(self.src)
            except OSError:
                same = False
            if same:
                QMessageBox.warning(self, "Destino no válido",
                                    "El destino coincide con el original. Elige otro nombre.")
                return
            if QMessageBox.question(
                    self, "Sobrescribir", f"«{dest.name}» ya existe.\n¿Quieres reemplazarlo?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
        self.settings.last_dir = str(dest.parent)
        self._set_busy(True)
        self.worker = CompressWorker(self.src, dest, self.level(), self.password, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.succeeded.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.cancelled.connect(lambda: self._finish("Operación cancelada. No se creó ningún archivo."))
        self.worker.finished.connect(self._on_thread_finished)
        self.worker.start()

    def _set_busy(self, busy: bool) -> None:
        self.bar.setVisible(busy)
        self.bar.setRange(0, 0 if busy else 1)
        for w in (self.btn_go, self.btn_pick, *self.radios.values()):
            w.setEnabled(not busy)

    def _on_progress(self, n: int, total: int) -> None:
        self.bar.setRange(0, total)
        self.bar.setValue(n)

    def _on_thread_finished(self) -> None:
        if self.worker:
            self.worker.deleteLater()
        self.worker = None

    def _finish(self, msg: str, error: bool = False) -> None:
        self._set_busy(False)
        self.btn_go.setEnabled(self.src is not None)
        (QMessageBox.critical if error else QMessageBox.information)(self, "Comprimir PDF", msg)

    def _on_failed(self, msg: str) -> None:
        self._finish(msg, error=True)

    def _on_success(self, path: str, before: int, after: int) -> None:
        self._set_busy(False)
        self.btn_go.setEnabled(True)
        pct = round((1 - after / before) * 100)
        box = QMessageBox(self)
        box.setWindowTitle("Listo")
        box.setIcon(QMessageBox.Information)
        box.setText(f"De {format_size(before)} a {format_size(after)} (−{pct} %).")
        box.setInformativeText(path)
        b_file = box.addButton("Abrir archivo", QMessageBox.AcceptRole)
        b_dir = box.addButton("Abrir carpeta", QMessageBox.ActionRole)
        box.addButton("Cerrar", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is b_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif box.clickedButton() is b_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))

    def closeEvent(self, e) -> None:
        if self.worker:
            if QMessageBox.question(
                    self, "Compresión en curso", "¿Cancelar y cerrar?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                e.ignore()
                return
            self.worker.cancel()
            self.worker.wait(10000)
        e.accept()

    def reject(self) -> None:  # Esc
        self.close()
