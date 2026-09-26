from dataclasses import dataclass

from examples.laya_find_lib.policy import apply_policy


@dataclass
class Candidate:
    key: str
    summary: str
    selector: str = ""
    href: str = ""
    kind: str = "button"


def test_apply_policy_none_dedupes_without_reordering():
    first = Candidate("first", "text=Ajuda", selector="#same")
    duplicate = Candidate("duplicate", "text=Cadastrar agora", selector="#same")
    other = Candidate("other", "text=Entrar", selector="#other")

    assert apply_policy([first, duplicate, other], "cadastrar agora", "none") == [
        first,
        other,
    ]


def test_apply_policy_light_soft_ranks_without_narrowing():
    help_link = Candidate("help", "kind=link, text=Ajuda", selector="#help")
    signup = Candidate(
        "signup", "kind=link, text=Cadastrar agora", selector="#signup"
    )

    assert apply_policy([help_link, signup], "botão cadastrar agora", "light") == [
        signup,
        help_link,
    ]


def test_apply_policy_strict_narrows_to_best_phrase_match():
    help_link = Candidate("help", "kind=link, text=Ajuda", selector="#help")
    signup = Candidate(
        "signup", "kind=link, text=Cadastrar agora", selector="#signup"
    )

    assert apply_policy([help_link, signup], "botão cadastrar agora", "strict") == [
        signup
    ]
