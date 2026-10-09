import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from pypdf import PdfWriter
from reportlab.pdfgen import canvas


def make_pdf(path, labels, password=None):
    """PDF con una página por etiqueta, con el texto de la etiqueta."""
    c = canvas.Canvas(str(path))
    for lab in labels:
        c.drawString(100, 700, lab)
        c.showPage()
    c.save()
    if password:
        from pypdf import PdfReader
        r = PdfReader(str(path))
        w = PdfWriter()
        for p in r.pages:
            w.add_page(p)
        w.encrypt(password)
        with open(path, "wb") as fh:
            w.write(fh)
    return path


def page_texts(path, password=None):
    from pypdf import PdfReader
    r = PdfReader(str(path))
    if r.is_encrypted:
        r.decrypt(password or "")
    return [p.extract_text().strip() for p in r.pages]


@pytest.fixture
def pdfs(tmp_path):
    d = tmp_path / "in"
    d.mkdir()
    return {
        "a": make_pdf(d / "Solicitud ñandú.pdf", ["A1", "A2"]),
        "b": make_pdf(d / "Identidad.pdf", ["B1"]),
        "c": make_pdf(d / "Anexos.pdf", ["C1", "C2", "C3"]),
    }
