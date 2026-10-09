from __future__ import annotations

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from app.models.pdf_item import PdfItem
from app.services.file_service import format_size

HEADERS = ["#", "Documento", "Páginas", "Tamaño", "Estado"]


class PdfListModel(QAbstractTableModel):
    def __init__(self) -> None:
        super().__init__()
        self._items: list[PdfItem] = []

    # --- API de datos ---
    @property
    def items(self) -> tuple[PdfItem, ...]:
        return tuple(self._items)

    def total_pages(self) -> int:
        return sum(i.page_count for i in self._items)

    def add_items(self, items: list[PdfItem]) -> None:
        if not items:
            return
        start = len(self._items)
        self.beginInsertRows(QModelIndex(), start, start + len(items) - 1)
        self._items.extend(items)
        self.endInsertRows()

    def remove_rows(self, rows: list[int]) -> None:
        for r in sorted(set(rows), reverse=True):
            if 0 <= r < len(self._items):
                self.beginRemoveRows(QModelIndex(), r, r)
                del self._items[r]
                self.endRemoveRows()
        self._renumber()

    def clear(self) -> None:
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def move_rows(self, rows: list[int], target: int) -> list[int]:
        """Mueve `rows` para que queden juntas antes de la posición `target`
        (índice en la lista original). Devuelve las nuevas posiciones."""
        rows = sorted({r for r in rows if 0 <= r < len(self._items)})
        if not rows:
            return []
        target = max(0, min(target, len(self._items)))
        moving = [self._items[r] for r in rows]
        before = sum(1 for r in rows if r < target)
        rest = [it for i, it in enumerate(self._items) if i not in set(rows)]
        pos = target - before
        new = rest[:pos] + moving + rest[pos:]
        if new == self._items:
            return rows
        self.beginResetModel()
        self._items = new
        self.endResetModel()
        return list(range(pos, pos + len(moving)))

    def move_up(self, rows: list[int]) -> list[int]:
        rows = sorted(rows)
        if not rows or rows[0] == 0:
            return rows
        return self.move_rows(rows, rows[0] - 1)

    def move_down(self, rows: list[int]) -> list[int]:
        rows = sorted(rows)
        if not rows or rows[-1] >= len(self._items) - 1:
            return rows
        return self.move_rows(rows, rows[-1] + 2)

    def _renumber(self) -> None:
        if self._items:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 0))

    # --- QAbstractTableModel ---
    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def columnCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(HEADERS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return HEADERS[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        it = self._items[index.row()]
        col = index.column()
        if role == Qt.DisplayRole:
            return [
                str(index.row() + 1),
                it.display_name,
                str(it.page_count),
                format_size(it.size_bytes),
                "Listo" if it.status == "ready" else "Error",
            ][col]
        if role == Qt.ToolTipRole:
            return str(it.path)
        if role == Qt.TextAlignmentRole and col in (0, 2, 3):
            return int(Qt.AlignRight | Qt.AlignVCenter)
        return None

    def flags(self, index):
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        return base | Qt.ItemIsDragEnabled if index.isValid() else base
