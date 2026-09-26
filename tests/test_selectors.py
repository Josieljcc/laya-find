from examples.laya_find_lib.selectors import (
    is_volatile_href,
    is_volatile_selector,
    stable_href_candidates,
    score_selector_stability,
)

VOLATILE = (
    "https://accounts.eduzz.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/login"
    "?isPartnerCreate=true&redirectTo=https%3A%2F%2Forbita.eduzz.com%2F"
)


def test_volatile_href_detects_uuid_and_query():
    assert is_volatile_href(VOLATILE) is True
    assert is_volatile_href("https://dashboard.kiwify.com/login?lang=pt") is False


def test_stable_candidates_prefer_contains_login():
    cands = stable_href_candidates(VOLATILE)
    assert cands[0] == 'a[href*="login"]'
    assert any('href="' in c and "http" in c for c in cands)  # full URL last
    assert cands[-1].startswith('a[href="http')


def test_stability_scores_contains_above_full_url():
    assert score_selector_stability('a[href*="login"]') > score_selector_stability(
        f'a[href="{VOLATILE}"]'
    )
    assert is_volatile_selector(f'a[href="{VOLATILE}"]') is True
    assert is_volatile_selector('a[href*="login"]') is False
