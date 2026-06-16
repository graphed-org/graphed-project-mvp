"""Config-drift guard (M10, finding B.4/B.5): every package repo's CI must cover the plan A.5
matrix and ship build-only wheel artifacts — and NONE of them may publish to PyPI.

Pure-text assertions (no YAML dependency) over each submodule's `.github/workflows/`. Run by the
`workflow-matrix` job of the meta repo's readme-sync workflow (submodules checked out). If a
sub-repo weakens its matrix, drops its wheels build, or grows a publish step, this fails the meta
build even though the sub-repo's own CI stays green.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REPOS = [
    "graphed",
    "graphed-core",
    "graphed-awkward",
    "graphed-numpy",
    "graphed-debug",
    "graphed-exec-local",
    "graphed-checkpoint",
    "graphed-preserve",
    "graphed-corpus",
    "graphed-orchestrator",
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
    """Publishing may exist ONLY behind an explicit human release act (the M0 release-workflow
    deliverable: a version tag -> TestPyPI staging, a published GitHub Release -> PyPI). Nothing
    that runs on branch pushes or PRs — i.e. ordinary CI — may upload anywhere."""
    for repo in REPOS:
        for name, text in _workflows(repo).items():
            has_publish = any(marker in text for marker in FORBIDDEN_PUBLISH_MARKERS)
            if not has_publish:
                continue
            head = text.split("jobs:")[0]  # the `on:` trigger block
            assert "release:" in head, (
                f"{repo}/{name}: publish step outside a release workflow"
            )
            assert "pull_request" not in head, (
                f"{repo}/{name}: a PR workflow must never publish"
            )
            if "push:" in head:
                push_block = head.split("push:")[1].split("release:")[0]
                assert "tags:" in push_block and "branches:" not in push_block, (
                    f"{repo}/{name}: a branch-push-triggered workflow must never publish"
                )


def test_core_wheels_cover_every_target_and_freethreaded() -> None:
    wheels = _workflows("graphed-core")["wheels.yml"]
    for marker in (
        "ubuntu-latest",
        "ubuntu-24.04-arm",
        "macos-latest",
        "windows-latest",
        "universal2-apple-darwin",
        '"3.14t"',
    ):
        assert marker in wheels, f"graphed-core/wheels.yml lost target {marker!r}"


def test_core_gates_rust_coverage_and_freethreaded() -> None:
    ci = _workflows("graphed-core")["ci.yml"]
    assert "cargo llvm-cov" in ci and "--fail-under-lines" in ci, (
        "graphed-core/ci.yml lost the Rust coverage gate (finding B.5)"
    )
    assert (
        "test-freethreaded" in ci
        and "continue-on-error"
        not in ci.split("test-freethreaded")[1].split("steps:")[0]
    ), "graphed-core 3.14t job must be a required gate"
