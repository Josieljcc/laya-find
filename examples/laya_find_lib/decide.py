"""Small, stable tournament labels and intent-overlap fallback helpers."""

from __future__ import annotations

import re
from typing import Protocol, TypeVar
from urllib.parse import unquote, urlparse

from examples.laya_find_lib.contract import summary_field
from examples.laya_find_lib.policy import intent_tokens


class CandidateLike(Protocol):
    summary: str
    href: str


CandidateT = TypeVar("CandidateT", bound=CandidateLike)

_VOLATILE_SEGMENT = re.compile(
    r"^(?:\d+|[0-9a-f]{8}-[0-9a-f-]{12,}|[0-9a-f-]{20,})$", re.I
)


def _href_hint(href: str) -> str:
    parsed = urlparse((href or "").strip())
    segments = [
        unquote(segment)
        for segment in parsed.path.split("/")
        if segment and not _VOLATILE_SEGMENT.fullmatch(segment)
    ]
    return segments[-1][:48] if segments else ""


def short_label(text: str, href: str, kind: str) -> str:
    """Build a compact choice label without volatile URL query data."""
    parts = []
    clean_text = " ".join((text or "").split())
    if clean_text:
        parts.append(f'text="{clean_text[:100]}"')
    hint = _href_hint(href)
    if hint:
        parts.append(f'href*="{hint}"')
    return " | ".join(parts) or (kind or "candidate")


def candidates_overlapping_intent(
    candidates: list[CandidateT], intent: str
) -> list[CandidateT]:
    """Return candidates whose visible text or href contains an intent token."""
    tokens = intent_tokens(intent)
    if not tokens:
        return []
    matched = []
    for candidate in candidates:
        text = summary_field(candidate.summary, "text")
        href = candidate.href or summary_field(candidate.summary, "href")
        haystack = f"{text} {href}".lower()
        if any(token in haystack for token in tokens):
            matched.append(candidate)
    return matched
