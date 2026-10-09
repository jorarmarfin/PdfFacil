import pytest

from app.core.pdf_inspector import inspect_pdf
from app.core.pdf_merger import MergeCancelled, MergeError, merge_pdfs
from app.core.pdf_validator import DestinationError
from tests.conftest import make_pdf, page_texts


def items(pdfs, *keys):
    return [inspect_pdf(pdfs[k]) for k in keys]


def test_a01_orden_manual(pdfs, tmp_path):  # A01, A10
    out = tmp_path / "salida ñ.pdf"
    n = merge_pdfs(items(pdfs, "a", "b", "c"), out)
    assert n == 6
    assert page_texts(out) == ["A1", "A2", "B1", "C1", "C2", "C3"]


def test_a02_cambio_orden(pdfs, tmp_path):
    out = tmp_path / "o.pdf"
    merge_pdfs(items(pdfs, "c", "a", "b"), out)
    assert page_texts(out)[0] == "C1"


def test_a03_mismo_nombre_distintas_carpetas(tmp_path):
    (tmp_path / "x").mkdir(); (tmp_path / "y").mkdir()
    p1 = make_pdf(tmp_path / "x" / "doc.pdf", ["X"])
    p2 = make_pdf(tmp_path / "y" / "doc.pdf", ["Y"])
    out = tmp_path / "o.pdf"
    merge_pdfs([inspect_pdf(p1), inspect_pdf(p2)], out)
    assert page_texts(out) == ["X", "Y"]


def test_a13_mismo_archivo_dos_veces(pdfs, tmp_path):
    out = tmp_path / "o.pdf"
    merge_pdfs(items(pdfs, "b", "b"), out)
    assert page_texts(out) == ["B1", "B1"]


def test_a07_destino_igual_original(pdfs):
    with pytest.raises(DestinationError):
        merge_pdfs(items(pdfs, "a", "b"), pdfs["a"])


def test_a14_cancelar_no_deja_archivos(pdfs, tmp_path):
    out = tmp_path / "o.pdf"
    with pytest.raises(MergeCancelled):
        merge_pdfs(items(pdfs, "a", "b"), out, is_cancelled=lambda: True)
    assert list(tmp_path.glob("o.pdf")) == [] and list(tmp_path.glob(".pdffacil_*")) == []


def test_cancelar_conserva_salida_previa(pdfs, tmp_path):
    out = tmp_path / "o.pdf"
    out.write_bytes(b"previo")
    calls = {"n": 0}

    def cancel():
        calls["n"] += 1
        return calls["n"] > 2

    with pytest.raises(MergeCancelled):
        merge_pdfs(items(pdfs, "a", "b", "c"), out, is_cancelled=cancel)
    assert out.read_bytes() == b"previo"
    assert list(tmp_path.glob(".pdffacil_*")) == []


def test_a09_fallo_conserva_original_y_previo(pdfs, tmp_path):
    out = tmp_path / "o.pdf"
    out.write_bytes(b"previo")
    its = items(pdfs, "a", "b")
    pdfs["b"].write_bytes(b"corrupto")
    with pytest.raises(MergeError):
        merge_pdfs(its, out)
    assert out.read_bytes() == b"previo"
    assert list(tmp_path.glob(".pdffacil_*")) == []


def test_originales_intactos(pdfs, tmp_path):
    antes = {k: v.read_bytes() for k, v in pdfs.items()}
    merge_pdfs(items(pdfs, "a", "b", "c"), tmp_path / "o.pdf")
    assert antes == {k: v.read_bytes() for k, v in pdfs.items()}


def test_progreso(pdfs, tmp_path):
    seen = []
    merge_pdfs(items(pdfs, "a", "b"), tmp_path / "o.pdf", progress=lambda n, t, nm: seen.append((n, t)))
    assert seen == [(1, 2), (2, 2)]


def test_a06_con_contrasena(tmp_path):
    p = make_pdf(tmp_path / "s.pdf", ["S1"], password="clave")
    q = make_pdf(tmp_path / "q.pdf", ["Q1"])
    it = inspect_pdf(p, "clave")
    assert it.is_encrypted and it.password == "clave"
    out = tmp_path / "o.pdf"
    merge_pdfs([it, inspect_pdf(q)], out)
    assert page_texts(out) == ["S1", "Q1"]
