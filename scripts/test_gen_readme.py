"""Validity tests for the README generator (run in CI before the sync check)."""

from __future__ import annotations

import gen_readme

# a minimal, self-contained state used so the tests don't depend on the live project state
STATE = {
    "project": "graphed",
    "org": "graphed-org",
    "meta_repo": "graphed-project",
    "current_milestone": "M6",
    "updated_at": "2026-01-01T00:00:00Z",
    "repos": {
        "graphed-project": {"role": "meta/superproject", "created": True, "is_submodule": False},
        "graphed-core": {"role": "M1/M4 core", "created": True, "is_submodule": True},
        "graphed-debug": {"role": "M6 debug", "created": False, "is_submodule": False},
    },
    "milestones": {
        "M1": {"title": "interned IR", "repos": ["graphed-core"], "status": "DONE", "phase": "DONE"},
        "M4": {"title": "optimizer", "repos": ["graphed-core"], "status": "DONE", "phase": "DONE"},
        "M6": {"title": "debug", "repos": ["graphed-debug"], "status": "PENDING", "phase": "PENDING"},
    },
}
PINS = {"graphed-core": "101cb8d3d77bf126d55f6d8e4ae3b286c7a6b8f5"}


def test_render_is_deterministic() -> None:
    assert gen_readme.render(STATE, PINS) == gen_readme.render(STATE, PINS)


def test_done_count_and_current_milestone() -> None:
    out = gen_readme.render(STATE, PINS)
    assert "**2 of 3 milestones DONE" in out  # M1 + M4 done, M6 pending
    assert "Current milestone: **M6**" in out


def test_status_badges() -> None:
    out = gen_readme.render(STATE, PINS)
    assert "| **M1** | ✅ DONE |" in out
    assert "| **M6** | ⬜ PENDING |" in out


def test_titles_and_repos_present() -> None:
    out = gen_readme.render(STATE, PINS)
    for mid in STATE["milestones"]:
        assert f"**{mid}**" in out
    assert "interned IR" in out and "optimizer" in out


def test_pinned_commit_is_short_sha() -> None:
    out = gen_readme.render(STATE, PINS)
    assert "`101cb8d`" in out  # 7-char short sha
    assert "101cb8d3d77b" not in out  # never the full sha


def test_repo_states() -> None:
    out = gen_readme.render(STATE, PINS)
    assert "| [graphed-core](https://github.com/graphed-org/graphed-core) | M1/M4 core | `101cb8d` | ✅ submodule |" in out
    assert "lazy |" in out  # graphed-debug is not created yet
    assert "| — | meta |" in out  # the meta repo itself


def test_clean_repos_strips_annotations() -> None:
    assert gen_readme._clean_repos(["graphed-orchestrator (DONE)", "graphed-corpus"]) == [
        "graphed-orchestrator",
        "graphed-corpus",
    ]


def test_meta_repo_sorted_first() -> None:
    out = gen_readme.render(STATE, PINS)
    rows = [ln for ln in out.splitlines() if ln.startswith("| [") and "github.com" in ln]
    assert "graphed-project" in rows[0]  # meta first
    assert "graphed-debug" in rows[-1]  # lazy repo last


def test_live_state_renders_and_matches_committed_readme() -> None:
    # the real project state must render, and (post-commit) match the committed README byte-for-byte
    state = gen_readme.load_state()
    pins = gen_readme.submodule_pins()
    out = gen_readme.render(state, pins)
    assert out.startswith("# graphed-project")
    assert gen_readme.README_PATH.read_text() == out, "run scripts/gen_readme.py to refresh README.md"
