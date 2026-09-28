from laya_find.find import FindOptions, run_on_page


class DummyPage:
    def set_default_timeout(self, _ms):
        return None


def test_run_on_page_missing_fields_exits_two():
    code = run_on_page(DummyPage(), FindOptions(json_stdout=False))
    assert code == 2


def test_run_on_page_json_missing_fields_emits_ok_false(capsys):
    code = run_on_page(
        DummyPage(),
        FindOptions(url="https://x", intent="", mode="dom", json_stdout=True),
    )
    assert code == 2
    out = capsys.readouterr().out.strip()
    assert '"ok": false' in out or '"ok":false' in out
