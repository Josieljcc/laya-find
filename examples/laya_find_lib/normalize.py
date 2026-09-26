"""Canonical link destinations and dedupe of same-target candidates."""

from __future__ import annotations

import re
from dataclasses import replace
from typing import Protocol, TypeVar
from urllib.parse import urlparse, urlunparse

from examples.laya_find_lib.contract import summary_field

_UUID_SEGMENT = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.I,
)


class CandidateLike(Protocol):
    kind: str
    summary: str
    href: str


CandidateT = TypeVar("CandidateT", bound=CandidateLike)


def _is_uuid_path_segment(segment: str) -> bool:
    if _UUID_SEGMENT.match(segment):
        return True
    return len(segment) >= 20 and bool(re.fullmatch(r"[0-9a-f-]+", segment, re.I))


def canonical_destination(href: str) -> str:
    """Strip UUID path segments and tracking query; absolute http(s) URLs only."""
    href = (href or "").strip()
    if not href:
        return ""
    parsed = urlparse(href)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""
    segments = [
        seg
        for seg in parsed.path.split("/")
        if seg and not _is_uuid_path_segment(seg)
    ]
    path = "/" + "/".join(segments) if segments else ""
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _candidate_href(candidate: CandidateT) -> str:
    return candidate.href or summary_field(candidate.summary, "href")


def _text_richness(candidate: CandidateT) -> int:
    return len(summary_field(candidate.summary, "text"))


def _with_observed_href(candidate: CandidateT, raw_href: str) -> CandidateT:
    if not raw_href or candidate.href:
        return candidate
    return replace(candidate, href=raw_href)  # type: ignore[type-var]


def dedupe_by_destination(cands: list[CandidateT]) -> list[CandidateT]:
    """One candidate per (kind, canonical destination); keep richest link text."""
    winners: dict[tuple[str, str], CandidateT] = {}

    for candidate in cands:
        raw_href = _candidate_href(candidate)
        canon = canonical_destination(raw_href)
        if not canon:
            continue
        key = (candidate.kind, canon)
        if key not in winners:
            winners[key] = _with_observed_href(candidate, raw_href)
            continue
        current = winners[key]
        raw = raw_href or _candidate_href(current)
        if _text_richness(candidate) > _text_richness(current):
            winners[key] = _with_observed_href(candidate, raw)
        else:
            winners[key] = _with_observed_href(current, raw)

    emitted: set[tuple[str, str]] = set()
    out: list[CandidateT] = []
    for candidate in cands:
        raw_href = _candidate_href(candidate)
        canon = canonical_destination(raw_href)
        if not canon:
            out.append(candidate)
            continue
        key = (candidate.kind, canon)
        if key in emitted:
            continue
        emitted.add(key)
        out.append(winners[key])
    return out
