import json
from pathlib import Path

from examples import laya_find
from laya_find.cache import CacheStore, cache_key


class FakePage:
    def __init__(self, matches):
        self.matches = matches
        self.frames = []
        self.main_frame = None

    def evaluate(self, _script, _selector):
        return self.matches


def test_same_host_login_paths_share_cache_key():
    root = cache_key("https://www.eduzz.com/", "botão de login")
    pricing = cache_key("https://www.eduzz.com/pricing", "  Botão   de LOGIN ")

    assert root == pricing


def test_cache_key_separates_hosts_and_intents():
    login = cache_key("https://www.eduzz.com/", "login")

    assert login != cache_key("https://accounts.eduzz.com/", "login")
    assert login != cache_key("https://www.eduzz.com/", "cadastro")


def test_store_round_trip_and_invalidate(tmp_path):
    path = tmp_path / "selector-cache.json"
    key = cache_key("https://example.com/a", "login")
    record = {
        "selector": 'a[href*="login"]',
        "kind": "link",
        "href_hint": "/login",
        "updated_at": "2026-09-26T12:00:00+00:00",
        "hits": 0,
        "last_ok": True,
    }

    store = CacheStore.load(path)
    store.put(key, record)
    store.save()

    loaded = CacheStore.load(path)
    assert loaded.get(key) == record
    assert loaded.invalidate(key) is True
    assert loaded.get(key) is None
    loaded.save()
    assert CacheStore.load(path).get(key) is None


def test_load_missing_or_invalid_cache_starts_empty(tmp_path):
    missing = tmp_path / "missing.json"
    assert CacheStore.load(missing).get("anything") is None

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{not json", encoding="utf-8")
    assert CacheStore.load(invalid).get("anything") is None


def test_save_creates_parent_and_valid_json(tmp_path):
    path = tmp_path / "nested" / "cache.json"
    store = CacheStore.load(path)
    store.put("example.com::login", {"selector": "#login"})

    store.save()

    assert json.loads(path.read_text(encoding="utf-8")) == {
        "example.com::login": {"selector": "#login"}
    }


def test_cache_cli_flags_default_on_and_can_be_disabled(tmp_path):
    defaults = laya_find.parse_args([])
    disabled = laya_find.parse_args(["--no-cache"])
    custom = laya_find.parse_args(["--cache-path", str(tmp_path / "custom.json")])

    assert defaults.use_cache is True
    assert Path(defaults.cache_path).parts[-2:] == ("examples", "selector_cache.json")
    assert disabled.use_cache is False
    assert custom.cache_path == str(tmp_path / "custom.json")


def test_verified_hit_increments_hits_and_stale_hit_is_invalidated(tmp_path):
    path = tmp_path / "cache.json"
    store = CacheStore.load(path)
    store.put("valid", {"selector": "#login", "hits": 2, "last_ok": True})
    store.put("stale", {"selector": "#missing", "hits": 0, "last_ok": True})

    record, matches = laya_find.resolve_cache_hit(store, "valid", FakePage(1))

    assert matches == 1
    assert record["hits"] == 3
    assert laya_find.resolve_cache_hit(store, "stale", FakePage(0)) is None
    reloaded = CacheStore.load(path)
    assert reloaded.get("valid")["hits"] == 3
    assert reloaded.get("stale") is None


def test_only_verified_stable_candidate_is_cached(tmp_path):
    store = CacheStore.load(tmp_path / "cache.json")
    stable = laya_find.Candidate(
        key="dom_1",
        source="dom",
        kind="link",
        summary="href=/login",
        selector='a[href*="login"]',
        href="/login",
    )
    volatile = laya_find.Candidate(
        key="dom_2",
        source="dom",
        kind="link",
        summary="",
        selector='a[href="https://example.com/login?token=abc"]',
    )

    assert laya_find.save_cache_candidate(store, "stable", stable, True, 1) is True
    assert laya_find.save_cache_candidate(store, "volatile", volatile, True, 1) is False
    assert CacheStore.load(store.path).get("stable")["selector"] == 'a[href*="login"]'
    assert CacheStore.load(store.path).get("volatile") is None
