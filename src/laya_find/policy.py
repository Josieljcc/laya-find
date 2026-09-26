"""Candidate filtering and ranking policies for ``laya_find``."""

from __future__ import annotations

import re
from typing import Literal, Protocol, TypeVar

Policy = Literal["none", "light", "strict"]


class CandidateLike(Protocol):
    kind: str
    summary: str
    selector: str
    href: str


CandidateT = TypeVar("CandidateT", bound=CandidateLike)

_STOPWORDS = {
    "botão",
    "botao",
    "button",
    "campo",
    "de",
    "da",
    "do",
    "dos",
    "das",
    "o",
    "a",
    "os",
    "as",
    "um",
    "uma",
    "the",
    "for",
    "to",
    "and",
    "or",
    "no",
    "na",
    "em",
    "com",
    "por",
    "que",
    "link",
    "input",
}


def intent_tokens(intent: str) -> list[str]:
    """Return meaningful intent tokens used for candidate overlap."""
    raw = re.findall(r"[a-zA-ZÀ-ÿ0-9]+", intent.lower())
    return [token for token in raw if len(token) >= 3 and token not in _STOPWORDS]


def _text_overlap_score(summary: str, tokens: list[str]) -> int:
    summary = summary.lower()
    return sum(1 for token in tokens if token in summary)


def _dedupe(cands: list[CandidateT]) -> list[CandidateT]:
    seen: set[str] = set()
    unique: list[CandidateT] = []
    for candidate in cands:
        key = (
            candidate.selector
            or f"{candidate.kind}|{candidate.href}|{candidate.summary}"
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)
    return unique


def soft_rank(cands: list[CandidateT], intent: str) -> list[CandidateT]:
    """Stable-sort likely matches first without removing candidates."""
    intent_l = intent.lower()
    tokens = intent_tokens(intent)
    boost_terms: list[str] = []
    if any(word in intent_l for word in ("senha", "password", "passwd")):
        boost_terms += [
            "type=password",
            "password",
            "senha",
            "autocomplete=current-password",
        ]
    if any(
        word in intent_l
        for word in ("email", "e-mail", "usuário", "usuario", "login", "user")
    ):
        boost_terms += [
            "type=email",
            "email",
            "login",
            "user",
            "autocomplete=username",
        ]
    if any(
        word in intent_l
        for word in (
            "entrar",
            "submit",
            "enviar",
            "salvar",
            "save",
            "login",
            "acessar",
            "cadastrar",
            "cadastro",
            "signup",
            "sign-up",
            "register",
            "inscrev",
        )
    ):
        boost_terms += [
            "type=submit",
            "entrar",
            "salvar",
            "enviar",
            "login",
            "acessar",
            "cadastrar",
            "cadastro",
            "signup",
            "sign-up",
            "register",
            "href=",
        ]

    def score(candidate: CandidateT) -> tuple[int, int, int, int, int]:
        summary = candidate.summary.lower()
        hits = sum(1 for term in boost_terms if term in summary)
        overlap = _text_overlap_score(summary, tokens)
        phrase = " ".join(tokens)
        phrase_hit = int(bool(phrase and phrase in summary))
        tag_penalty = 0
        if "kind=link" in summary and hits == 0 and overlap == 0:
            tag_penalty = 2
        if "tag=summary" in summary:
            tag_penalty += 5
        return (
            -phrase_hit,
            -overlap,
            -hits,
            tag_penalty,
            0 if "id=" in summary else 1,
        )

    return sorted(cands, key=score)


def narrow_by_intent(cands: list[CandidateT], intent: str) -> list[CandidateT]:
    """Hard-narrow when the intent has a confidently matching candidate."""
    intent_l = intent.lower()
    tokens = intent_tokens(intent)

    if any(word in intent_l for word in ("senha", "password", "passwd")):
        password = [
            candidate
            for candidate in cands
            if "type=password" in candidate.summary.lower()
        ]
        if password:
            return password
    if any(word in intent_l for word in ("email", "e-mail")) and not any(
        word in intent_l for word in ("senha", "password")
    ):
        email = [
            candidate
            for candidate in cands
            if any(
                marker in candidate.summary.lower()
                for marker in ("type=email", "email", "e-mail")
            )
        ]
        if email:
            return email

    if tokens:
        scored = [
            (_text_overlap_score(candidate.summary, tokens), candidate)
            for candidate in cands
        ]
        best = max((score for score, _ in scored), default=0)
        if best > 0:
            need = best if best >= 2 or len(tokens) == 1 else max(1, best)
            matched = [candidate for score, candidate in scored if score >= need]
            phrase = " ".join(tokens)
            phrase_hits = [
                candidate
                for candidate in cands
                if phrase in candidate.summary.lower()
            ]
            if phrase_hits:
                return phrase_hits
            if matched:
                return matched

    if any(
        word in intent_l for word in ("login", "entrar", "acessar", "sign in")
    ) and not any(
        word in intent_l for word in ("cadastr", "signup", "register")
    ):
        login = [
            candidate
            for candidate in cands
            if any(
                marker in candidate.summary.lower()
                for marker in (
                    "login",
                    "entrar",
                    "acessar",
                    "sign in",
                    "type=submit",
                    "/login",
                    "signin",
                    "sign-in",
                )
            )
        ]
        if login:
            return login
    if any(
        word in intent_l for word in ("entrar", "submit", "enviar")
    ) and any(
        word in intent_l for word in ("botão", "botao", "button", "entrar")
    ):
        submit = [
            candidate
            for candidate in cands
            if any(
                marker in candidate.summary.lower()
                for marker in ("type=submit", "entrar", "enviar", "login")
            )
        ]
        if submit:
            return submit
    return cands


def apply_policy(
    cands: list[CandidateT], intent: str, policy: Policy
) -> list[CandidateT]:
    """Dedupe candidates, then apply the selected ranking/filtering policy."""
    unique = _dedupe(cands)
    if policy == "none":
        return unique
    if policy == "light":
        return soft_rank(unique, intent)
    if policy == "strict":
        return soft_rank(narrow_by_intent(unique, intent), intent)
    raise ValueError(f"unknown policy: {policy}")
