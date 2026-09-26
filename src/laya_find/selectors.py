"""Stable href selector helpers shared by laya_find CLIs."""

from __future__ import annotations

import re
from urllib.parse import urlparse

_HREF_KEYWORDS = (
    "login",
    "signin",
    "sign-in",
    "signup",
    "sign-up",
    "cadastro",
    "register",
    "auth",
)

_PATH_KW = ("login", "signup", "signin", "auth", "cadastro")

_UUID_RE = re.compile(
    r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}",
    re.I,
)


def is_volatile_href(href: str) -> bool:
    """True when href embeds session-specific ids or heavy redirect query strings."""
    if not href:
        return False
    if _UUID_RE.search(href):
        return True
    try:
        parsed = urlparse(href)
        q = parsed.query.lower()
        if not q:
            return False
        if "redirect" in q:
            return True
        if len(parsed.query) > 40:
            return True
    except Exception:
        pass
    return False


def is_volatile_selector(sel: str) -> bool:
    if not sel:
        return True
    if sel.startswith("text="):
        return True
    if 'href="http' in sel or "href='http" in sel:
        return True
    if len(sel) > 80 and "[href=" in sel and "[href*=" not in sel:
        return True
    return False


def stable_href_candidates(href: str) -> list[str]:
    """Prefer short contains-selectors over full volatile URLs."""
    low = href.lower()
    out: list[str] = []
    for kw in _HREF_KEYWORDS:
        if kw in low:
            out.append(f'a[href*="{kw}"]')
    try:
        parsed = urlparse(href)
        if parsed.hostname:
            out.append(f'a[href*="{parsed.hostname}"]')
        for seg in parsed.path.split("/"):
            if 3 <= len(seg) <= 40 and not re.fullmatch(r"[0-9a-f-]{20,}", seg, re.I):
                if any(k in seg.lower() for k in _PATH_KW):
                    out.append(f'a[href*="{seg}"]')
    except Exception:
        pass
    out.append(f'a[href="{href}"]')  # last resort
    seen: set[str] = set()
    uniq: list[str] = []
    for s in out:
        if s not in seen:
            seen.add(s)
            uniq.append(s)
    return uniq


def score_selector_stability(sel: str) -> int:
    """Higher score means more stable / preferable selector."""
    if not sel:
        return 0
    score = 100 - min(len(sel) // 2, 80)
    if "[href*=" in sel:
        score += 25
    if is_volatile_selector(sel):
        score -= 100
    return score
