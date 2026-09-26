"""Persistent selector cache keyed by site and normalized user intent."""

from __future__ import annotations

import json
import os
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def _normalize_intent(intent: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", intent).casefold().split())


def cache_key(url: str, intent: str) -> str:
    """Return a site-wide key so pages on the same host can share CTAs."""
    parsed = urlsplit(url)
    host = (parsed.hostname or parsed.netloc).casefold()
    port = parsed.port
    if port and not (
        (parsed.scheme.casefold() == "http" and port == 80)
        or (parsed.scheme.casefold() == "https" and port == 443)
    ):
        host = f"{host}:{port}"
    return f"{host}::{_normalize_intent(intent)}"


class CacheStore:
    """Small JSON-backed mapping for selector cache records."""

    def __init__(self, path: str | os.PathLike[str], records: dict[str, dict[str, Any]] | None = None):
        self.path = Path(path)
        self._records = records or {}

    @classmethod
    def load(cls, path: str | os.PathLike[str]) -> "CacheStore":
        cache_path = Path(path)
        try:
            raw = json.loads(cache_path.read_text(encoding="utf-8"))
            records = {
                key: value
                for key, value in raw.items()
                if isinstance(key, str) and isinstance(value, dict)
            }
        except (OSError, json.JSONDecodeError, AttributeError):
            records = {}
        return cls(cache_path, records)

    def save(self, path: str | os.PathLike[str] | None = None) -> None:
        if path is not None:
            self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f"{self.path.suffix}.tmp")
        temporary.write_text(
            json.dumps(self._records, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.path)

    def get(self, key: str) -> dict[str, Any] | None:
        return self._records.get(key)

    def put(self, key: str, record: dict[str, Any]) -> None:
        self._records[key] = record

    def invalidate(self, key: str) -> bool:
        return self._records.pop(key, None) is not None
