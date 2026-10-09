from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication, QFileDialog, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QProgressDialog, QPushButton, QVBoxLayout, QWidget,
)

from app.core.pdf_inspector import PasswordRequired, PdfError, inspect_pdf
from app.core.pdf_validator import DestinationError, validate_destination, validate_items
from app.models.pdf_item import PdfItem
from app.services.file_service import expand_paths, list_pdfs_in_folder
from app.services.merge_worker import MergeWorker
from app.services.settings_service import SettingsService
from app.resources import resource_path
from app.ui.compress_dialog import CompressDialog
from app.ui.pdf_list_model import PdfListModel
from app.ui.widgets.pdf_table_view import PdfTableView, urls_to_paths


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PDF Fácil")
        self.resize(820, 560)
        self.setAcceptDrops(True)
        self.settings = SettingsService()
        self.model = PdfListModel()
        self.worker: MergeWorker | None = None
        self.progress_dlg: QProgressDialog | None = None
        self._build_ui()
        geo = self.settings.load_geometry()
        if geo:
            self.restoreGeometry(geo)
        self._refresh()

    # ---------- UI ----------
    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        lay = QVBoxLayout(root)

        logo = resource_path("assets/logo.png")
        if logo.is_file():
            header = QLabel()
            pm = QPixmap(str(logo)).scaledToHeight(56, Qt.SmoothTransformation)
            header.setPixmap(pm)
            lay.addWidget(header)

        top = QHBoxLayout()
        self.drop_label = QLabel("Suelta aquí tus PDF")
        self.drop_label.setAlignment(Qt.AlignCenter)
        self.drop_label.setObjectName("drop")
        self.btn_add = QPushButton("Agregar PDF")
        self.btn_folder = QPushButton("Agregar carpeta")
        top.addWidget(self.drop_label, 1)
        top.addWidget(self.btn_add)
        top.addWidget(self.btn_folder)
        lay.addLayout(top)

        self.table = PdfTableView()
        self.table.setModel(self.model)
        lay.addWidget(self.table, 1)

        row = QHBoxLayout()
        self.btn_up = QPushButton("Subir")
        self.btn_down = QPushButton("Bajar")
        self.btn_remove = QPushButton("Quitar")
        self.btn_clear = QPushButton("Vaciar lista")
        self.btn_compress = QPushButton("Comprimir PDF…")
        for b in (self.btn_up, self.btn_down, self.btn_remove, self.btn_clear):
            row.addWidget(b)
        row.addStretch(1)
        row.addWidget(self.btn_compress)
        lay.addLayout(row)

        bottom = QHBoxLayout()
        self.count_label = QLabel()
        self.count_label.setObjectName("count")
        self.btn_merge = QPushButton("UNIR PDF")
        self.btn_merge.setMinimumHeight(44)
        self.btn_merge.setMinimumWidth(180)
        self.btn_merge.setObjectName("primary")
        self.btn_merge.setDefault(True)
        bottom.addWidget(self.count_label, 1)
        bottom.addWidget(self.btn_merge)
        lay.addLayout(bottom)

        self.btn_add.clicked.connect(self.on_add_files)
        self.btn_folder.clicked.connect(self.on_add_folder)
        self.btn_up.clicked.connect(self.on_up)
        self.btn_down.clicked.connect(self.on_down)
        self.btn_remove.clicked.connect(self.on_remove)
        self.btn_clear.clicked.connect(self.on_clear)
        self.btn_merge.clicked.connect(self.on_merge)
        self.btn_compress.clicked.connect(lambda: self.open_compress())
        self.table.files_dropped.connect(self.add_paths)
        self.table.rows_moved.connect(lambda _: self._refresh())
        self.model.rowsInserted.connect(lambda *_: self._refresh())
        self.model.rowsRemoved.connect(lambda *_: self._refresh())
        self.model.modelReset.connect(self._refresh)
        self.table.selectionModel().selectionChanged.connect(lambda *_: self._refresh())

        for seq, fn in (
            ("Ctrl+O", self.on_add_files), ("Ctrl+Shift+O", self.on_add_folder),
            ("Delete", self.on_remove), ("Ctrl+Up", self.on_up), ("Ctrl+Down", self.on_down),
            ("Ctrl+Return", self.on_merge),
        ):
            QShortcut(QKeySequence(seq), self, activated=fn)

        self.setTabOrder(self.btn_add, self.btn_folder)
        self.setTabOrder(self.btn_folder, self.table)
        self.setTabOrder(self.table, self.btn_up)
        self.setTabOrder(self.btn_up, self.btn_down)
        self.setTabOrder(self.btn_down, self.btn_remove)
        self.setTabOrder(self.btn_remove, self.btn_clear)
        self.setTabOrder(self.btn_clear, self.btn_compress)
        self.setTabOrder(self.btn_compress, self.btn_merge)

    def _refresh(self) -> None:
        n, p = self.model.rowCount(), self.model.total_pages()
        self.count_label.setText(f"{n} archivo{'s' if n != 1 else ''} · {p} página{'s' if p != 1 else ''}")
        busy = self.worker is not None
        sel = bool(self.table.selected_rows())
        self.btn_merge.setEnabled(n > 0 and not busy)
        self.btn_up.setEnabled(sel and not busy)
        self.btn_down.setEnabled(sel and not busy)
        self.btn_remove.setEnabled(sel and not busy)
        self.btn_clear.setEnabled(n > 0 and not busy)
        self.btn_add.setEnabled(not busy)
        self.btn_folder.setEnabled(not busy)

    # ---------- Importación ----------
    def dragEnterEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e) -> None:
        if e.mimeData().hasUrls():
            self.add_paths(urls_to_paths(e.mimeData()))
            e.acceptProposedAction()

    def on_add_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self, "Agregar PDF", self.settings.last_dir, "Documentos PDF (*.pdf);;Todos (*)")
        if files:
            self.settings.last_dir = str(Path(files[0]).parent)
            self.add_paths([Path(f) for f in files])

    def on_add_folder(self) -> None:
        d = QFileDialog.getExistingDirectory(self, "Agregar carpeta", self.settings.last_dir)
        if not d:
            return
        self.settings.last_dir = d
        pdfs = list_pdfs_in_folder(Path(d))
        if not pdfs:
            QMessageBox.information(self, "PDF Fácil", "La carpeta no contiene archivos PDF.")
            return
        self.add_paths(pdfs)

    def _ask_password(self, name: str, retry: bool) -> str | None:
        msg = f"«{name}» está protegido con contraseña."
        if retry:
            msg = "Contraseña incorrecta. " + msg
        pw, ok = QInputDialog.getText(self, "Contraseña", msg, QLineEdit.Password)
        return pw if ok else None

    def add_paths(self, paths: list[Path]) -> None:
        """Agrega al final, en el orden recibido (carpetas ya expandidas y ordenadas)."""
        paths = expand_paths([Path(p) for p in paths])
        existing = {it.path for it in self.model.items}
        new_items: list[PdfItem] = []
        errors: list[str] = []
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            for p in paths:
                try:
                    rp = p.resolve()
                except OSError:
                    rp = p
                if rp in existing or any(i.path == rp for i in new_items):
                    QApplication.restoreOverrideCursor()
                    r = QMessageBox.question(
                        self, "Archivo repetido",
                        f"«{p.name}» ya está en la lista.\n¿Agregarlo de nuevo?")
                    QApplication.setOverrideCursor(Qt.WaitCursor)
                    if r != QMessageBox.Yes:
                        continue
                item = self._inspect_with_password(p)
                if isinstance(item, str):
                    errors.append(f"{p.name}: {item}")
                elif item is not None:
                    new_items.append(item)
        finally:
            QApplication.restoreOverrideCursor()
        self.model.add_items(new_items)
        if errors:
            QMessageBox.warning(self, "No se pudieron agregar algunos archivos", "\n".join(errors))

    def _inspect_with_password(self, p: Path):
        """PdfItem, mensaje de error (str) o None si el usuario canceló."""
        pw: str | None = None
        retry = False
        while True:
            try:
                return inspect_pdf(p, pw)
            except PasswordRequired:
                QApplication.restoreOverrideCursor()
                pw = self._ask_password(p.name, retry)
                QApplication.setOverrideCursor(Qt.WaitCursor)
                if pw is None:
                    return None
                retry = True
            except PdfError as e:
                return str(e)

    # ---------- Edición de lista ----------
    def on_up(self) -> None:
        self.table.select_rows(self.model.move_up(self.table.selected_rows()))

    def on_down(self) -> None:
        self.table.select_rows(self.model.move_down(self.table.selected_rows()))

    def on_remove(self) -> None:
        if self.worker is None:
            self.model.remove_rows(self.table.selected_rows())

    def on_clear(self) -> None:
        if self.model.rowCount() and QMessageBox.question(
                self, "Vaciar lista", "¿Quitar todos los archivos de la lista?\n(No se borran del disco)"
        ) == QMessageBox.Yes:
            self.model.clear()

    # ---------- Unión ----------
    def on_merge(self) -> None:
        if self.worker is not None:
            return
        items = self.model.items  # copia inmutable
        try:
            validate_items(items)
        except DestinationError as e:
            QMessageBox.warning(self, "PDF Fácil", str(e))
            return
        if any(i.has_signature for i in items):
            if QMessageBox.warning(
                    self, "Firma digital detectada",
                    "Algún documento tiene firma digital. Al unirlos la firma "
                    "se perderá o quedará inválida.\n¿Continuar?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                return
        start = str(Path(self.settings.last_dir) / "Documento_unido.pdf")
        dest_s, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF unido", start, "Documento PDF (*.pdf)",
            options=QFileDialog.DontConfirmOverwrite)
        if not dest_s:
            return
        dest = Path(dest_s)
        if dest.suffix.lower() != ".pdf":
            dest = dest.with_name(dest.name + ".pdf")
        try:
            validate_destination(dest, items)
        except DestinationError as e:
            QMessageBox.warning(self, "Destino no válido", str(e))
            return
        if dest.exists() and QMessageBox.question(
                self, "Sobrescribir",
                f"«{dest.name}» ya existe.\n¿Quieres reemplazarlo?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
            return
        self.settings.last_dir = str(dest.parent)

        self.progress_dlg = QProgressDialog("Preparando…", "Cancelar", 0, len(items), self)
        self.progress_dlg.setWindowTitle("Uniendo PDF")
        self.progress_dlg.setWindowModality(Qt.WindowModal)
        self.progress_dlg.setMinimumDuration(0)
        self.progress_dlg.setAutoClose(False)
        self.progress_dlg.setAutoReset(False)
        self.progress_dlg.setValue(0)

        self.worker = MergeWorker(items, dest, self)
        self.worker.progress.connect(self._on_progress)
        self.worker.succeeded.connect(self._on_success)
        self.worker.failed.connect(self._on_failed)
        self.worker.cancelled.connect(self._on_cancelled)
        self.worker.finished.connect(self._on_thread_finished)
        self.progress_dlg.canceled.connect(self.worker.cancel)
        self._refresh()
        self.worker.start()

    def _on_progress(self, n: int, total: int, name: str) -> None:
        if self.progress_dlg:
            self.progress_dlg.setLabelText(f"Archivo {n} de {total}: {name}")
            self.progress_dlg.setValue(n - 1)

    def _close_progress(self) -> None:
        if self.progress_dlg:
            self.progress_dlg.canceled.disconnect()
            self.progress_dlg.close()
            self.progress_dlg = None

    def _on_thread_finished(self) -> None:
        if self.worker:
            self.worker.deleteLater()
        self.worker = None
        self._refresh()

    def _on_success(self, path: str, pages: int) -> None:
        self._close_progress()
        box = QMessageBox(self)
        box.setWindowTitle("Listo")
        box.setIcon(QMessageBox.Information)
        box.setText(f"PDF creado con {pages} página{'s' if pages != 1 else ''}.")
        box.setInformativeText(path)
        b_file = box.addButton("Abrir archivo", QMessageBox.AcceptRole)
        b_dir = box.addButton("Abrir carpeta", QMessageBox.ActionRole)
        b_zip = box.addButton("Comprimir…", QMessageBox.ActionRole)
        box.addButton("Cerrar", QMessageBox.RejectRole)
        box.exec()
        if box.clickedButton() is b_zip:
            self.open_compress(Path(path))
        elif box.clickedButton() is b_file:
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))
        elif box.clickedButton() is b_dir:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(path).parent)))

    def open_compress(self, src: Path | None = None) -> None:
        CompressDialog(self, src).exec()

    def _on_failed(self, msg: str) -> None:
        self._close_progress()
        QMessageBox.critical(self, "No se pudo unir", msg)

    def _on_cancelled(self) -> None:
        self._close_progress()
        QMessageBox.information(self, "PDF Fácil", "Operación cancelada. No se creó ningún archivo.")

    def closeEvent(self, e) -> None:
        if self.worker is not None:
            if QMessageBox.question(
                    self, "Unión en curso", "Se está uniendo un PDF. ¿Cancelar y salir?",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No) != QMessageBox.Yes:
                e.ignore()
                return
            self.worker.cancel()
            self.worker.wait(10000)
        self.settings.save_geometry(self.saveGeometry())
        e.accept()
