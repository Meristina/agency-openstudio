"""Recipe checkpoint helpers are deferred to the existing mission checkpoint seam."""

from __future__ import annotations

from dataclasses import asdict

from .models import RecipeRun


def envelope(run: RecipeRun, completed_stages: list[str]) -> dict:
    return {**asdict(run), "completed_stages": completed_stages, "cloud_optins": sorted(run.cloud_optins)}
