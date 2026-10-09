from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, QSettings


class SettingsService:
    def __init__(self) -> None:
        self._s = QSettings("PDFFacil", "PDFFacil")

    @property
    def last_dir(self) -> str:
        v = self._s.value("last_dir", "")
        return v if isinstance(v, str) and v and Path(v).is_dir() else str(Path.home())

    @last_dir.setter
    def last_dir(self, value: str) -> None:
        self._s.setValue("last_dir", value)

    def save_geometry(self, data: QByteArray) -> None:
        self._s.setValue("geometry", data)

    def load_geometry(self) -> QByteArray | None:
        v = self._s.value("geometry")
        return v if isinstance(v, QByteArray) else None
