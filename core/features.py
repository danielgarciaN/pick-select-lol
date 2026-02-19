from __future__ import annotations

import math
import time
from dataclasses import dataclass

from core.db import get_conn


@dataclass
class PersonalScore:
    score: float
    reasons: list[str]


def score_personal(champion_id: int, role: str | None, puuid: str | None) -> PersonalScore:
    if not puuid:
        return PersonalScore(0.0, ["Sin jugador sincronizado"])

    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM my_participation WHERE puuid=? AND champion_id=?",
            (puuid, champion_id),
        ).fetchall()
        mastery = conn.execute(
            "SELECT points, last_play_time FROM mastery WHERE puuid=? AND champion_id=?",
            (puuid, champion_id),
        ).fetchone()

    games = len(rows)
    wins = sum(r["win"] for r in rows)
    kills = sum(r["kills"] for r in rows)
    deaths = sum(r["deaths"] for r in rows)
    assists = sum(r["assists"] for r in rows)

    prior_games = 12
    prior_wr = 0.5
    wr = (wins + prior_games * prior_wr) / (games + prior_games)
    wr_score = (wr - 0.5) * 10

    kda = (kills + assists) / max(1, deaths)
    kda_score = min(2.0, (kda - 2.0) * 0.7)

    mastery_score = 0.0
    recency_penalty = 0.0
    reasons: list[str] = []

    if mastery:
        points = mastery["points"]
        mastery_score = min(2.5, math.log10(points + 1))
        reasons.append(f"+{mastery_score:.1f} por mastery")

        last_play = mastery["last_play_time"]
        if last_play:
            days = (time.time() * 1000 - last_play) / (1000 * 3600 * 24)
            if days > 30:
                recency_penalty = min(2.5, (days - 30) / 20)
                reasons.append(f"-{recency_penalty:.1f} por no jugarlo en {int(days)} días")

    if games > 0:
        reasons.append(f"+{wr_score:.1f} por winrate suavizado ({games} partidas)")
        reasons.append(f"+{kda_score:.1f} por KDA proxy")

    total = wr_score + kda_score + mastery_score - recency_penalty
    if role:
        role_games = sum(1 for r in rows if (r["role"] or "").lower() == role.lower())
        if role_games > 0:
            total += 0.5
            reasons.append(f"+0.5 por experiencia en rol {role}")

    return PersonalScore(total, reasons)
