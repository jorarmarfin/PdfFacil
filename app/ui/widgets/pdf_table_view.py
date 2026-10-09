from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QHeaderView, QTableView


def urls_to_paths(mime) -> list[Path]:
    return [Path(u.toLocalFile()) for u in mime.urls() if u.isLocalFile()]


class PdfTableView(QTableView):
    """Tabla reordenable por arrastre; también acepta archivos del Explorador."""

    files_dropped = Signal(list)
    rows_moved = Signal(list)  # nuevas posiciones seleccionadas

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)
        self.setDefaultDropAction(Qt.MoveAction)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setWordWrap(False)
        self.verticalHeader().setVisible(False)
        self.horizontalHeader().setStretchLastSection(False)

    def setModel(self, model) -> None:
        super().setModel(model)
        h = self.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.Stretch)
        for c in (2, 3, 4):
            h.setSectionResizeMode(c, QHeaderView.ResizeToContents)

    def selected_rows(self) -> list[int]:
        return sorted({i.row() for i in self.selectionModel().selectedRows()})

    def select_rows(self, rows: list[int]) -> None:
        sm = self.selectionModel()
        sm.clearSelection()
        for r in rows:
            sm.select(self.model().index(r, 0),
                      sm.SelectionFlag.Select | sm.SelectionFlag.Rows)

    def dragEnterEvent(self, e) -> None:
        if e.mimeData().hasUrls() or e.source() is self:
            e.acceptProposedAction()
        else:
            e.ignore()

    def dragMoveEvent(self, e) -> None:
        if e.mimeData().hasUrls() or e.source() is self:
            e.acceptProposedAction()
        else:
            e.ignore()

    def dropEvent(self, e) -> None:
        if e.source() is self:
            rows = self.selected_rows()
            idx = self.indexAt(e.position().toPoint())
            if idx.isValid():
                rect = self.visualRect(idx)
                target = idx.row() + (1 if e.position().toPoint().y() > rect.center().y() else 0)
            else:
                target = self.model().rowCount()
            new_rows = self.model().move_rows(rows, target)
            self.select_rows(new_rows)
            self.rows_moved.emit(new_rows)
            e.ignore()  # evita que Qt borre las filas de origen
        elif e.mimeData().hasUrls():
            self.files_dropped.emit(urls_to_paths(e.mimeData()))
            e.acceptProposedAction()
        else:
            e.ignore()
