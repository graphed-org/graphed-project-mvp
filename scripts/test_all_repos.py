#!/usr/bin/env python3
"""Run every submodule repo's test suite against the CURRENT (possibly uncommitted) editable installs.

A cross-repo smoke: a change in one package — e.g. flipping the executor's default reduction to peer
(M38) — is live for every consumer through the shared editable venv, so this catches a downstream
break before it is committed. Each repo is run from its own directory so its pytest config /
conftest / pythonpath apply; results are summarized and the exit code is nonzero if any repo failed.

    python scripts/test_all_repos.py            # all repos
    python scripts/test_all_repos.py graphed-preserve graphed-checkpoint   # a subset
"""

from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPOS = (
    "graphed-core",
    "graphed",
    "graphed-numpy",
    "graphed-awkward",
    "graphed-debug",
    "graphed-exec-local",
    "graphed-checkpoint",
    "graphed-preserve",
    "graphed-corpus",
    "graphed-histogram",
    "graphed-orchestrator",
)


def main(argv: list[str]) -> int:
    repos = argv or list(REPOS)
    results: dict[str, tuple[int, str, float]] = {}
    for repo in repos:
        d = ROOT / repo
        if not (d / "pyproject.toml").is_file():
            print(f"SKIP {repo:22s} (not checked out)", flush=True)
            continue
        t0 = time.perf_counter()
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--timeout=900"],
            cwd=d,
            capture_output=True,
            text=True,
        )
        dt = time.perf_counter() - t0
        last = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "(no output)"
        results[repo] = (proc.returncode, last, dt)
        print(f"{'OK  ' if proc.returncode == 0 else 'FAIL'} {repo:22s} {dt:6.1f}s  {last}", flush=True)
        if proc.returncode != 0:  # show the failure tail so a break is actionable from the log
            print("\n".join(proc.stdout.strip().splitlines()[-25:]), flush=True)

    bad = [r for r, (rc, _, _) in results.items() if rc != 0]
    print(f"\n{'ALL REPOS GREEN' if not bad else 'FAILURES: ' + ', '.join(bad)}", flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
