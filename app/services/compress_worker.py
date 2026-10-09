from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from app.core.pdf_compressor import CompressCancelled, CompressError, compress_pdf


class CompressWorker(QThread):
    progress = Signal(int, int)
    succeeded = Signal(str, int, int)  # ruta, antes, después
    failed = Signal(str)
    cancelled = Signal()

    def __init__(self, src: Path, dest: Path, level: str, password: str | None = None, parent=None) -> None:
        super().__init__(parent)
        self._args = (Path(src), Path(dest), level, password)
        self._stop = threading.Event()

    def cancel(self) -> None:
        self._stop.set()

    def run(self) -> None:
        src, dest, level, pw = self._args
        try:
            before, after = compress_pdf(
                src, dest, level, pw,
                progress=lambda n, t: self.progress.emit(n, t),
                is_cancelled=self._stop.is_set)
        except CompressCancelled:
            self.cancelled.emit()
        except CompressError as e:
            self.failed.emit(str(e))
        except Exception:
            self.failed.emit("Ocurrió un error inesperado.")
        else:
            self.succeeded.emit(str(dest), before, after)
