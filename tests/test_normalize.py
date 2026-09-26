from dataclasses import dataclass

from examples.laya_find_lib.normalize import canonical_destination, dedupe_by_destination


def test_strips_uuid_and_tracking_query():
    a = canonical_destination(
        "https://accounts.eduzz.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/login?redirectTo=x&logo=y"
    )
    b = canonical_destination(
        "https://accounts.eduzz.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/login?foo=1"
    )
    assert a == b == "https://accounts.eduzz.com/login"


@dataclass
class Candidate:
    key: str
    summary: str
    selector: str = ""
    href: str = ""
    kind: str = "link"


def test_dedupe_by_destination_keeps_richest_text_and_raw_href():
    short = Candidate(
        "a",
        "dom_1: kind=link, text=Login, href=https://x.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/signup?a=1",
        selector="#a",
        href="https://x.com/53124931-1a7a-424b-aca7-a2eb91fd5b20/signup?a=1",
        kind="link",
    )
    rich = Candidate(
        "b",
        "dom_2: kind=link, text=Cadastrar agora no site, href=https://x.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/signup?b=2",
        selector="#b",
        href="https://x.com/aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee/signup?b=2",
        kind="link",
    )
    other_kind = Candidate(
        "c",
        "dom_3: kind=button, text=Cadastrar agora no site, href=https://x.com/other-uuid/signup",
        selector="#c",
        kind="button",
    )

    out = dedupe_by_destination([short, rich, other_kind])
    assert len(out) == 2
    kept = next(c for c in out if c.kind == "link")
    assert "Cadastrar agora no site" in kept.summary
    assert kept.href.startswith("https://x.com/")


def test_dedupe_skips_candidates_without_canonical_destination():
    a = Candidate("a", "dom_1: kind=button, text=Entrar", selector="#a", kind="button")
    b = Candidate("b", "dom_2: kind=button, text=Salvar", selector="#b", kind="button")
    assert dedupe_by_destination([a, b]) == [a, b]
