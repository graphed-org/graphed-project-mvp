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

> ⚙️ **This file is generated** by [`scripts/gen_readme.py`](scripts/gen_readme.py) from
> [`.graphed/state.json`](.graphed/state.json) + the live submodule pins, and CI fails if it drifts.
> Edit the state, not this file. The machine-readable source of truth is `.graphed/state.json`.

## Milestone status

**12 of 12 milestones DONE — all CI-green on the §A.5 matrix.** Current milestone: **DONE**.

| Milestone | Status | Repo(s) | What it delivered |
|---|:--:|---|---|
| **ORCH** | ✅ DONE | graphed-orchestrator | Deterministic orchestrator engine (Part B + B.8 faker suite) |
| **M0** | ✅ DONE | graphed-orchestrator, graphed-corpus, graphed-debug, graphed-exec-local, graphed-checkpoint, graphed-preserve | Repository spine (per repo) |
| **M0.5** | ✅ DONE | graphed-corpus | Reference corpus study & Required Operations Catalog |
| **M1** | ✅ DONE | graphed-core | graphed-core thread-safe interned graph IR |
| **M2** | ✅ DONE | graphed, graphed-numpy | frontend + backend protocol + graphed-numpy |
| **M3** | ✅ DONE | graphed-awkward, graphed | graphed-awkward typetracer forms + provenance |
| **M4** | ✅ DONE | graphed-core | graphed-core optimizer: DCE/CSE + equality-saturation stage fusion |
| **M5** | ✅ DONE | graphed-awkward, graphed-numpy, graphed | Necessary-buffer (column) projection |
| **M6** | ✅ DONE | graphed-debug | graphed-debug: opt-level lowering, source-mapped tracebacks, viz |
| **M7** | ✅ DONE | graphed-exec-local, graphed-core | Execution-layer contract + graphed-exec-local |
| **M8** | ✅ DONE | graphed-checkpoint, graphed-core, graphed | graphed-checkpoint: plan serialization + checkpoint/resume |
| **M9** | ✅ DONE | graphed-preserve, graphed-core, graphed, graphed-awkward | graphed-preserve: analysis preservation bundle |

The development process is a **gated three-role pipeline** (test-author → implementer → reviewer)
coordinated by the deterministic `graphed-orchestrator`. A milestone is `DONE` only when every
mechanical gate is green **and** the §A.5-matrix CI for the exact pinned commit is confirmed green —
the orchestrator refuses to record DONE off an unfinished CI run.

## Repositories

| Repo | Role | Pinned commit | State |
|---|---|---|:--:|
| [graphed-project](https://github.com/graphed-org/graphed-project) | meta/superproject | — | meta |
| [graphed](https://github.com/graphed-org/graphed) | M2/M3 frontend | `f99bffb` | ✅ submodule |
| [graphed-awkward](https://github.com/graphed-org/graphed-awkward) | M3/M5 reference backend | `c2b05a7` | ✅ submodule |
| [graphed-checkpoint](https://github.com/graphed-org/graphed-checkpoint) | M8 checkpoint/resume | `80d2dfa` | ✅ submodule |
| [graphed-core](https://github.com/graphed-org/graphed-core) | M1/M4/M7-contract/M8-plan | `4c5590c` | ✅ submodule |
| [graphed-corpus](https://github.com/graphed-org/graphed-corpus) | M0.5 requirements + fixtures | `eebd14e` | ✅ submodule |
| [graphed-debug](https://github.com/graphed-org/graphed-debug) | M6 debug/tracebacks | `bba6b77` | ✅ submodule |
| [graphed-exec-local](https://github.com/graphed-org/graphed-exec-local) | M7 reference executor | `af5913f` | ✅ submodule |
| [graphed-numpy](https://github.com/graphed-org/graphed-numpy) | M2 trivial backend | `66dab2a` | ✅ submodule |
| [graphed-orchestrator](https://github.com/graphed-org/graphed-orchestrator) | Part B deterministic orchestrator | `ed85a25` | ✅ submodule |
| [graphed-preserve](https://github.com/graphed-org/graphed-preserve) | M9 preservation bundle | `02b603a` | ✅ submodule |

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

<sub>Generated from <code>.graphed/state.json</code> (updated 2026-06-05T19:36:01Z).</sub>
