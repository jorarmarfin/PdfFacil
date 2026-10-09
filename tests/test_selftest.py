import json

from app.selftest import main


def test_selftest_ok(tmp_path):
    assert main([str(tmp_path)]) == 0
    result = json.loads((tmp_path / "selftest.json").read_text(encoding="utf-8"))
    assert result["ok"], result
