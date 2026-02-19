from core.draft_engine import score_draft


def test_score_draft_synergy_and_counter_positive() -> None:
    res = score_draft(
        champion_id=54,
        ally_picks=[120],
        enemy_picks=[238],
        ally_bans=[],
        enemy_bans=[],
        mode="counter",
    )
    assert res.score > 0
    assert any("sinergia" in r for r in res.reasons)
    assert any("counter" in r for r in res.reasons)
