from __future__ import annotations

import threading
from pathlib import Path
from typing import Sequence

from PySide6.QtCore import QThread, Signal

from app.core.pdf_merger import MergeCancelled, MergeError, merge_pdfs
from app.core.pdf_validator import DestinationError
from app.models.pdf_item import PdfItem


class MergeWorker(QThread):
    progress = Signal(int, int, str)
    succeeded = Signal(str, int)  # ruta, páginas
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, items: Sequence[PdfItem], dest: Path, parent=None) -> None:
        super().__init__(parent)
        self._items = tuple(items)
        self._dest = Path(dest)
        self._stop = threading.Event()

    def cancel(self) -> None:
        self._stop.set()

    def run(self) -> None:
        try:
            pages = merge_pdfs(
                self._items, self._dest,
                progress=lambda n, t, name: self.progress.emit(n, t, name),
                is_cancelled=self._stop.is_set,
            )
        except MergeCancelled:
            self.cancelled.emit()
        except (MergeError, DestinationError) as e:
            self.failed.emit(str(e))
        except Exception:
            self.failed.emit("Ocurrió un error inesperado.")
        else:
            self.succeeded.emit(str(self._dest), pages)
