from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Callable

from core import ddragon
from core.db import get_conn, get_state, set_state
from core.riot_client import RiotClient, RiotConfig

LogFn = Callable[[str], None]


def _today_key(prefix: str, suffix: str = "") -> str:
    date = datetime.now(timezone.utc).date().isoformat()
    return f"{prefix}:{suffix}:{date}" if suffix else f"{prefix}:{date}"


def sync_ddragon(log: LogFn) -> str:
    log("Consultando versión más reciente de Data Dragon...")
    version = ddragon.get_latest_version()
    set_state("latest_version", version)
    payload = ddragon.get_champion_full(version)
    champs = ddragon.parse_champions(payload, version)
    with get_conn() as conn:
        for c in champs:
            conn.execute(
                """
                INSERT INTO champions(id, name, key_str, tags_json, icon_url)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                  name=excluded.name, key_str=excluded.key_str,
                  tags_json=excluded.tags_json, icon_url=excluded.icon_url
                """,
                (c.id, c.name, c.key_str, json.dumps(c.tags), c.icon_url),
            )
    log(f"Campeones actualizados: {len(champs)}")
    return version


def sync_player_and_matches(game_name: str, tag_line: str, region: str, match_count: int, log: LogFn) -> None:
    client = RiotClient(
        RiotConfig(
            api_key=os.getenv("RIOT_API_KEY", ""),
            platform_region=region,
            regional_routing=os.getenv("RIOT_ROUTING", "europe"),
        )
    )
    account = client.get_account_by_riot_id(game_name, tag_line)
    puuid = account["puuid"]

    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO player(puuid, game_name, tag_line, region, last_sync)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(puuid) DO UPDATE SET
              game_name=excluded.game_name, tag_line=excluded.tag_line,
              region=excluded.region, last_sync=CURRENT_TIMESTAMP
            """,
            (puuid, game_name, tag_line, region),
        )

    log(f"Jugador resuelto, puuid={puuid[:8]}...")
    mastery = client.get_mastery_by_puuid(puuid)
    with get_conn() as conn:
        for m in mastery:
            conn.execute(
                """
                INSERT INTO mastery(puuid, champion_id, points, level, last_play_time)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(puuid, champion_id) DO UPDATE SET
                  points=excluded.points, level=excluded.level,
                  last_play_time=excluded.last_play_time
                """,
                (puuid, m["championId"], m["championPoints"], m["championLevel"], m.get("lastPlayTime")),
            )
    log(f"Mastery sync completado: {len(mastery)} campeones")

    day_cache = _today_key("match_ids", puuid)
    cached = get_state(day_cache)
    if cached:
        match_ids = json.loads(cached)
        log(f"Usando caché diaria de match_ids ({len(match_ids)})")
    else:
        match_ids = client.get_match_ids(puuid, count=match_count)
        set_state(day_cache, json.dumps(match_ids))
        log(f"Match ids descargados: {len(match_ids)}")

    inserted, skipped = 0, 0
    with get_conn() as conn:
        existing = {r["match_id"] for r in conn.execute("SELECT match_id FROM matches").fetchall()}

    for mid in match_ids:
        if mid in existing:
            skipped += 1
            continue
        info = client.get_match(mid)["info"]
        with get_conn() as conn:
            conn.execute(
                "INSERT OR IGNORE INTO matches(match_id, patch, queue_id, game_creation, duration) VALUES (?, ?, ?, ?, ?)",
                (
                    mid,
                    ".".join(info.get("gameVersion", "").split(".")[:2]) if info.get("gameVersion") else None,
                    info.get("queueId"),
                    info.get("gameCreation"),
                    info.get("gameDuration"),
                ),
            )
            for p in info.get("participants", []):
                if p.get("puuid") == puuid:
                    cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO my_participation(match_id, puuid, champion_id, role, lane, win, kills, deaths, assists, cs)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (mid, puuid, p.get("championId"), p.get("teamPosition"), p.get("lane"), int(bool(p.get("win"))), p.get("kills", 0), p.get("deaths", 0), p.get("assists", 0), cs),
                    )
        inserted += 1
    log(f"Partidas nuevas insertadas: {inserted}, omitidas por duplicado: {skipped}")
