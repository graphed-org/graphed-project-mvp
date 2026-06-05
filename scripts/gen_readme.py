#!/usr/bin/env python3
"""Generate the meta repo's README.md from `.graphed/state.json` + the live submodule pins, so the
high-level status is ALWAYS in sync with the machine-readable state (no hand-maintained drift).

Usage:
    python scripts/gen_readme.py            # write README.md
    python scripts/gen_readme.py --check     # exit 1 if README.md is out of sync (used in CI)

The render is a pure function of (state, pins); `pins` is injectable so the renderer is unit-tested
without git or a network.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STATE_PATH = ROOT / ".graphed" / "state.json"
README_PATH = ROOT / "README.md"

STATUS_BADGE = {"DONE": "✅ DONE", "PENDING": "⬜ PENDING"}

_INTRO = """# graphed-project

Meta / superproject for **graphed** — a schedulable, serializable, debuggable HEP task-graph system
that reduces a graph to a concise set of stage-nodes *incrementally as the user builds it*, so a
large un-reduced graph never exists. Reduction runs in a Rust extension via equality saturation over
e-graphs. The goal is the middle path between dask-awkward (kept a huge graph; O(N²) optimization
dominated wall time) and coffea 2025 (discarded the schedulable graph).

This repo holds the root [`CLAUDE.md`](CLAUDE.md), the authoritative plan
(`graphed-project-plan-gated.md`), and the package repos as **git submodules**. It is **multi-repo**:
each package lives in its own repo under the [`graphed-org`](https://github.com/graphed-org)
organization and replicates the M0 spine (per-package CI on the §A.5 matrix, wheels, Sphinx).

> ⚙️ **This file is generated** by [`scripts/gen_readme.py`](scripts/gen_readme.py) from
> [`.graphed/state.json`](.graphed/state.json) + the live submodule pins, and CI fails if it drifts.
> Edit the state, not this file. The machine-readable source of truth is `.graphed/state.json`."""

_PIPELINE = """The development process is a **gated three-role pipeline** (test-author → implementer → reviewer)
coordinated by the deterministic `graphed-orchestrator`. A milestone is `DONE` only when every
mechanical gate is green **and** the §A.5-matrix CI for the exact pinned commit is confirmed green —
the orchestrator refuses to record DONE off an unfinished CI run."""

_SUBMODULES = """## Working with the submodules

```bash
# clone the whole project
git clone --recurse-submodules git@github.com:graphed-org/graphed-project.git
# or, after a plain clone:
git submodule update --init --recursive
# pull latest of everything
git pull && git submodule update --init --recursive
```

When a submodule advances, the superproject commits the updated pointer so it pins a known-good
revision of every package."""

_PRECEDENCE = """## Precedence

When guidance conflicts, the higher authority wins: **(1)** the project plan
(`graphed-project-plan-gated.md`) always wins · **(2)** the root [`CLAUDE.md`](CLAUDE.md) · **(3)** a
sub-repo's `CLAUDE.md` (local detail only)."""


def load_state(path: Path = STATE_PATH) -> dict:
    return json.loads(path.read_text())


_PIN_RE = re.compile(r"^[ +\-U]?([0-9a-f]{40})\s+(\S+)")


def submodule_pins(root: Path = ROOT) -> dict[str, str]:
    """Map submodule path -> SHA via `git submodule status`. This reports the working-tree pin (the
    one a bookkeeping commit is about to record), so a combined submodule-advance + README commit is
    self-consistent; in CI it equals the committed pin. Needs no submodule checkout or network."""
    out = subprocess.run(
        ["git", "-C", str(root), "submodule", "status"], capture_output=True, text=True, check=True
    ).stdout
    pins: dict[str, str] = {}
    for line in out.splitlines():
        m = _PIN_RE.match(line)
        if m:
            pins[m.group(2)] = m.group(1)
    return pins


def _clean_repos(repos: list[str]) -> list[str]:
    """Strip annotations like 'graphed-orchestrator (DONE)' -> 'graphed-orchestrator'."""
    return [re.sub(r"\s*\(.*?\)", "", r).strip() for r in repos]


def _repo_order(name: str, info: dict, meta_repo: str) -> tuple[int, int, str]:
    return (0 if name == meta_repo else 1, 0 if info.get("created") else 1, name)


def render(state: dict, pins: dict[str, str]) -> str:
    milestones = state["milestones"]
    repos = state["repos"]
    meta_repo = state.get("meta_repo", "graphed-project")
    org = state.get("org", "graphed-org")
    done = sum(1 for m in milestones.values() if m["status"] == "DONE")
    total = len(milestones)

    lines: list[str] = [_INTRO, "", "## Milestone status", ""]
    lines.append(
        f"**{done} of {total} milestones DONE — all CI-green on the §A.5 matrix.** "
        f"Current milestone: **{state['current_milestone']}**."
    )
    lines += ["", "| Milestone | Status | Repo(s) | What it delivered |", "|---|:--:|---|---|"]
    for mid, m in milestones.items():
        badge = STATUS_BADGE.get(m["status"], m["status"])
        repo_cell = ", ".join(_clean_repos(m["repos"])) or "—"
        lines.append(f"| **{mid}** | {badge} | {repo_cell} | {m['title']} |")
    lines += ["", _PIPELINE, "", "## Repositories", ""]
    lines += ["| Repo | Role | Pinned commit | State |", "|---|---|---|:--:|"]
    for name in sorted(repos, key=lambda n: _repo_order(n, repos[n], meta_repo)):
        info = repos[name]
        link = f"[{name}](https://github.com/{org}/{name})"
        if name == meta_repo:
            pin, state_cell = "—", "meta"
        elif info.get("is_submodule") and name in pins:
            pin, state_cell = f"`{pins[name][:7]}`", "✅ submodule"
        elif info.get("created"):
            pin, state_cell = "—", "✅ created"
        else:
            pin, state_cell = "—", "lazy"
        lines.append(f"| {link} | {info.get('role', '')} | {pin} | {state_cell} |")
    lines += [
        "",
        "`lazy` repos are created when their milestone begins.",
        "",
        _SUBMODULES,
        "",
        _PRECEDENCE,
        "",
        f"<sub>Generated from <code>.graphed/state.json</code> (updated {state.get('updated_at', '?')}).</sub>",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true", help="exit 1 if README.md is out of sync")
    args = ap.parse_args(argv)

    content = render(load_state(), submodule_pins())
    if args.check:
        current = README_PATH.read_text() if README_PATH.exists() else ""
        if current != content:
            print("README.md is OUT OF SYNC with .graphed/state.json.", file=sys.stderr)
            print("Run: python scripts/gen_readme.py", file=sys.stderr)
            return 1
        print("README.md is in sync.")
        return 0
    README_PATH.write_text(content)
    print(f"wrote {README_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
