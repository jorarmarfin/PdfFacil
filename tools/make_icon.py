"""Genera assets/ a partir de logo.png y logo-corto.png de la raíz (ejecutar: python tools/make_icon.py).

- assets/icon.png / icon.ico: logo corto (ícono de app e instalador)
- assets/logo.png: logo completo con fondo blanco convertido a transparente (cabecera)
"""
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets"
OUT.mkdir(exist_ok=True)

short = Image.open(ROOT / "logo-corto.png").convert("RGBA")
side = max(short.size)
sq = Image.new("RGBA", (side, side), (0, 0, 0, 0))
sq.paste(short, ((side - short.width) // 2, (side - short.height) // 2))
sq = sq.resize((512, 512), Image.LANCZOS)
sq.save(OUT / "icon.png")
sq.save(OUT / "icon.ico", sizes=[(s, s) for s in (16, 24, 32, 48, 64, 128, 256)])

full = Image.open(ROOT / "logo.png").convert("RGBA")
px = full.load()
for y in range(full.height):  # blanco -> transparente (con suavizado de borde)
    for x in range(full.width):
        r, g, b, _ = px[x, y]
        m = min(r, g, b)
        if m > 235:
            px[x, y] = (r, g, b, max(0, (255 - m) * 12))
full.save(OUT / "logo.png")
