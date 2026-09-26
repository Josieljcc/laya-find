import json
import urllib.error

from laya_find.find import FindOptions, cache_lookup_allowed, run, settle_page


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


def test_reveal_default_false_and_settle_never_clicks():
    opts = FindOptions(
        url="https://example.com",
        intent="x",
        mode="dom",
        reveal=False,
    )
    page = SettlePage()

    settle_page(page, 300, "input", reveal=opts.reveal)

    assert opts.reveal is False
    assert page.password_queries == 0
    assert page.clicks == 0


def test_dom_cache_lookup_is_disabled_for_network_discovery():
    assert cache_lookup_allowed("dom", "input") is True
    assert cache_lookup_allowed("both", "link") is True
    assert cache_lookup_allowed("network", "input") is False
    assert cache_lookup_allowed("both", "network") is False
    assert cache_lookup_allowed("dom", "network") is False


def test_json_runtime_failure_emits_one_object_and_nonzero(monkeypatch, capsys):
    def fail(_options):
        raise RuntimeError("navigation exploded")

    monkeypatch.setattr("laya_find.find._run_impl", fail)

    exit_code = run(
        FindOptions(
            url="https://example.com",
            mode="dom",
            intent="login",
            json_stdout=True,
        )
    )

    captured = capsys.readouterr()
    lines = captured.out.splitlines()
    assert exit_code != 0
    assert len(lines) == 1
    result = json.loads(lines[0])
    assert result["ok"] is False
    assert result["text"] == "navigation exploded"


def test_unreachable_serve_is_configuration_error(monkeypatch, capsys):
    def offline(_serve):
        raise urllib.error.URLError("connection refused")

    monkeypatch.setattr("laya_find.find.check_serve", offline)

    exit_code = run(
        FindOptions(
            url="https://example.com",
            mode="dom",
            intent="login",
            json_stdout=True,
        )
    )

    captured = capsys.readouterr()
    assert exit_code == 2
    assert len(captured.out.splitlines()) == 1
    assert json.loads(captured.out)["ok"] is False
