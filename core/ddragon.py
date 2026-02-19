from __future__ import annotations

from typing import Any

import requests

from core.models import Champion

VERSIONS_URL = "https://ddragon.leagueoflegends.com/api/versions.json"


def get_latest_version() -> str:
    resp = requests.get(VERSIONS_URL, timeout=20)
    resp.raise_for_status()
    versions: list[str] = resp.json()
    return versions[0]


def get_champion_full(version: str) -> dict[str, Any]:
    url = f"https://ddragon.leagueoflegends.com/cdn/{version}/data/en_US/championFull.json"
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    return resp.json()


def parse_champions(payload: dict[str, Any], version: str) -> list[Champion]:
    champs = []
    for champ in payload.get("data", {}).values():
        key_str = champ["key"]
        champ_id = int(key_str)
        image_name = champ.get("image", {}).get("full")
        icon_url = f"https://ddragon.leagueoflegends.com/cdn/{version}/img/champion/{image_name}" if image_name else None
        champs.append(
            Champion(
                id=champ_id,
                name=champ["name"],
                key_str=key_str,
                tags=champ.get("tags", []),
                icon_url=icon_url,
            )
        )
    return sorted(champs, key=lambda c: c.name)
