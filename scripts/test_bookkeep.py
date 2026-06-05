"""Validity tests for the meta-repo bookkeeping helpers."""

from __future__ import annotations

import re

import bookkeep


def test_set_current_mutates_rollup() -> None:
    state = {"current_milestone": "M5"}
    bookkeep.set_current(state, "M6")
    assert state["current_milestone"] == "M6"


def test_set_updated_at() -> None:
    state: dict = {}
    bookkeep.set_updated_at(state, "2026-06-05T03:00:00Z")
    assert state["updated_at"] == "2026-06-05T03:00:00Z"


def test_now_iso_is_utc_zulu() -> None:
    stamp = bookkeep.now_iso()
    # e.g. 2026-06-05T03:00:00Z — UTC, second precision, trailing Z (no microseconds, no +00:00)
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", stamp), stamp


def test_files_to_stage_includes_state_readme_and_every_submodule() -> None:
    pins = {"graphed-core": "abc", "graphed": "def"}
    staged = bookkeep.files_to_stage(pins)
    assert staged[0] == ".graphed/state.json"
    assert "README.md" in staged
    # every submodule pointer is staged so an advanced pin is captured
    assert "graphed-core" in staged and "graphed" in staged
    # submodules are sorted/deterministic
    assert staged[2:] == sorted(pins)


def test_files_to_stage_with_no_submodules() -> None:
    assert bookkeep.files_to_stage({}) == [".graphed/state.json", "README.md"]
