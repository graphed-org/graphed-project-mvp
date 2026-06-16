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

**22 of 22 milestones DONE — all CI-green on the §A.5 matrix.** Current milestone: **DONE**.

| Milestone | Status | Repo(s) | What it delivered |
|---|:--:|---|---|
| **ORCH** | ✅ DONE | graphed-orchestrator | Deterministic orchestrator engine (Part B + B.8 faker suite) |
| **M0** | ✅ DONE | graphed-orchestrator, graphed-corpus-mvp, graphed-debug-mvp, graphed-exec-local-mvp, graphed-checkpoint-mvp, graphed-preserve-mvp | Repository spine (per repo) |
| **M0.5** | ✅ DONE | graphed-corpus-mvp | Reference corpus study & Required Operations Catalog |
| **M1** | ✅ DONE | graphed-core-mvp | graphed-core thread-safe interned graph IR |
| **M2** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | frontend + backend protocol + graphed-numpy |
| **M3** | ✅ DONE | graphed-awkward-mvp, graphed-mvp | graphed-awkward typetracer forms + provenance |
| **M4** | ✅ DONE | graphed-core-mvp | graphed-core optimizer: DCE/CSE + equality-saturation stage fusion |
| **M5** | ✅ DONE | graphed-awkward-mvp, graphed-numpy-mvp, graphed-mvp | Necessary-buffer (column) projection |
| **M6** | ✅ DONE | graphed-debug-mvp | graphed-debug: opt-level lowering, source-mapped tracebacks, viz |
| **M7** | ✅ DONE | graphed-exec-local-mvp, graphed-core-mvp | Execution-layer contract + graphed-exec-local |
| **M8** | ✅ DONE | graphed-checkpoint-mvp, graphed-core-mvp, graphed-mvp | graphed-checkpoint: plan serialization + checkpoint/resume |
| **M9** | ✅ DONE | graphed-preserve-mvp, graphed-core-mvp, graphed-mvp, graphed-awkward-mvp | graphed-preserve: analysis preservation bundle |
| **M11** | ✅ DONE | graphed-mvp, graphed-numpy-mvp, graphed-awkward-mvp | dask.array parity P0: full ufunc tier + backend-idiom factorization (array_type; NumpyArray proxy; awkward stays functions-only) |
| **M12** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P1: axis-aware reductions/scans (boundary vs fusible structural rule), creation routines, deterministic random, tree-reducible monoids |
| **M13** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P2: indexing (slices/ints common; tuple subscripts numpy-side) + manipulation with axis-0 geometry rules + concatenate/unique/bincount/histogram* |
| **M14** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P3.8: graphed.apply multi-input blockwise externals + signature-aware apply_gufunc (P3.9 + P4 deferred to Phase 2 by user decision) |
| **M15** | ✅ DONE | graphed-mvp, graphed-awkward-mvp, graphed-numpy-mvp | Partitioned parquet I/O: backend-agnostic base in graphed (blind partitions, deferred write plans) + awkward specialization (schema-only forms, buffer-projection-wired writes) + numpy rectilinear specialization (R16.7 amended by user decision: parquet alone enters the numpy MVP) |
| **M16** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P0: full canonical ufunc tier on the awkward backend, the structural reduction rule on every reducer (name-based boundary classification retired), 13 new reducers |
| **M17** | ✅ DONE | graphed-mvp, graphed-awkward-mvp | dask-awkward parity P1: ~20 structure functions through the single apply dispatch + the common record-subset getitem (a[[fields]]) |
| **M18** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P2: behaviors — with_name + backend behavior registration; vector four-vectors record, evaluate, and project to exactly the leaves they read |
| **M19** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P3.8: fields/type_of/backend_of introspection (recording nothing), head/sample peeking, common slice/index ops on the awkward backend; __awkward_function__ dispatch and the rest stay Phase 2 by user decision |
| **M37** | ✅ DONE | graphed-core-mvp, graphed-exec-local-mvp, graphed-debug-mvp | Live execution dashboard (FINOS Perspective + websockets + a network transport): passive Monitor seam (graphed-core, unchanged), executor emit (graphed-exec-local), and graphed-debug's DashboardServer (perspective Server + Tornado) + NetworkMonitor (websocket, loopback or remote) + Dashboard + pyinstrument profile rows. Determinism gate green attached-or-not. Root prompt R20. (SSE/uPlot prototype on m37-sse-uplot.) |

The development process is a **gated three-role pipeline** (test-author → implementer → reviewer)
coordinated by the deterministic `graphed-orchestrator`. A milestone is `DONE` only when every
mechanical gate is green **and** the §A.5-matrix CI for the exact pinned commit is confirmed green —
the orchestrator refuses to record DONE off an unfinished CI run.

## Repositories

| Repo | Role | Pinned commit | State |
|---|---|---|:--:|
| [graphed-project-mvp](https://github.com/graphed-org/graphed-project-mvp) | meta/superproject | — | meta |
| [graphed-mvp](https://github.com/graphed-org/graphed-mvp) | M2/M3 frontend | `b6ad6cc` | ✅ submodule |
| [graphed-awkward-mvp](https://github.com/graphed-org/graphed-awkward-mvp) | M3/M5 reference backend | `fc6daff` | ✅ submodule |
| [graphed-checkpoint-mvp](https://github.com/graphed-org/graphed-checkpoint-mvp) | M8 checkpoint/resume | `641a4af` | ✅ submodule |
| [graphed-core-mvp](https://github.com/graphed-org/graphed-core-mvp) | M1/M4/M7-contract/M8-plan | `c2a4660` | ✅ submodule |
| [graphed-corpus-mvp](https://github.com/graphed-org/graphed-corpus-mvp) | M0.5 requirements + fixtures | `825e62a` | ✅ submodule |
| [graphed-debug-mvp](https://github.com/graphed-org/graphed-debug-mvp) | M6 debug/tracebacks | `cd75ddb` | ✅ submodule |
| [graphed-exec-local-mvp](https://github.com/graphed-org/graphed-exec-local-mvp) | M7 reference executor | `6d17cf0` | ✅ submodule |
| [graphed-numpy-mvp](https://github.com/graphed-org/graphed-numpy-mvp) | M2 trivial backend | `d630002` | ✅ submodule |
| [graphed-orchestrator](https://github.com/graphed-org/graphed-orchestrator) | Part B deterministic orchestrator | `2caf95d` | ✅ submodule |
| [graphed-preserve-mvp](https://github.com/graphed-org/graphed-preserve-mvp) | M9 preservation bundle | `041fd0c` | ✅ submodule |

`lazy` repos are created when their milestone begins.

## Working with the submodules

```bash
# clone the whole project
git clone --recurse-submodules git@github.com:graphed-org/graphed-project-mvp.git
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

<sub>Generated from <code>.graphed/state.json</code> (updated 2026-06-16T23:02:41Z).</sub>
