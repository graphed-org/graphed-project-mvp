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

**41 of 41 milestones DONE — all CI-green on the §A.5 matrix.** Current milestone: **DONE**.

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
| **M10** | ✅ DONE | graphed-mvp, graphed-core-mvp, graphed-awkward-mvp, graphed-exec-local-mvp, graphed-orchestrator | Remediation of the mvp-shortcomings findings: IR-driven execution (compile_ir/evaluate_ir, one dispatch per REDUCED node), genuine incremental sessions (Session(incremental=True)), buffer-level projection, full A.5 CI matrices + build-only wheels + cargo llvm-cov, opt-in maximal fusion + pooled combines, Partition.blind, and an integrity scan that catches bare-pass targets |
| **M11** | ✅ DONE | graphed-mvp, graphed-numpy-mvp, graphed-awkward-mvp | dask.array parity P0: full ufunc tier + backend-idiom factorization (array_type; NumpyArray proxy; awkward stays functions-only) |
| **M12** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P1: axis-aware reductions/scans (boundary vs fusible structural rule), creation routines, deterministic random, tree-reducible monoids |
| **M13** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P2: indexing (slices/ints common; tuple subscripts numpy-side) + manipulation with axis-0 geometry rules + concatenate/unique/bincount/histogram* |
| **M14** | ✅ DONE | graphed-mvp, graphed-numpy-mvp | dask.array parity P3.8: graphed.apply multi-input blockwise externals + signature-aware apply_gufunc (P3.9 + P4 deferred to Phase 2 by user decision) |
| **M15** | ✅ DONE | graphed-mvp, graphed-awkward-mvp, graphed-numpy-mvp | Partitioned parquet I/O: backend-agnostic base in graphed (blind partitions, deferred write plans) + awkward specialization (schema-only forms, buffer-projection-wired writes) + numpy rectilinear specialization (R16.7 amended by user decision: parquet alone enters the numpy MVP) |
| **M16** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P0: full canonical ufunc tier on the awkward backend, the structural reduction rule on every reducer (name-based boundary classification retired), 13 new reducers |
| **M17** | ✅ DONE | graphed-mvp, graphed-awkward-mvp | dask-awkward parity P1: ~20 structure functions through the single apply dispatch + the common record-subset getitem (a[[fields]]) |
| **M18** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P2: behaviors — with_name + backend behavior registration; vector four-vectors record, evaluate, and project to exactly the leaves they read |
| **M19** | ✅ DONE | graphed-awkward-mvp | dask-awkward parity P3.8: fields/type_of/backend_of introspection (recording nothing), head/sample peeking, common slice/index ops on the awkward backend; __awkward_function__ dispatch and the rest stay Phase 2 by user decision |
| **M20** | ✅ DONE | graphed-mvp | Partitioned-write base: a format-agnostic graphed.write that client integrations specialize (parquet in the backends, ROOT in the reader fork) instead of borrowing parquet tools — a deferred write_plan with worker-reported paths, blind partition indexing, and exact step reconstruction |
| **M21** | ✅ DONE | graphed-awkward-mvp | Partitioned-source writer dispatch: the generic to_parquet writes any deferred array partition-wise via the graphed.write.PartitionedSource protocol (one read per partition tiling the dataset; the read list merges syntactic source-field accesses with buffer-projection refinement) |
| **M22** | ✅ DONE | graphed-mvp, graphed-core-mvp | Output-scoped compiles: graph outputs are a property of the compile REQUEST, not session/store state — fixes the compile_ir output-accumulation footgun; sequential compiles from one session/store are history-independent and byte-identical to fresh-session compiles |
| **M23** | ✅ DONE | graphed-mvp, graphed-histogram-mvp | Deferred histogram filling (graphed-histogram, the dask-histogram analogue): a histogram fill is a preservable External node; graphed gains record_external(descriptor=, form=) so backends stay domain-free |
| **M24** | ✅ DONE | graphed-awkward-mvp | gak <-> ak interface parity: every gak function mirrors awkward's signature and defaults (anti-drift pin over 38 functions), default-axis fixes, weighted moments, depth_limit zip, and combinations/cartesian/reducer parity |
| **M25** | ✅ DONE | graphed-preserve-mvp | Histogram fills are preservable Externals end-to-end (closing the M9<-M23 gap): build_bundle accepts histogram-terminal analyses directly (no value/weight/spec triple) and reproduce() returns the histogram bit-for-bit |
| **M26** | ✅ DONE | graphed-preserve-mvp | ML externals preserved end-to-end: an analysis with recorded ML inference (Triton remote via an injectable transport; XGBoost local-bytes) records -> build_bundle -> reproduce bit-for-bit, and a vanished server fails loudly at reproduce time |
| **M27** | ✅ DONE | graphed-preserve-mvp | Variadic call templates for the External family: the callee's real signature (multiple inputs, interleaved constants, named args, multiple axes/weights) becomes part of the preserved node and replay obeys it exactly (legacy no-args shape pinned byte-compatible) |
| **M28** | ✅ DONE | graphed-awkward-mvp | External-recording seam aligned with preservation (additive; M3 path untouched): content-identity hashing (not raw file bytes), args/kwargs call templates so record and replay agree by construction, and no filesystem-path leakage into the IR |
| **M29** | ✅ DONE | graphed-histogram-mvp | Multiple multiplicative weights are a first-class fill signature: fill(weight=[...]) records each weight as a graph input (params carry n_weights) and evaluation multiplies them elementwise; a single weight records exactly as before |
| **M30** | ✅ DONE | graphed-preserve-mvp | Producer cross-seam acceptance: Externals recorded through the real user surfaces (gak.apply_correction/gak.onnx_inference with call templates, Histogram.fill with multiple weights) pass build_bundle payload-integrity and replay bit-for-bit |
| **M31** | ✅ DONE | graphed-exec-local-mvp | Ship the process callable to each worker ONCE, not per task: the driver pickles the compiled-IR-bearing process once and broadcasts it (cached by content hash), submitting only (token, partition) per task — results and determinism unchanged |
| **M32** | ✅ DONE | graphed-core-mvp | The dependency-free reference executor lives with the execution contract: SequentialRunner and LocalResources move to graphed_core.execution beside Plan/Executor/WorkerResources (no longer accreted in a frontend write-format module) |
| **M33** | ✅ DONE | graphed-core-mvp | LocalResources is bounded and closeable: open_once's per-worker locality cache is LRU-bounded (eviction closes the handle) and close() releases all handles — no unbounded handle accumulation on a long-lived worker |
| **M34** | ✅ DONE | graphed-exec-local-mvp | Bounded shared-process cache + dedup: the M31 ship-once broadcast cache is FIFO-bounded in lockstep with the driver's token set (full worker coverage asserted before caching), reusing graphed-core's one bounded LocalResources |
| **M35** | ✅ DONE | graphed-mvp | Session.walk evaluates iteratively (explicit stack): a deeply-chained selection/systematics graph materializes far beyond Python's recursion limit instead of raising RecursionError (materialize and projection share walk) |
| **M36** | ✅ DONE | graphed-preserve-mvp | Model-parsing content hashes are memoized: memoized_model_hash caches the parse result by a cheap raw-bytes digest (bounded FIFO, keyed per (domain, bytes), cold in a fresh process) so a payload parses once, not per call |
| **M37** | ✅ DONE | graphed-core-mvp, graphed-exec-local-mvp, graphed-debug-mvp | Live execution dashboard (FINOS Perspective + websockets + a network transport): passive Monitor seam (graphed-core, unchanged), executor emit (graphed-exec-local), and graphed-debug's DashboardServer (perspective Server + Tornado) + NetworkMonitor (websocket, loopback or remote) + Dashboard + pyinstrument profile rows. Determinism gate green attached-or-not. Root prompt R20. (SSE/uPlot prototype on m37-sse-uplot.) |
| **M38** | ✅ DONE | graphed-core-mvp, graphed-exec-local-mvp | Inter-worker comms: a WorkerTransport seam (graphed-core) plus IPC/HTTP backends with peer tree-reduction and work-stealing (graphed-exec-local); peer is the default (comms='ipc') and reduces bit-for-bit identical to the hub path. Root prompt R21 |

