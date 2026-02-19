from core.draft_engine import apply_rules
from core.models import Rule


def test_apply_rules_enemy_pick_and_target_champion() -> None:
    rules = [
        Rule(
            condition_type="enemy_pick",
            condition_value="238",
            target_type="champion",
            target_value="99",
            weight=3.0,
            note="Counter a Zed",
        )
    ]
    res = apply_rules(
        champion_id=99,
        rules=rules,
        ally_picks=[],
        enemy_picks=[238],
        ally_bans=[],
        enemy_bans=[],
        role="mid",
        mode="counter",
    )
    assert res.score == 3.0
    assert any("Counter a Zed" in x for x in res.reasons)
