from app.core.pdf_inspector import inspect_pdf
from app.ui.pdf_list_model import PdfListModel


def build(pdfs, keys="abc"):
    m = PdfListModel()
    m.add_items([inspect_pdf(pdfs[k]) for k in keys])
    return m


def names(m):
    return [i.path.stem for i in m.items]


def test_mover_al_inicio(pdfs):
    m = build(pdfs)
    new = m.move_rows([2], 0)
    assert names(m) == ["Anexos", "Solicitud ñandú", "Identidad"] and new == [0]


def test_mover_al_final_y_multiple(pdfs):
    m = build(pdfs)
    new = m.move_rows([0, 1], 3)
    assert names(m) == ["Anexos", "Solicitud ñandú", "Identidad"] and new == [1, 2]


def test_subir_bajar(pdfs):
    m = build(pdfs)
    assert m.move_down([0]) == [1]
    assert names(m)[1] == "Solicitud ñandú"
    assert m.move_up([1]) == [0]
    assert m.move_up([0]) == [0]
    assert m.move_down([2]) == [2]


def test_quitar_y_totales(pdfs):
    m = build(pdfs)
    assert m.total_pages() == 6
    m.remove_rows([0, 2])
    assert names(m) == ["Identidad"] and m.total_pages() == 1


def test_duplicado_permitido(pdfs):
    m = build(pdfs, "bb")
    assert m.rowCount() == 2 and m.items[0].id != m.items[1].id
