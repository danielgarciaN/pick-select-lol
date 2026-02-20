from __future__ import annotations

from core.draft_engine import apply_rules, get_candidate_champions, score_draft
from core.features import score_personal
from core.models import Rule, ScoreBreakdown

W_DRAFT = 0.62
W_PERSONAL = 0.23
W_NOTES = 0.14
W_PATCH = 0.01


def recommend(
    puuid: str | None,
    role: str,
    mode: str,
    ally_picks: list[int],
    enemy_picks: list[int],
    ally_bans: list[int],
    enemy_bans: list[int],
    rules: list[Rule],
    top_k: int = 5,
) -> list[tuple[int, ScoreBreakdown]]:
    results: list[tuple[int, ScoreBreakdown]] = []
    for champion_id in get_candidate_champions(role):
        d = score_draft(champion_id, ally_picks, enemy_picks, ally_bans, enemy_bans, mode)
        if d.score < -100:
            continue
        p = score_personal(champion_id, role, puuid)
        r = apply_rules(champion_id, rules, ally_picks, enemy_picks, ally_bans, enemy_bans, role, mode)
        patch = 0.0

        total = W_DRAFT * d.score + W_PERSONAL * p.score + W_NOTES * r.score + W_PATCH * patch
        reasons = d.reasons + p.reasons + r.reasons
        results.append(
            (
                champion_id,
                ScoreBreakdown(draft=d.score, personal=p.score, rules=r.score, patch=patch, total=total, reasons=reasons),
            )
        )

    results.sort(key=lambda x: x[1].total, reverse=True)
    return results[:top_k]
