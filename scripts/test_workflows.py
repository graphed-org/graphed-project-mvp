"""Config-drift guard (M10, finding B.4/B.5): every package repo's CI must cover the plan A.5
matrix and ship build-only wheel artifacts — and NONE of them may publish to PyPI.

Pure-text assertions (no YAML dependency) over each submodule's `.github/workflows/`. Run by the
`workflow-matrix` job of the meta repo's readme-sync workflow (submodules checked out). If a
sub-repo weakens its matrix, drops its wheels build, or grows a publish step, this fails the meta
build even though the sub-repo's own CI stays green.
"""

from __future__ import tomllib
import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Post-consolidation (2026-07-17) the frontend/core/awkward/numpy/debug/checkpoint/preserve packages
# live in ONE repo, `graphed`; `graphed-exec-local` is the `graphed-executors` package. So the guard
# now covers the five live submodules, not the pre-consolidation per-package repos.
REPOS = [
    "graphed",
    "graphed-exec-local",
    "graphed-corpus",
    "graphed-orchestrator",
    "graphed-histogram",
]

# what the A.5 matrix requires of every repo's test job
REQUIRED_CI_MARKERS = [
    "ubuntu-latest",
    "ubuntu-24.04-arm",  # the arch dimension
    "macos-latest",
    "windows-latest",
    '"3.11"',
    '"3.12"',
    '"3.13"',
    '"3.14"',
    "3.14t",  # free-threaded (required gate in graphed-core; advisory where deps lag)
]

# strings that may never appear in any workflow: CI must not publish anywhere
FORBIDDEN_PUBLISH_MARKERS = [
    "pypa/gh-action-pypi-publish",
    "twine upload",
    "maturin publish",
    "maturin upload",
    "pypi-publish",
]


def _workflows(repo: str) -> dict[str, str]:
    wf_dir = ROOT / repo / ".github" / "workflows"
    assert wf_dir.is_dir(), (
        f"{repo}: no .github/workflows (submodules not checked out?)"
    )
    return {p.name: p.read_text() for p in sorted(wf_dir.glob("*.yml"))}


def test_every_repo_ci_covers_the_a5_matrix() -> None:
    for repo in REPOS:
        ci = _workflows(repo).get("ci.yml")
        assert ci, f"{repo}: ci.yml missing"
        for marker in REQUIRED_CI_MARKERS:
            assert marker in ci, f"{repo}/ci.yml lost {marker!r} from the A.5 matrix"


def test_every_repo_builds_wheel_artifacts() -> None:
    for repo in REPOS:
        wheels = _workflows(repo).get("wheels.yml")
        assert wheels, f"{repo}: wheels.yml missing (A.5: wheels build on all targets)"
        assert "upload-artifact" in wheels, (
            f"{repo}/wheels.yml does not upload the built dist"
        )


def test_no_branch_push_or_pr_workflow_publishes_to_pypi() -> None:
    """Publishing may exist ONLY behind an explicit human release act — a published GitHub `release:`
    event, a version-TAG push (`vX.Y.Z`), or a manual `workflow_dispatch`. Nothing that runs on
    branch pushes or PRs — i.e. ordinary CI — may upload anywhere. (The consolidated repos publish on
    a version-tag push with OIDC provenance, which carries no `release:` event, so the guard checks
    the invariant — no PR, no branch push — rather than mandating a `release:` trigger specifically.)"""
    for repo in REPOS:
        for name, text in _workflows(repo).items():
            has_publish = any(marker in text for marker in FORBIDDEN_PUBLISH_MARKERS)
            if not has_publish:
                continue
            head = text.split("jobs:")[0]  # the `on:` trigger block
            assert "pull_request" not in head, (
                f"{repo}/{name}: a PR workflow must never publish"
            )
            # a `push:` trigger on a publishing workflow must be version-TAG-only, never a branch push
            # (a `release:` event or a `workflow_dispatch` carries no push block and is fine).
            if "push:" in head:
                push_block = head.split("push:", 1)[1].split("release:", 1)[0]
                assert "tags:" in push_block and "branches:" not in push_block, (
                    f"{repo}/{name}: a branch-push-triggered workflow must never publish"
                )


def test_graphed_wheels_cover_every_target_and_freethreaded() -> None:
    # Post-consolidation the Rust core ships in the `graphed` repo's wheels: cibuildwheel drives
    # maturin from [tool.cibuildwheel] in pyproject, one native runner per (OS, arch).
    wheels = _workflows("graphed")["wheels.yml"]
    for marker in (
        "ubuntu-latest",  # linux x86_64
        "ubuntu-24.04-arm",  # linux aarch64
        "macos-14",  # macOS arm64
        "macos-15-intel",  # macOS x86_64 (the last Intel runner)
        "windows-latest",
    ):
        assert marker in wheels, f"graphed/wheels.yml lost target {marker!r}"
    cibw = tomllib.loads((ROOT / "graphed" / "pyproject.toml").read_text())["tool"]["cibuildwheel"]
    assert "cp314t-*" in cibw["build"], (
        "graphed lost the dedicated free-threaded cp314t wheel (plan §A.5)"
    )


def test_graphed_gates_rust_coverage_and_freethreaded() -> None:
    # Post-consolidation the Rust coverage + free-threaded gates live in the `graphed` repo's CI.
    ci = _workflows("graphed")["ci.yml"]
    assert "cargo llvm-cov" in ci and "--fail-under-lines" in ci, (
        "graphed/ci.yml lost the Rust coverage gate (finding B.5)"
    )
    assert (
        "test-freethreaded" in ci
        and "continue-on-error"
        not in ci.split("test-freethreaded")[1].split("steps:")[0]
    ), "graphed 3.14t job must be a required gate"
