from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class PdfItem:
    path: Path
    page_count: int
    size_bytes: int
    is_encrypted: bool = False
    has_signature: bool = False
    status: str = "ready"  # ready | error
    # Solo en memoria; nunca se persiste ni se registra en logs.
    password: str | None = field(default=None, repr=False)
    id: str = field(default_factory=lambda: uuid.uuid4().hex)

    @property
    def display_name(self) -> str:
        return self.path.name
