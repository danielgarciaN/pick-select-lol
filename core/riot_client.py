from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

import requests

from core.utils_cache import TTLCache


class RiotApiError(RuntimeError):
    pass


@dataclass
class RiotConfig:
    api_key: str
    platform_region: str
    regional_routing: str


class RiotClient:
    def __init__(self, config: RiotConfig | None = None) -> None:
        self.config = config or RiotConfig(
            api_key=os.getenv("RIOT_API_KEY", ""),
            platform_region=os.getenv("RIOT_REGION", "euw1"),
            regional_routing=os.getenv("RIOT_ROUTING", "europe"),
        )
        self.cache = TTLCache()
        self.session = requests.Session()

    def _request(self, url: str, params: dict[str, Any] | None = None, ttl: int = 3600) -> Any:
        if not self.config.api_key:
            raise RiotApiError("RIOT_API_KEY no configurada")
        params = params or {}
        key = self.cache.make_key(url, params)
        cached = self.cache.get(key, ttl)
        if cached is not None:
            return cached

        headers = {"X-Riot-Token": self.config.api_key}
        for attempt in range(5):
            resp = self.session.get(url, headers=headers, params=params, timeout=20)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After", "1")) + attempt
                time.sleep(wait)
                continue
            if resp.status_code in (401, 403):
                raise RiotApiError(f"API key inválida o sin permisos: {resp.status_code}")
            if resp.status_code >= 400:
                raise RiotApiError(f"Error Riot API {resp.status_code}: {resp.text}")
            payload = resp.json()
            self.cache.set(key, payload)
            return payload
        raise RiotApiError("Rate limit persistente tras reintentos")

    def get_account_by_riot_id(self, game_name: str, tag_line: str) -> dict[str, Any]:
        url = (
            f"https://{self.config.regional_routing}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/"
            f"{game_name}/{tag_line}"
        )
        return self._request(url, ttl=86400)

    def get_summoner_by_puuid(self, puuid: str) -> dict[str, Any]:
        url = f"https://{self.config.platform_region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
        return self._request(url, ttl=86400)

    def get_mastery_by_puuid(self, puuid: str) -> list[dict[str, Any]]:
        url = (
            f"https://{self.config.platform_region}.api.riotgames.com/lol/champion-mastery/v4/champion-masteries/by-puuid/"
            f"{puuid}"
        )
        return self._request(url, ttl=21600)

    def get_match_ids(self, puuid: str, count: int = 200, start: int = 0) -> list[str]:
        url = f"https://{self.config.regional_routing}.api.riotgames.com/lol/match/v5/matches/by-puuid/{puuid}/ids"
        return self._request(url, params={"count": count, "start": start}, ttl=21600)

    def get_match(self, match_id: str) -> dict[str, Any]:
        url = f"https://{self.config.regional_routing}.api.riotgames.com/lol/match/v5/matches/{match_id}"
        return self._request(url, ttl=86400)
