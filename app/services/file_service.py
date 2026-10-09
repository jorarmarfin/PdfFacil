from __future__ import annotations

from pathlib import Path


def format_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.0f} KB"
    return f"{n / 1024 ** 2:.1f} MB"


def list_pdfs_in_folder(folder: Path) -> list[Path]:
    """PDF del nivel actual (no recursivo), orden alfabético natural-insensible."""
    folder = Path(folder)
    files = [p for p in folder.iterdir() if p.is_file() and p.suffix.lower() == ".pdf"]
    return sorted(files, key=lambda p: p.name.casefold())


def expand_paths(paths: list[Path]) -> list[Path]:
    """Archivos tal cual; carpetas -> sus PDF (alfabético por carpeta)."""
    out: list[Path] = []
    for p in paths:
        p = Path(p)
        if p.is_dir():
            out.extend(list_pdfs_in_folder(p))
        elif p.is_file():
            out.append(p)
    return out
