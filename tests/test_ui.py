from pathlib import Path

from PySide6.QtWidgets import QMessageBox

from app.ui.main_window import MainWindow


def test_agregar_y_contador(qtbot, pdfs, monkeypatch):
    w = MainWindow()
    qtbot.addWidget(w)
    w.add_paths([pdfs["a"], pdfs["b"]])
    assert w.model.rowCount() == 2
    assert w.count_label.text() == "2 archivos · 3 páginas"


def test_corrupto_no_bloquea_resto(qtbot, pdfs, tmp_path, monkeypatch):
    bad = tmp_path / "malo.pdf"; bad.write_bytes(b"xx")
    monkeypatch.setattr(QMessageBox, "warning", lambda *a, **k: QMessageBox.Ok)
    w = MainWindow(); qtbot.addWidget(w)
    w.add_paths([bad, pdfs["a"]])
    assert [i.path.name for i in w.model.items] == [pdfs["a"].name]


def test_duplicado_pregunta(qtbot, pdfs, monkeypatch):
    w = MainWindow(); qtbot.addWidget(w)
    w.add_paths([pdfs["b"]])
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.Yes)
    w.add_paths([pdfs["b"]])
    assert w.model.rowCount() == 2
    monkeypatch.setattr(QMessageBox, "question", lambda *a, **k: QMessageBox.No)
    w.add_paths([pdfs["b"]])
    assert w.model.rowCount() == 2


def test_botones_reordenan(qtbot, pdfs):
    w = MainWindow(); qtbot.addWidget(w)
    w.add_paths([pdfs["a"], pdfs["b"], pdfs["c"]])
    w.table.select_rows([2])
    w.on_up()
    assert [i.path.stem for i in w.model.items] == ["Solicitud ñandú", "Anexos", "Identidad"]
    w.table.select_rows([1])
    w.on_remove()
    assert w.model.rowCount() == 2


def test_merge_en_hilo(qtbot, pdfs, tmp_path):
    from app.services.merge_worker import MergeWorker
    from app.core.pdf_inspector import inspect_pdf
    out = tmp_path / "o.pdf"
    wk = MergeWorker([inspect_pdf(pdfs["a"]), inspect_pdf(pdfs["b"])], out)
    with qtbot.waitSignal(wk.succeeded, timeout=10000) as sig:
        wk.start()
    assert sig.args == [str(out), 3]
    wk.wait()
