#!/usr/bin/env python3
"""Meta-repo bookkeeping entrypoint — the one step that records project state.

It ALWAYS regenerates `README.md` (via `gen_readme`) before staging, so the human-readable status can
never be committed out of sync with `.graphed/state.json` or the submodule pins. Optional convenience
mutations (`--set-current`, `--touch`) edit the state first; richer per-milestone edits (status,
evidence) stay explicit in `.graphed/state.json`.

Usage:
    python scripts/bookkeep.py                              # sync README, stage state+README+submodules
    python scripts/bookkeep.py --set-current M6 --touch     # bump rollup fields, then sync + stage
    python scripts/bookkeep.py --commit "M5 DONE: ..."      # also commit
    python scripts/bookkeep.py --commit "..." --push        # also push
"""

from __future__ import annotations

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

import gen_readme

ROOT = gen_readme.ROOT
STATE_PATH = gen_readme.STATE_PATH
CO_AUTHOR = "Co-Authored-By: Claude Opus 4.8 <noreply@anthropic.com>"


# ---- pure state helpers (unit-tested) ---------------------------------------
def set_current(state: dict, milestone: str) -> dict:
    state["current_milestone"] = milestone
    return state


def set_updated_at(state: dict, iso: str) -> dict:
    state["updated_at"] = iso
    return state


def now_iso() -> str:
    return datetime.datetime.now(datetime.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def files_to_stage(pins: dict[str, str]) -> list[str]:
    """The paths a bookkeeping commit touches: the state, the generated README, and every submodule
    pointer (so an advanced pin is captured)."""
    return [".graphed/state.json", "README.md", *sorted(pins)]


# ---- git/IO orchestration ---------------------------------------------------
def _git(*args: str) -> None:
    subprocess.run(["git", "-C", str(ROOT), *args], check=True)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--set-current", metavar="MID", help="set milestones rollup current_milestone")
    ap.add_argument("--touch", action="store_true", help="set updated_at to now (UTC)")
    ap.add_argument("--commit", metavar="MSG", help="commit the staged bookkeeping changes")
    ap.add_argument("--push", action="store_true", help="push after committing")
    args = ap.parse_args(argv)

    state = gen_readme.load_state()
    if args.set_current:
        set_current(state, args.set_current)
    if args.touch:
        set_updated_at(state, now_iso())
    if args.set_current or args.touch:
        STATE_PATH.write_text(json.dumps(state, indent=2) + "\n")

    # the hook: regenerate the README from the (possibly just-edited) state + live pins
    gen_readme.main([])
    if gen_readme.main(["--check"]) != 0:  # belt-and-suspenders: must be in sync after regenerating
        print("internal error: README still out of sync after regeneration", file=sys.stderr)
        return 1

    _git("add", *files_to_stage(gen_readme.submodule_pins()))
    if args.commit:
        _git("commit", "-m", f"{args.commit}\n\n{CO_AUTHOR}")
        if args.push:
            _git("push", "origin", "HEAD")
    else:
        _git("status", "--short")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
