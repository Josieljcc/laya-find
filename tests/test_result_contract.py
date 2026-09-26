import json

from laya_find.contract import build_result, emit_json_line

FULL_RESULT_KEYS = {
    "ok",
    "url",
    "final_url",
    "intent",
    "kind",
    "selector",
    "selector_ok",
    "matches",
    "href",
    "text",
    "confidence",
    "confirm_noul",
    "policy",
    "cached",
}


def test_result_has_required_keys():
    r = build_result(
        url="https://x",
        final_url="https://x",
        intent="login",
        kind="button",
        selector='a[href*="login"]',
        selector_ok=True,
        matches=2,
        href="https://x/login",
        text="Login",
        confidence=0.5,
        confirm_noul=0.9,
        policy="light",
        cached=False,
    )
    assert r["ok"] is True
    assert set(r) == FULL_RESULT_KEYS


def test_emit_json_line_is_single_object():
    r = build_result(
        url="https://x",
        final_url="https://x",
        intent="login",
        kind="button",
        selector="a",
        selector_ok=True,
        matches=1,
    )
    line = emit_json_line(r)
    parsed = json.loads(line)
    assert parsed["url"] == "https://x"
    assert set(parsed) == FULL_RESULT_KEYS
    assert "\n" not in line.strip()
