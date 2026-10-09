from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader
from pypdf.errors import PyPdfError

from app.models.pdf_item import PdfItem


class PdfError(Exception):
    """Error de lectura con mensaje apto para el usuario."""


class PasswordRequired(PdfError):
    """El PDF está cifrado y falta (o es incorrecta) la contraseña."""


def _has_signature(reader: PdfReader) -> bool:
    try:
        root = reader.trailer["/Root"]
        form = root.get("/AcroForm")
        if form is None:
            return False
        form = form.get_object()
        if int(form.get("/SigFlags", 0)) & 1:
            return True
        for f in form.get("/Fields", []):
            if f.get_object().get("/FT") == "/Sig":
                return True
    except Exception:
        return False
    return False


def open_reader(path: Path, password: str | None = None) -> PdfReader:
    """Abre y desbloquea un PDF. Lanza PdfError / PasswordRequired."""
    try:
        reader = PdfReader(str(path))
        if reader.is_encrypted:
            ok = reader.decrypt(password or "")
            if not ok:
                raise PasswordRequired("Este PDF requiere contraseña.")
        # Fuerza lectura real de la estructura de páginas.
        _ = len(reader.pages)
        return reader
    except PdfError:
        raise
    except FileNotFoundError:
        raise PdfError("No se encuentra el archivo.")
    except PermissionError:
        raise PdfError("No hay permiso para leer el archivo.")
    except (PyPdfError, ValueError, KeyError, TypeError, OSError, RecursionError):
        raise PdfError("El archivo está dañado o no es un PDF válido.")


def inspect_pdf(path: Path, password: str | None = None) -> PdfItem:
    path = Path(path).resolve()
    reader = open_reader(path, password)
    try:
        pages = len(reader.pages)
    except Exception:
        raise PdfError("El archivo está dañado o no es un PDF válido.")
    if pages < 1:
        raise PdfError("El PDF no tiene páginas.")
    return PdfItem(
        path=path,
        page_count=pages,
        size_bytes=path.stat().st_size,
        is_encrypted=reader.is_encrypted,
        has_signature=_has_signature(reader),
        password=password if reader.is_encrypted else None,
    )