The development process is a **gated three-role pipeline** (test-author → implementer → reviewer)
coordinated by the deterministic `graphed-orchestrator`. A milestone is `DONE` only when every
mechanical gate is green **and** the §A.5-matrix CI for the exact pinned commit is confirmed green —
the orchestrator refuses to record DONE off an unfinished CI run.

## Repositories

| Repo | Role | Pinned commit | State |
|---|---|---|:--:|
| [graphed-project-mvp](https://github.com/graphed-org/graphed-project-mvp) | meta/superproject | — | meta |
| [graphed-mvp](https://github.com/graphed-org/graphed-mvp) | M2/M3 frontend | `7ecd1a9` | ✅ submodule |
| [graphed-awkward-mvp](https://github.com/graphed-org/graphed-awkward-mvp) | M3/M5 reference backend | `58fe272` | ✅ submodule |
| [graphed-checkpoint-mvp](https://github.com/graphed-org/graphed-checkpoint-mvp) | M8 checkpoint/resume | `ed4907f` | ✅ submodule |
| [graphed-core-mvp](https://github.com/graphed-org/graphed-core-mvp) | M1/M4/M7-contract/M8-plan | `82519ef` | ✅ submodule |
| [graphed-corpus-mvp](https://github.com/graphed-org/graphed-corpus-mvp) | M0.5 requirements + fixtures | `65b20c4` | ✅ submodule |
| [graphed-debug-mvp](https://github.com/graphed-org/graphed-debug-mvp) | M6 debug/tracebacks | `62621c0` | ✅ submodule |
| [graphed-exec-local-mvp](https://github.com/graphed-org/graphed-exec-local-mvp) | M7 reference executor | `b4daf03` | ✅ submodule |
| [graphed-histogram-mvp](https://github.com/graphed-org/graphed-histogram-mvp) | M23/M29 deferred histogram filling | `9b0497b` | ✅ submodule |
| [graphed-numpy-mvp](https://github.com/graphed-org/graphed-numpy-mvp) | M2 trivial backend | `768d808` | ✅ submodule |
| [graphed-orchestrator](https://github.com/graphed-org/graphed-orchestrator) | Part B deterministic orchestrator | `30c959c` | ✅ submodule |
| [graphed-preserve-mvp](https://github.com/graphed-org/graphed-preserve-mvp) | M9 preservation bundle | `2d7542e` | ✅ submodule |

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

<sub>Generated from <code>.graphed/state.json</code> (updated 2026-06-19T02:59:56Z).</sub>
