"""Genera los logos del MSIX desde assets/icon.png (Pillow). Uso: python tools/make_msix_assets.py <carpeta_destino>"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

SQUARE = {"StoreLogo.png": 50, "Square44x44Logo.png": 44, "Square150x150Logo.png": 150, "SmallTile.png": 71}
# Las variantes con escala evitan que Windows reescale y se vean borrosas.
SCALES = (100, 125, 150, 200, 400)


def _fit(src: Image.Image, w: int, h: int) -> Image.Image:
    canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    side = min(w, h)
    icon = src.resize((side, side), Image.LANCZOS)
    canvas.paste(icon, ((w - side) // 2, (h - side) // 2), icon)
    return canvas


def main(dest: Path) -> None:
    src = Image.open(Path(__file__).resolve().parent.parent / "assets" / "icon.png").convert("RGBA")
    dest.mkdir(parents=True, exist_ok=True)
    for name, size in SQUARE.items():
        _fit(src, size, size).save(dest / name)
    _fit(src, 310, 150).save(dest / "Wide310x150Logo.png")
    # Iconos de la lista de aplicaciones sin placa (barra de tareas, Inicio).
    for size in (16, 24, 32, 48, 256):
        _fit(src, size, size).save(dest / f"Square44x44Logo.targetsize-{size}.png")
        _fit(src, size, size).save(dest / f"Square44x44Logo.targetsize-{size}_altform-unplated.png")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
