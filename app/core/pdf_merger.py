from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable, Sequence

from pypdf import PdfReader, PdfWriter

from app.core.pdf_inspector import PdfError, open_reader
from app.core.pdf_validator import validate_destination, validate_items
from app.models.pdf_item import PdfItem

ProgressCb = Callable[[int, int, str], None]  # (archivo_actual, total, nombre)
CancelCb = Callable[[], bool]


class MergeCancelled(Exception):
    pass


class MergeError(Exception):
    pass


def merge_pdfs(
    items: Sequence[PdfItem],
    dest: Path,
    progress: ProgressCb | None = None,
    is_cancelled: CancelCb | None = None,
) -> int:
    """Une los PDF en el orden dado. Devuelve el total de páginas escritas.

    Escribe a un temporal en la carpeta destino y lo publica con os.replace.
    Ante error o cancelación borra el temporal y deja intacto el destino previo.
    """
    items = tuple(items)  # copia inmutable
    dest = Path(dest)
    validate_items(items)
    validate_destination(dest, items)
    cancelled = is_cancelled or (lambda: False)

    expected = sum(i.page_count for i in items)
    fd, tmp_name = tempfile.mkstemp(prefix=".pdffacil_", suffix=".tmp", dir=str(dest.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        writer = PdfWriter()
        total = len(items)
        for n, it in enumerate(items, start=1):
            if cancelled():
                raise MergeCancelled()
            if progress:
                progress(n, total, it.display_name)
            try:
                reader = open_reader(it.path, it.password)
                for page in reader.pages:
                    writer.add_page(page)
            except PdfError as e:
                raise MergeError(f"«{it.display_name}»: {e}") from e
        if cancelled():
            raise MergeCancelled()
        with open(tmp, "wb") as fh:
            writer.write(fh)
        writer.close()

        check = PdfReader(str(tmp))
        if len(check.pages) != expected:
            raise MergeError("El PDF resultante no tiene el número de páginas esperado.")
        del check

        if cancelled():
            raise MergeCancelled()
        os.replace(tmp, dest)
        return expected
    except (MergeCancelled, MergeError):
        raise
    except PermissionError as e:
        raise MergeError("No hay permiso para escribir en esa ubicación (¿el archivo está abierto?).") from e
    except OSError as e:
        raise MergeError(f"No se pudo escribir el archivo (¿disco lleno o sin permisos?): {e.strerror or e}") from e
    except Exception as e:
        raise MergeError("Ocurrió un error inesperado al unir los PDF.") from e
    finally:
        try:
            tmp.unlink()
        except FileNotFoundError:
            pass
        except OSError:
            pass
