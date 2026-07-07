"""Recipe definitions for the additive deliverable engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

RecipeKind = Literal["composed", "production"]
StageKind = Literal["mission", "compose", "pipeline", "export"]
Tier = Literal["local", "cloud"]


@dataclass(frozen=True)
class InputSpec:
    key: str
    label_key: str


@dataclass(frozen=True)
class Stage:
    kind: StageKind
    label_key: str
    tier: Tier = "local"
    params: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Recipe:
    id: str
    kind: RecipeKind
    name_key: str
    desc_key: str
    required_inputs: list[InputSpec]
    stages: list[Stage]
    pipeline: str | None = None


@dataclass
class RecipeRun:
    run_id: str
    recipe_id: str
    subject: str
    cloud_optins: set[str] = field(default_factory=set)
    stage_index: int = 0
    outputs: dict = field(default_factory=dict)
