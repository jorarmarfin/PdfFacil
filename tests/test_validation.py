import pytest

from app.core.pdf_inspector import PasswordRequired, PdfError, inspect_pdf
from app.services.file_service import expand_paths, list_pdfs_in_folder
from tests.conftest import make_pdf


def test_a05_corrupto(tmp_path):
    p = tmp_path / "malo.pdf"
    p.write_bytes(b"esto no es un pdf")
    with pytest.raises(PdfError):
        inspect_pdf(p)


def test_valida_por_contenido_no_extension(tmp_path):
    p = make_pdf(tmp_path / "sin_extension", ["Z"])
    assert inspect_pdf(p).page_count == 1


def test_a06_pide_contrasena(tmp_path):
    p = make_pdf(tmp_path / "s.pdf", ["S"], password="abc")
    with pytest.raises(PasswordRequired):
        inspect_pdf(p)
    with pytest.raises(PasswordRequired):
        inspect_pdf(p, "mala")
    assert inspect_pdf(p, "abc").page_count == 1


def test_carpeta_no_recursiva_y_alfabetica(tmp_path):
    make_pdf(tmp_path / "b.pdf", ["B"]); make_pdf(tmp_path / "A.pdf", ["A"])
    (tmp_path / "sub").mkdir(); make_pdf(tmp_path / "sub" / "z.pdf", ["Z"])
    (tmp_path / "nota.txt").write_text("x")
    assert [p.name for p in list_pdfs_in_folder(tmp_path)] == ["A.pdf", "b.pdf"]
    assert len(expand_paths([tmp_path])) == 2
