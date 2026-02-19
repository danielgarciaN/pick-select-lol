from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

CACHE_PATH = Path("data/http_cache.json")


class TTLCache:
    def __init__(self, path: Path = CACHE_PATH) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}", encoding="utf-8")

    def _load(self) -> dict[str, dict[str, Any]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _save(self, data: dict[str, dict[str, Any]]) -> None:
        self.path.write_text(json.dumps(data), encoding="utf-8")

    @staticmethod
    def make_key(prefix: str, payload: dict[str, Any]) -> str:
        raw = f"{prefix}:{json.dumps(payload, sort_keys=True)}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, key: str, ttl_seconds: int) -> Any | None:
        data = self._load()
        item = data.get(key)
        if not item:
            return None
        if time.time() - item["ts"] > ttl_seconds:
            return None
        return item["value"]

    def set(self, key: str, value: Any) -> None:
        data = self._load()
        data[key] = {"ts": time.time(), "value": value}
        self._save(data)
