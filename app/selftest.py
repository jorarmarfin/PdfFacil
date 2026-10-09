"""Autoprueba sin interfaz: `PDF_Facil.exe --selftest <carpeta_salida>`.

La usa el CI para comprobar que la app funciona dentro del contenedor MSIX:
crea PDF, los lista y lee, une, comprime, guarda y relee. Escribe selftest.json
en la carpeta de salida (la app es --windowed y no tiene consola).
"""
from __future__ import annotations

import json
import random
import sys
import traceback
from pathlib import Path

from pypdf import PdfReader, PdfWriter


def _make_blank_pdf(path: Path, pages: int) -> None:
    w = PdfWriter()
    for _ in range(pages):
        w.add_blank_page(width=200, height=200)
    with open(path, "wb") as fh:
        w.write(fh)


def _make_image_pdf(path: Path) -> None:
    from PIL import Image

    rnd = random.Random(7)
    img = Image.new("RGB", (900, 900))
    img.putdata([(rnd.randrange(256), rnd.randrange(256), rnd.randrange(256)) for _ in range(900 * 900)])
    img.save(path, "PDF", quality=95)


def run(outdir: Path) -> dict:
    from PySide6.QtWidgets import QApplication

    from app.core.pdf_compressor import compress_pdf
    from app.core.pdf_inspector import inspect_pdf
    from app.core.pdf_merger import merge_pdfs
    from app.services.file_service import expand_paths
    from app.services.settings_service import SettingsService

    steps: dict[str, str] = {}

    def step(name: str, fn) -> None:
        try:
            steps[name] = fn() or "ok"
        except Exception:
            steps[name] = "FALLO: " + traceback.format_exc(limit=3)

    work = outdir / "work"
    work.mkdir(parents=True, exist_ok=True)
    src = work / "origen"
    src.mkdir(exist_ok=True)
    state: dict = {}

    def seleccion() -> None:
        _make_blank_pdf(src / "a.pdf", 2)
        _make_blank_pdf(src / "b.pdf", 3)
        _make_image_pdf(src / "imagen.pdf")
        found = expand_paths([src])
        assert [p.name for p in found] == ["a.pdf", "b.pdf", "imagen.pdf"], found
        state["found"] = found

    def lectura() -> None:
        state["items"] = [inspect_pdf(p) for p in state["found"]]
        assert [i.page_count for i in state["items"]] == [2, 3, 1]

    def union() -> None:
        dest = work / "unido.pdf"
        n = merge_pdfs(state["items"][:2], dest)
        assert n == 5 and len(PdfReader(str(dest)).pages) == 5

    def compresion() -> str:
        before, after = compress_pdf(src / "imagen.pdf", work / "imagen_comprimido.pdf", "media")
        assert after < before
        return f"ok {before} -> {after} bytes"

    def ajustes() -> None:
        s = SettingsService()
        s.last_dir = str(work)
        assert SettingsService().last_dir == str(work)

    def ventana() -> None:
        from app.ui.main_window import MainWindow

        _app = QApplication.instance() or QApplication(sys.argv[:1])
        MainWindow().close()

    for name, fn in (("seleccion", seleccion), ("lectura", lectura), ("union", union),
                     ("compresion", compresion), ("ajustes", ajustes), ("ventana", ventana)):
        step(name, fn)

    return {"ok": all(v.startswith("ok") for v in steps.values()), "steps": steps}


def main(argv: list[str]) -> int:
    outdir = Path(argv[0]) if argv else Path.cwd()
    outdir.mkdir(parents=True, exist_ok=True)
    try:
        result = run(outdir)
    except Exception:
        result = {"ok": False, "steps": {"general": traceback.format_exc()}}
    (outdir / "selftest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    return 0 if result["ok"] else 1
