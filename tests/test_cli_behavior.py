import json

from examples import laya_find


class SettlePage:
    def __init__(self):
        self.password_queries = 0
        self.clicks = 0

    def wait_for_load_state(self, *_args, **_kwargs):
        return None

    def wait_for_timeout(self, _timeout):
        return None

    def query_selector_all(self, _selector):
        self.password_queries += 1
        return []

    def locator(self, _selector):
        self.clicks += 1
        raise AssertionError("default discovery must not attempt reveal")


def test_reveal_is_opt_in_and_default_settle_never_clicks():
    defaults = laya_find.parse_args([])
    opted_in = laya_find.parse_args(["--reveal"])
    page = SettlePage()

    laya_find.settle_page(page, 300, "input", reveal=defaults.reveal)

    assert defaults.reveal is False
    assert opted_in.reveal is True
    assert page.password_queries == 0
    assert page.clicks == 0


def test_dom_cache_lookup_is_disabled_for_network_discovery():
    assert laya_find.cache_lookup_allowed("dom", "input") is True
    assert laya_find.cache_lookup_allowed("both", "link") is True
    assert laya_find.cache_lookup_allowed("network", "input") is False
    assert laya_find.cache_lookup_allowed("both", "network") is False
    assert laya_find.cache_lookup_allowed("dom", "network") is False


def test_json_runtime_failure_emits_one_object_and_nonzero(monkeypatch, capsys):
    def fail(_argv=None):
        raise RuntimeError("navigation exploded")

    monkeypatch.setattr(laya_find, "_main_impl", fail)

    exit_code = laya_find.main(
        ["--url", "https://example.com", "--mode", "dom", "--intent", "login", "--json"]
    )

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert exit_code != 0
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["ok"] is False
    assert result["text"] == "navigation exploded"
