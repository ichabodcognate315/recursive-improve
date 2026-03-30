"""Evolution engine: init, update, status, cleanup. The skill does the rest."""

from __future__ import annotations

from datetime import datetime, timezone

from recursive_improve.evolve.island import create_island, list_islands, cleanup_all, git_run
from recursive_improve.evolve.status import read_status, write_status, update_island_score
from recursive_improve.ratchet.config import RatchetConfig


def evolve_init(config: RatchetConfig) -> dict:
    """Create N island worktrees and write initial status."""
    session_id = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    base_ref = git_run("rev-parse", "--short", "HEAD").stdout.strip()

    islands = []
    for i in range(config.n_islands):
        info = create_island(i, base_ref, config.islands_dir, session_id)
        islands.append(info)

    write_status(config.islands_dir, {
        "session_id": session_id,
        "base_ref": base_ref,
        "n_islands": config.n_islands,
        "n_generations": config.n_generations,
        "generation": 0,
        "island_scores": {},
    })

    return {
        "session_id": session_id,
        "base_ref": base_ref,
        "islands": islands,
    }


def evolve_update(config: RatchetConfig, island_id: int, score: float, generation: int) -> dict:
    """Record an island's score and update generation."""
    update_island_score(config.islands_dir, island_id, score)

    data = read_status(config.islands_dir)
    if generation > data.get("generation", 0):
        data["generation"] = generation
        write_status(config.islands_dir, data)

    return {"island_id": island_id, "score": score, "generation": generation}


def evolve_status(config: RatchetConfig) -> dict:
    """Read current evolution status."""
    data = read_status(config.islands_dir)
    if not data:
        return {"initialized": False}

    islands = list_islands(config.islands_dir)
    scores = data.get("island_scores", {})

    for island in islands:
        island["score"] = scores.get(str(island["island_id"]), None)

    best_id = None
    best_score = None
    for iid_str, score in scores.items():
        if best_score is None or score > best_score:
            best_score = score
            best_id = int(iid_str)

    return {
        "initialized": True,
        "session_id": data.get("session_id"),
        "base_ref": data.get("base_ref"),
        "generation": data.get("generation", 0),
        "n_generations": data.get("n_generations", config.n_generations),
        "islands": islands,
        "best_island": best_id,
        "best_score": best_score,
        "converged": data.get("generation", 0) >= data.get("n_generations", config.n_generations),
    }


def evolve_cleanup(config: RatchetConfig) -> dict:
    """Remove all island worktrees and status."""
    count = cleanup_all(config.islands_dir)
    return {"removed": count}
