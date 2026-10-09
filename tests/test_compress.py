import os

import pytest
from PIL import Image
from reportlab.pdfgen import canvas

from app.core.pdf_compressor import CompressCancelled, CompressError, compress_pdf
from tests.conftest import make_pdf, page_texts


@pytest.fixture
def pdf_pesado(tmp_path):
    img = tmp_path / "foto.png"
    Image.frombytes("RGB", (1200, 1200), os.urandom(1200 * 1200 * 3)).save(img)
    p = tmp_path / "pesado.pdf"
    c = canvas.Canvas(str(p))
    c.drawString(100, 780, "TEXTO1")
    c.drawImage(str(img), 50, 100, 400, 400)
    c.showPage(); c.save()
    return p


@pytest.mark.parametrize("nivel", ["media", "alta"])
def test_reduce_y_conserva_texto(pdf_pesado, tmp_path, nivel):
    out = tmp_path / "o.pdf"
    antes, despues = compress_pdf(pdf_pesado, out, nivel)
    assert despues < antes * 0.7 and out.stat().st_size == despues
    assert page_texts(out) == ["TEXTO1"]


def test_sin_ganancia_no_crea_archivo(tmp_path):
    base = make_pdf(tmp_path / "base.pdf", ["A"])
    p = tmp_path / "ligero.pdf"
    compress_pdf(base, p, "baja")  # ya optimizado
    out = tmp_path / "o.pdf"
    with pytest.raises(CompressError):
        compress_pdf(p, out, "baja")
    assert not out.exists() and list(tmp_path.glob(".pdffacil_*")) == []


def test_destino_igual_original(pdf_pesado):
    with pytest.raises(CompressError):
        compress_pdf(pdf_pesado, pdf_pesado, "media")


def test_cancelar(pdf_pesado, tmp_path):
    out = tmp_path / "o.pdf"
    with pytest.raises(CompressCancelled):
        compress_pdf(pdf_pesado, out, "media", is_cancelled=lambda: True)
    assert not out.exists() and list(tmp_path.glob(".pdffacil_*")) == []


def test_original_intacto(pdf_pesado, tmp_path):
    antes = pdf_pesado.read_bytes()
    compress_pdf(pdf_pesado, tmp_path / "o.pdf", "alta")
    assert pdf_pesado.read_bytes() == antes


def test_dialogo(qtbot, pdf_pesado):
    from app.ui.compress_dialog import CompressDialog
    d = CompressDialog(None, pdf_pesado)
    qtbot.addWidget(d)
    assert d.btn_go.isEnabled() and d.level() == "media"
