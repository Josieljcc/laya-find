from laya_find.login_flow import LoginWizardOptions, run_wizard


class FakePage:
    def __init__(self):
        self.gotos = []

    def set_default_timeout(self, _ms):
        return None

    def goto(self, url, wait_until="domcontentloaded"):
        self.gotos.append(url)


class FakeBrowser:
    def __init__(self, page):
        self._page = page
        self.closed = False

    def new_page(self):
        return self._page

    def close(self):
        self.closed = True


class FakeChromium:
    def __init__(self, page):
        self._page = page

    def launch(self, headless=False):
        return FakeBrowser(self._page)


class FakePlaywright:
    def __init__(self, page):
        self.chromium = FakeChromium(page)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_wizard_calls_run_on_page_same_session(monkeypatch):
    page = FakePage()
    calls = []

    def fake_run_on_page(p, opts, **_kwargs):
        calls.append((p, opts.url, opts.intent, opts.mode))
        return 0

    monkeypatch.setattr(
        "laya_find.login_flow.sync_playwright",
        lambda: FakePlaywright(page),
    )
    monkeypatch.setattr("laya_find.login_flow.run_on_page", fake_run_on_page)
    monkeypatch.setattr("sys.stdin.isatty", lambda: True)
    monkeypatch.setattr("builtins.input", lambda *_a, **_k: "")

    code = run_wizard(
        LoginWizardOptions(
            login_url="https://example.com/login",
            url="https://example.com/app",
            intent="botão exportar",
            mode="dom",
        )
    )
    assert code == 0
    assert page.gotos == ["https://example.com/login"]
    assert len(calls) == 1
    assert calls[0][0] is page
    assert calls[0][1] == "https://example.com/app"
    assert calls[0][2] == "botão exportar"
