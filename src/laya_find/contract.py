"""JSON result contract for external scrapers (stdout) vs human logs (stderr)."""

from __future__ import annotations

import json
import re
from typing import Any

_SUMMARY_FIELD_RE = re.compile(r"\b(text|href)=([^,]+)")


def summary_field(summary: str, field: str) -> str:
    """Parse `text=` / `href=` snippets from candidate summary lines."""
    for m in _SUMMARY_FIELD_RE.finditer(summary):
        if m.group(1) == field:
            return m.group(2).strip()
    return ""


def build_result(
    *,
    url: str,
    final_url: str,
    intent: str,
    kind: str,
    selector: str = "",
    selector_ok: bool = False,
    matches: int = 0,
    href: str = "",
    text: str = "",
    confidence: float | None = None,
    confirm_noul: float | None = None,
    policy: str = "light",
    cached: bool = False,
    ok: bool = True,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "url": url,
        "final_url": final_url,
        "intent": intent,
        "kind": kind,
        "selector": selector,
        "selector_ok": selector_ok,
        "matches": matches,
        "href": href,
        "text": text,
        "confidence": confidence,
        "confirm_noul": confirm_noul,
        "policy": policy,
        "cached": cached,
    }


def emit_json_line(result: dict[str, Any]) -> str:
    """One JSON object, no embedded newlines (for piping to ConvertFrom-Json)."""
    return json.dumps(result, ensure_ascii=False, separators=(",", ":"))
