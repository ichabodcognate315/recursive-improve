"""Flat JSON status file for evolution state."""

from __future__ import annotations

import json
from pathlib import Path


def read_status(islands_dir: str) -> dict:
    """Read evolution status. Returns empty dict if not initialized."""
    p = Path(islands_dir) / "status.json"
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def write_status(islands_dir: str, data: dict) -> None:
    """Write evolution status."""
    p = Path(islands_dir) / "status.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, indent=2), encoding="utf-8")


def update_island_score(islands_dir: str, island_id: int, score: float) -> None:
    """Update an island's score in the status file."""
    data = read_status(islands_dir)
    scores = data.get("island_scores", {})
    scores[str(island_id)] = round(score, 4)
    data["island_scores"] = scores
    write_status(islands_dir, data)
