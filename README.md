# graphed-project

Meta / superproject for **graphed** — a schedulable, serializable, debuggable HEP task-graph system
that reduces a graph to a concise set of stage-nodes *incrementally as the user builds it*, so a
large un-reduced graph never exists. Reduction runs in a Rust extension via equality saturation over
e-graphs. The goal is the middle path between dask-awkward (kept a huge graph; O(N²) optimization
dominated wall time) and coffea 2025 (discarded the schedulable graph).

This repo holds the root [`CLAUDE.md`](CLAUDE.md), the authoritative plan
(`graphed-project-plan-gated.md`), and the package repos as **git submodules**. It is **multi-repo**:
each package lives in its own repo under the [`graphed-org`](https://github.com/graphed-org)
organization and replicates the M0 spine (per-package CI on the §A.5 matrix, wheels, Sphinx).

> This README is the easily-accessible high-level status. The authoritative machine-readable state
> is [`.graphed/state.json`](.graphed/state.json) (this repo) and one per sub-repo.

## Milestone status

**8 of 12 milestones DONE — all CI-green on the §A.5 matrix.** Current milestone: **M6**.

| Milestone | Status | Repo(s) | What it delivered |
|-----------|:------:|---------|-------------------|
| **ORCH** | ✅ DONE | graphed-orchestrator | Deterministic state machine, mechanical gates, stall/escalation ladder, B.8 faker suite, **CI-confirmation gate** |
| **M0** | ✅ DONE | every repo | Per-repo CI / tooling / wheels / Sphinx spine |
| **M0.5** | ✅ DONE | graphed-corpus | Required Operations Catalog + ADL 1–8 / AGC-ttbar / TTGamma fixtures (reproduced bit-for-bit) |
| **M1** | ✅ DONE | graphed-core | Thread-safe interned IR (Rust + PyO3); hash-consing = CSE |
| **M2** | ✅ DONE | graphed, graphed-numpy | Python frontend + `Backend` protocol + trivial numpy backend |
| **M3** | ✅ DONE | graphed-awkward, graphed | awkward typetracer forms + real provenance + correctionlib/ONNX `External` nodes |
| **M4** | ✅ DONE | graphed-core | Optimizer: DCE/CSE + equality-saturation stage fusion (`egg` behind `RewriteEngine`); super-linear-reduction CI benchmark guard |
| **M5** | ✅ DONE | graphed-awkward, graphed-numpy, graphed | Necessary-buffer (column) projection — **over-touch protected** |
| **M6** | ⬜ PENDING | graphed-debug | opt-level lowering (`opt_level=0` is 1:1) + picklable source-mapped `StageError` |
| **M7** | ⬜ PENDING | graphed-exec-local, graphed-core | Reference executor + exec protocol (AGC ttbar slice end-to-end) |
| **M8** | ⬜ PENDING | graphed-checkpoint, graphed-core | Deterministic `Plan` serialization + content-addressed checkpoint/resume |
| **M9** | ⬜ PENDING | graphed-preserve | Self-contained content-addressed Preservation Bundle |

The development process is a **gated three-role pipeline** (test-author → implementer → reviewer)
coordinated by the deterministic `graphed-orchestrator`. A milestone is `DONE` only when every
mechanical gate is green **and** the §A.5-matrix CI for the exact pinned commit is confirmed green —
the orchestrator refuses to record DONE off an unfinished CI run.

## Repositories

| Repo | Milestones | Pinned commit | Exists |
|------|------------|---------------|:------:|
| [graphed-project](https://github.com/graphed-org/graphed-project) | meta / superproject | — | ✅ |
| [graphed-orchestrator](https://github.com/graphed-org/graphed-orchestrator) | ORCH, M0 | `44b1a8c` | ✅ |
| [graphed-corpus](https://github.com/graphed-org/graphed-corpus) | M0, M0.5 | `f7a2f23` | ✅ |
| [graphed-core](https://github.com/graphed-org/graphed-core) | M0, M1, M4 | `101cb8d` | ✅ |
| [graphed](https://github.com/graphed-org/graphed) | M0, M2, M3, M5 | `3eb4241` | ✅ |
| [graphed-numpy](https://github.com/graphed-org/graphed-numpy) | M0, M2, M5 | `9b5f465` | ✅ |
| [graphed-awkward](https://github.com/graphed-org/graphed-awkward) | M0, M3, M5 | `1a1bf2a` | ✅ |
| graphed-debug | M6 | — | lazy |
| graphed-exec-local | M7 | — | lazy |
| graphed-checkpoint | M8 | — | lazy |
| graphed-preserve | M9 | — | lazy |

`lazy` repos are created when their milestone begins.

## Working with the submodules

```bash
# clone the whole project
git clone --recurse-submodules git@github.com:graphed-org/graphed-project.git
# or, after a plain clone:
git submodule update --init --recursive
# pull latest of everything
git pull && git submodule update --init --recursive
```

When a submodule advances, the superproject commits the updated pointer so it pins a known-good
revision of every package.

## Precedence

When guidance conflicts, the higher authority wins: **(1)** the project plan
(`graphed-project-plan-gated.md`) always wins · **(2)** the root [`CLAUDE.md`](CLAUDE.md) · **(3)** a
sub-repo's `CLAUDE.md` (local detail only).

<sub>Status as of 2026-06-05. Maintained alongside <code>.graphed/state.json</code>.</sub>
