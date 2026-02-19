from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from core.db import get_conn
from core.models import Rule


@dataclass
class DraftScore:
    score: float
    reasons: list[str]


DATA_DIR = Path("data")


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_matrices() -> tuple[dict, dict, dict]:
    synergy = _load_json(DATA_DIR / "synergy_matrix.json")
    counter = _load_json(DATA_DIR / "counter_matrix.json")
    tags = _load_json(DATA_DIR / "manual_tags.json")
    return synergy, counter, tags


def _matrix_lookup(matrix: dict, a: int, b: int) -> float:
    return float(matrix.get(str(a), {}).get(str(b), 0.0))


def score_draft(
    champion_id: int,
    ally_picks: list[int],
    enemy_picks: list[int],
    ally_bans: list[int],
    enemy_bans: list[int],
    mode: str,
) -> DraftScore:
    synergy, counter, tags_map = load_matrices()
    reasons: list[str] = []

    if champion_id in ally_picks or champion_id in enemy_picks or champion_id in ally_bans or champion_id in enemy_bans:
        return DraftScore(-999.0, ["Campeón no elegible (pick/baneo)"])

    total = 0.0
    for ally in ally_picks:
        s = _matrix_lookup(synergy, champion_id, ally)
        if s:
            reasons.append(f"{s:+.1f} por sinergia con aliado {ally}")
            total += s

    for enemy in enemy_picks:
        c = _matrix_lookup(counter, champion_id, enemy)
        if c:
            reasons.append(f"{c:+.1f} por counter a {enemy}")
            total += c

    team_tags = set()
    for ally in ally_picks:
        team_tags.update(tags_map.get(str(ally), []))

    my_tags = set(tags_map.get(str(champion_id), []))
    if "engage" not in team_tags and "engage" in my_tags:
        total += 1.5
        reasons.append("+1.5 por aportar engage faltante")
    if "frontline" not in team_tags and "frontline" in my_tags:
        total += 1.2
        reasons.append("+1.2 por aportar frontline faltante")

    if mode == "counter" and enemy_picks:
        total += 0.8
        reasons.append("+0.8 por modo counter")

    return DraftScore(total, reasons)


def apply_rules(
    champion_id: int,
    rules: list[Rule],
    ally_picks: list[int],
    enemy_picks: list[int],
    ally_bans: list[int],
    enemy_bans: list[int],
    role: str,
    mode: str,
) -> DraftScore:
    _, _, tags_map = load_matrices()
    tags = set(tags_map.get(str(champion_id), []))
    total = 0.0
    reasons: list[str] = []

    for r in rules:
        condition_ok = False
        cv = r.condition_value
        if r.condition_type == "enemy_pick":
            condition_ok = cv.isdigit() and int(cv) in enemy_picks
        elif r.condition_type == "ally_pick":
            condition_ok = cv.isdigit() and int(cv) in ally_picks
        elif r.condition_type == "role":
            condition_ok = cv.lower() == role.lower()
        elif r.condition_type == "banned":
            condition_ok = cv.isdigit() and int(cv) in (ally_bans + enemy_bans)
        elif r.condition_type == "mode":
            condition_ok = cv.lower() == mode.lower()
        elif r.condition_type == "team_need":
            condition_ok = cv.lower() in {"engage", "frontline", "ap", "ad", "peel", "waveclear"}

        if not condition_ok:
            continue

        target_ok = (r.target_type == "champion" and r.target_value.isdigit() and int(r.target_value) == champion_id) or (
            r.target_type == "tag" and r.target_value in tags
        )
        if target_ok:
            total += r.weight
            msg = r.note or "regla personalizada"
            reasons.append(f"{r.weight:+.1f} por regla: {msg}")

    return DraftScore(total, reasons)


def get_candidate_champions(role: str | None = None) -> list[int]:
    with get_conn() as conn:
        rows = conn.execute("SELECT id FROM champions ORDER BY name").fetchall()
    return [r["id"] for r in rows]
