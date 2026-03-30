"""Git worktree operations for evolution islands."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


def git_run(*args: str, cwd: str | Path | None = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command. Used by island and engine modules."""
    return subprocess.run(["git", *args], capture_output=True, text=True, cwd=cwd, check=check)


def create_island(island_id: int, base_ref: str, islands_dir: str, session_id: str) -> dict:
    """Create a worktree for an island. Returns {island_id, path, branch}."""
    branch = f"ri/evolve-{session_id}-island-{island_id}"
    wt = Path(islands_dir) / f"island-{island_id}"
    wt.parent.mkdir(parents=True, exist_ok=True)

    if wt.exists():
        git_run("worktree", "remove", str(wt), "--force", check=False)
    git_run("branch", "-D", branch, check=False)

    git_run("worktree", "add", str(wt), "-b", branch, base_ref)
    return {"island_id": island_id, "path": str(wt.resolve()), "branch": branch}


def destroy_island(island_id: int, islands_dir: str) -> None:
    """Remove a worktree and its branch."""
    wt = Path(islands_dir) / f"island-{island_id}"
    if wt.exists():
        git_run("worktree", "remove", str(wt), "--force", check=False)
    result = git_run("branch", "--list", f"ri/evolve-*-island-{island_id}", check=False)
    for line in result.stdout.splitlines():
        branch = line.strip().lstrip("* ")
        if branch:
            git_run("branch", "-D", branch, check=False)


def list_islands(islands_dir: str) -> list[dict]:
    """List active islands from git worktree list."""
    result = git_run("worktree", "list", "--porcelain", check=False)
    if result.returncode != 0:
        return []

    islands = []
    path = branch = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            path = line.split(" ", 1)[1]
        elif line.startswith("branch "):
            branch = line.split(" ", 1)[1].replace("refs/heads/", "")
        elif line == "":
            if path and branch and "ri/evolve-" in (branch or ""):
                name = Path(path).name
                if name.startswith("island-"):
                    try:
                        iid = int(name.split("-", 1)[1])
                        islands.append({"island_id": iid, "path": path, "branch": branch})
                    except ValueError:
                        pass
            path = branch = None
    return sorted(islands, key=lambda i: i["island_id"])


def cleanup_all(islands_dir: str) -> int:
    """Remove all island worktrees and branches."""
    islands = list_islands(islands_dir)
    for i in islands:
        destroy_island(i["island_id"], islands_dir)
    p = Path(islands_dir)
    if p.exists():
        shutil.rmtree(p, ignore_errors=True)
    return len(islands)
