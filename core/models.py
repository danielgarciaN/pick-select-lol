from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class Champion(BaseModel):
    id: int
    name: str
    key_str: str
    tags: list[str] = Field(default_factory=list)
    icon_url: str | None = None


class Player(BaseModel):
    puuid: str
    game_name: str
    tag_line: str
    region: str


class Rule(BaseModel):
    id: int | None = None
    condition_type: Literal["enemy_pick", "ally_pick", "role", "team_need", "banned", "mode"]
    condition_value: str
    target_type: Literal["champion", "tag"]
    target_value: str
    weight: float
    note: str | None = None


class ScoreBreakdown(BaseModel):
    draft: float
    personal: float
    rules: float
    patch: float
    total: float
    reasons: list[str]
