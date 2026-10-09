from __future__ import annotations

import os
import tempfile
from pathlib import Path
from typing import Callable

from pypdf import PdfReader, PdfWriter

from app.core.pdf_inspector import PdfError, open_reader

# nivel -> (calidad JPEG o None = sin tocar imágenes, lado máximo en px o None)
LEVELS: dict[str, tuple[int | None, int | None]] = {
    "baja": (None, None),   # sin pérdida de calidad
    "media": (70, None),
    "alta": (45, 1400),
}


class CompressCancelled(Exception):
    pass


class CompressError(Exception):
    pass


def _recompress_images(page, quality: int, max_side: int | None) -> None:
    for img in list(page.images):
        try:
            pil = img.image
            if pil.mode not in ("RGB", "L"):
                pil = pil.convert("RGB")
            if max_side and max(pil.size) > max_side:
                pil.thumbnail((max_side, max_side))
            img.replace(pil, quality=quality)
        except Exception:
            continue  # imagen no soportada: se deja como está


def compress_pdf(
    src: Path,
    dest: Path,
    level: str = "media",
    password: str | None = None,
    progress: Callable[[int, int], None] | None = None,
    is_cancelled: Callable[[], bool] | None = None,
) -> tuple[int, int]:
    """Comprime `src` en `dest`. Devuelve (bytes_antes, bytes_después).

    Lanza CompressError si no se logra reducir el tamaño (no se crea archivo).
    """
    src, dest = Path(src), Path(dest)
    if level not in LEVELS:
        raise CompressError("Nivel de compresión desconocido.")
    if os.path.normcase(os.path.abspath(src)) == os.path.normcase(os.path.abspath(dest)) or (
            dest.exists() and os.path.samefile(src, dest)):
        raise CompressError("El destino no puede ser el mismo archivo original.")
    if not dest.parent.is_dir():
        raise CompressError("La carpeta de destino no existe.")
    cancelled = is_cancelled or (lambda: False)
    quality, max_side = LEVELS[level]
    before = src.stat().st_size

    fd, tmp_name = tempfile.mkstemp(prefix=".pdffacil_", suffix=".tmp", dir=str(dest.parent))
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        try:
            reader = open_reader(src, password)
        except PdfError as e:
            raise CompressError(str(e)) from e
        writer = PdfWriter()
        total = len(reader.pages)
        for n, page in enumerate(reader.pages, start=1):
            if cancelled():
                raise CompressCancelled()
            if progress:
                progress(n, total)
            p = writer.add_page(page)
            if quality is not None:
                _recompress_images(p, quality, max_side)
            try:
                p.compress_content_streams()
            except Exception:
                pass
        writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
        with open(tmp, "wb") as fh:
            writer.write(fh)
        writer.close()
        if cancelled():
            raise CompressCancelled()

        if len(PdfReader(str(tmp)).pages) != total:
            raise CompressError("El PDF comprimido no es válido.")
        after = tmp.stat().st_size
        if after >= before:
            raise CompressError(
                "No se pudo reducir el tamaño de este PDF (ya está optimizado). No se creó ningún archivo.")
        os.replace(tmp, dest)
        return before, after
    except (CompressCancelled, CompressError):
        raise
    except PermissionError as e:
        raise CompressError("No hay permiso para escribir en esa ubicación (¿el archivo está abierto?).") from e
    except OSError as e:
        raise CompressError(f"No se pudo escribir el archivo: {e.strerror or e}") from e
    except Exception as e:
        raise CompressError("Ocurrió un error inesperado al comprimir.") from e
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
