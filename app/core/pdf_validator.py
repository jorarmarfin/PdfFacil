from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

from app.models.pdf_item import PdfItem


class DestinationError(Exception):
    """El destino elegido no es seguro."""


def _same(a: Path, b: Path) -> bool:
    try:
        if a.exists() and b.exists():
            return os.path.samefile(a, b)
    except OSError:
        pass
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def validate_destination(dest: Path, items: Iterable[PdfItem]) -> None:
    dest = Path(dest)
    for it in items:
        if _same(dest, it.path):
            raise DestinationError(
                f"El destino coincide con el original «{it.display_name}». Elige otro nombre."
            )
    if not dest.parent.is_dir():
        raise DestinationError("La carpeta de destino no existe.")
    if dest.is_dir():
        raise DestinationError("El destino es una carpeta, no un archivo.")


def validate_items(items: Iterable[PdfItem]) -> None:
    items = list(items)
    if not items:
        raise DestinationError("No hay archivos en la lista.")
    for it in items:
        if not it.path.is_file():
            raise DestinationError(f"No se encuentra «{it.display_name}». ¿Se movió o borró?")
