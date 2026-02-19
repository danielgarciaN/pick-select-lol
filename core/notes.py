from __future__ import annotations

import json
from typing import Iterable

from core.db import get_conn
from core.models import Rule


def add_note(scope: str, text: str, champion_id: int | None = None, role: str | None = None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO notes(scope, champion_id, role, text) VALUES (?, ?, ?, ?)",
            (scope, champion_id, role, text),
        )


def list_notes() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM notes ORDER BY id DESC").fetchall()
        return [dict(r) for r in rows]


def delete_note(note_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM notes WHERE id=?", (note_id,))


def add_rule(rule: Rule) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO rules(condition_type, condition_value, target_type, target_value, weight, note)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                rule.condition_type,
                rule.condition_value,
                rule.target_type,
                rule.target_value,
                rule.weight,
                rule.note,
            ),
        )


def list_rules() -> list[Rule]:
    with get_conn() as conn:
        rows = conn.execute("SELECT * FROM rules ORDER BY id DESC").fetchall()
    return [Rule(**dict(row)) for row in rows]


def delete_rule(rule_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM rules WHERE id=?", (rule_id,))


def export_rules_json() -> str:
    return json.dumps([r.model_dump() for r in list_rules()], indent=2, ensure_ascii=False)


def import_rules_json(items: Iterable[dict]) -> int:
    count = 0
    for item in items:
        item.pop("id", None)
        add_rule(Rule(**item))
        count += 1
    return count
