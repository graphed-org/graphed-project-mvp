# `graphed` — Root Prompt

**What this document is.** A self-contained brief handed to an AI software architect to (1) produce a
gated, milestone-by-milestone project plan and (2) build, through that plan, a system called `graphed`.
It is the single source of truth: everything needed to design and execute the project is contained
here or in the public references it names.

It is organized so that **Part I (Rationale)** — the *why*, which is context and is non-binding — is
cleanly separated from **Part II (Requirements)** — the *what*, which is binding and written to be
specific and testable. **Part III (Glossary)** defines specialized terms.

Requirements use RFC-2119 keywords: **MUST / MUST NOT / SHOULD / MAY**. Each is identified as `R#.#`.
If Part I and Part II ever seem to disagree, Part II governs.

---

# PART I — RATIONALE (context; non-binding)

## 1. What `graphed` is and why it should exist

`graphed` is a schedulable, serializable, debuggable task-graph system for high-energy-physics (HEP)
analysis. It targets a gap between two unsatisfactory points in the design space:

- Systems that keep a complete, low-level task graph and optimize it late (the `dask` / `dask-awkward`
  approach). On real analyses with many systematic variations the graph reaches tens of thousands to
  hundreds of thousands of nodes, and graph *optimization itself* comes to dominate wall-clock time
  while consuming large amounts of local memory.
- Systems that react by discarding the schedulable graph entirely (a direction taken by the `coffea`
  framework). This regains speed but loses serializability, checkpointing, and reproducibility.

The intended middle path: **reduce the graph to a concise set of meaningful "stage" nodes incrementally,
as the user builds it,** so that a large un-reduced graph never exists, while keeping the graph as a
durable, schedulable, serializable artifact. A *stage* is a maximal fused run of array operations
between boundaries, where a boundary is a source, a reduction, a repartition, a materialize/checkpoint,
or an external/opaque operation. The goal is to minimize time spent in the Python interpreter and
maximize time spent inside array kernels (ragged-array kernels by default).

## 2. The failure modes this design must avoid

These pathologies have been observed in low-level-graph systems. Part II turns each into a constraint
or a guard.

1. The complete graph is built before reusable sub-components are optimized.
2. Intent is recorded operation-by-operation, producing many nodes irrelevant to the computation.
3. Graph optimization is slow and grows super-linearly, dominating wall time.
4. The graph plus its optimization consume large local memory.
5. Packaging of a heavy component (for example a neural network) for parallel execution is unclear.
6. Low-level graphs are so large that the interpreter itself is a cost.
7. Optimized graphs are so nested with sub-graph-execute calls that interpreter time is again a cost.
8. Remote/distributed tracebacks are opaque and do not point at the user's analysis line.

Complex graph **topologies** — diamonds (fan-out then re-converge), stars (fan-out/fan-in), and deeply
nested shapes with shared sub-DAGs — are classic failure points for graph optimizers: quadratic
blow-ups, common-subexpression elimination failing, dead-code elimination dropping a node reachable by
two paths, and re-execution of shared sub-graphs. They deserve dedicated, adversarial testing rather
than incidental coverage.

## 3. The HEP execution reality

- Data is **ragged / nested-tabular** (jagged arrays of records), not flat tensors.
- Inputs are columnar physics files, frequently on spinning disks; re-opening a file repeatedly is
  expensive, so work should be partitioned to favor one-file-per-worker locality, and straggling
  "tails" are acceptable in exchange for robustness.
- Compute runs on batch systems and increasingly wants **free-threaded Python** (no global interpreter
  lock) to exploit many cores without per-process overhead.
- Analyses carry **external payloads**: machine-learning models, scale-factor corrections, and
  systematic variations. These are first-class reproducibility hazards unless captured precisely.
- Adaptive execution — resizing work units based on small probe runs — and morsel-driven parallelism
  with tree reduction keep cores busy without a fixed, exhaustive task list.

## 4. Why these specific techniques

Rather than hand-roll, the design reuses established computer-science machinery: **equality saturation
over e-graphs** for canonicalization and cost-based fusion; the **logical-vs-physical, cost-based
optimizer** framing (the Volcano/Cascades tradition); **hash-consing/interning** for
dedup-on-construction (from which common-subexpression elimination follows for free); **abstract
type/shape evaluation** that reads only metadata, not event data; and **content-addressed memoization**
(the approach behind reproducible build systems) for checkpoint and resubmission. Reproducibility should
reuse the HEP community's existing serialization standards rather than invent new formats.

## 5. Why a gated, adversarial development process

An AI implementer will, if permitted, make a quality gate pass by weakening the thing the gate
measures. The development process is therefore adversarial by construction: the party that writes the
acceptance tests does not see the implementation; the implementer cannot alter the frozen tests; and a
reviewer judges what mechanical gates cannot. A deterministic coordinator — not a language model —
drives the workflow. A subtle and important consequence: "done" must be bound to the *exact committed
revision* being green on the *full* platform matrix, not to a local test run or an earlier revision,
because otherwise a milestone can be declared complete against results that do not correspond to the
code being shipped.

## 6. Why integrate with an established file reader

Synthetic in-memory arrays are enough to prove the graph machinery, but they cannot prove that the
system is usable. `graphed`'s value only appears when it reads **real physics files** along the path a
physicist would actually take. The community already has an established columnar reader for ROOT files
that exposes a deferred/lazy array backend (its `dask`-backed entry point). The lowest-friction way to
put `graphed` in physicists' hands is therefore to surface it **the same way that reader already
surfaces its existing lazy backend** — a parallel entry point with the same call shape — so adoption
requires no new vocabulary and the new backend is judged against a familiar baseline.

This integration is also the project's strongest regression test. Wiring `graphed` into the reader
means editing that library's public surface (its package entry points and writer). Testing `graphed`
in isolation cannot catch a regression those edits introduce into the *host library*. Running
`graphed` **inside the host reader's own full test suite** does. The integration must also exercise the
real deployable path — the reference process-pool executor and the native checkpoint/preservation
machinery — rather than a shortcut that merely mimics the deferred-backend feel (for example computing
in-process), which would give a false appearance of parity without testing what actually ships.

---

# PART II — REQUIREMENTS (binding; specific)

## R0 — Development process and integrity

- **R0.1** The project MUST be built as a **gated three-role pipeline**, milestone by milestone, driven
  by a **deterministic orchestrator** (a state machine, not a language model). The workflow MUST move a
  milestone through: pending → decompose → author tests → test-sanity → freeze → implement → review →
  done, with side states for test disputes, escalation, pause, and abort.
- **R0.2** The three roles MUST be isolated and communicate only through frozen artifacts:
  - **test-author** writes the acceptance suite; never sees or writes implementation.
  - **implementer** makes the frozen suite pass without weakening it; MAY add additional tests; MUST NOT
    edit any frozen test.
  - **reviewer** judges intent, guardrails, technique, and abstraction; MAY reject; MAY approve only
    when every mechanical gate is green.
- **R0.3** Before freezing, a **test-sanity** check MUST confirm the suite collects, is **non-vacuous**
  (it fails the unimplemented stub for the *right* reason), is deterministic across two runs, and has
  coverage instrumentation wired.
- **R0.4** Each implementer iteration MUST pass these **mechanical gates**: all frozen tests pass;
  **≥ 90 % line-and-branch coverage on new/changed lines**, with the covering hits coming from the
  *frozen* acceptance suite (not only from additional tests); linters clean; static type-checking clean
  in strict mode; **determinism** (identical input produces byte-identical optimized graphs and
  serialized plans across two runs); any defined performance benchmark within budget; and an automated
  integrity scan clean.
- **R0.5 (Completion-confirmation gate — MANDATORY).** A milestone MUST NOT be recorded done until the
  **exact revision pinned by the milestone's completion record** has been confirmed **green on the full
  CI matrix (R11.1)**. CI that is in progress, queued, or absent MUST count as *not green*. The
  orchestrator MUST hold the milestone in review (this is a normal waiting state, not an integrity
  violation) until the pinned revision is confirmed. Confirmation MUST be performed by a deterministic
  checker that polls the specific revision; ad-hoc shell polling loops MUST NOT be relied upon.
- **R0.6 (Integrity rules — NON-NEGOTIABLE; a violation pauses the run).** No party may: edit, delete,
  skip, mark-expected-failure, or otherwise weaken any frozen test; lower a coverage or benchmark
  threshold or relax a CI gate; stub, mock, or hard-code the specific thing a test verifies; leave a
  named implementation target as a bare not-implemented placeholder while reporting its test green; or
  blanket-apply type-checker suppressions, swallow-all exception handlers, or unjustified unsafe code.
- **R0.7** If a frozen test appears wrong, the implementer MUST NOT route around it; it MUST file a
  written **dispute** (recording the test, the requirement it contradicts, and a proposed correction)
  and stop. Honest incompleteness is preferable to a green gate obtained by cheating.
- **R0.8** Every implementer iteration MUST be logged to a per-milestone attempt record, and the
  reviewer's approval MUST be recorded. Stalls MUST escalate through the orchestrator's bounded-retry
  and escalation logic.
- **R0.9** Milestones MUST be built strictly in order; the next MUST NOT start until the current is done.

## R1 — System architecture and repository layout

- **R1.1** The graph — its intermediate representation (IR), interned store, optimizer, plan
  serialization, and execution protocol — MUST live in a **Rust core exposed to Python**. The core MUST
  NOT depend on any array backend (in particular, not on the ragged-array library).
- **R1.2** The system MUST be an **ecosystem of separately-built, separately-CI'd packages** with hard
  boundaries:
  - the Rust core (IR, optimizer, plan, execution protocol) — backend-free;
  - a **backend-agnostic frontend** (a deferred-array proxy plus a backend protocol), with no array-
    library types leaking into core types;
  - a reference **ragged-array** backend and a trivial **dense-array** backend that proves the seam;
  - a **debugging** package, a **local execution** package, a **checkpoint/resume** package, an
    **analysis-preservation** package, a **requirements/corpus** package, and the **orchestrator**.
- **R1.3 (Repository layout — choose explicitly).** The layout MUST be chosen deliberately and stated.
  RECOMMENDED: multiple repositories under one organization, with a meta/superproject that pins each
  package at a known-good revision. A single repository is acceptable only if every per-package
  obligation in R11 is still satisfied independently.
- **R1.4 (High-level project state is generated, never hand-written).** Any human-readable status
  summary of the overall project MUST be **generated from machine-readable state** by a script, kept in
  sync by a CI check that fails on drift, and produced through a single bookkeeping entry point that
  also advances the recorded package revisions.
- **R1.5** Each package MUST carry concise written guidance that defers to a single root guidance
  document, which in turn defers to this brief and the generated plan; the plan governs on conflict.

## R2 — Techniques that MUST be used (do not hand-roll alternatives)

- **R2.1** Graph reduction MUST use **equality saturation over e-graphs**, behind an internal optimizer/
  rewrite-engine interface so the engine is swappable. The initial engine MUST be an existing e-graph
  library, and **no engine-specific types may leak past the interface**. Replacing the engine with a
  more capable one (for example a Datalog-style e-graph engine) is a later-phase option and MUST NOT be
  built initially.
- **R2.2** Only **sound** rewrite rules may be enabled (for example commutativity and additive/
  multiplicative identities). Domain-dependent or potentially unsound rewrites MUST be excluded.
- **R2.3** **Dead-code elimination and common-subexpression elimination MUST live outside the rewrite
  engine.** Dead-code elimination is reachability from the graph's outputs. Common-subexpression
  elimination MUST follow from hash-consing at construction; it MUST be asserted, not re-derived.
- **R2.4** Node identity MUST be by **structural hash-consing/interning**: structurally identical nodes
  share one identifier, and repeated sub-expressions add zero new nodes. Floating-point values in node
  keys MUST hash with a total order and a canonical bit pattern (every NaN interns to a single value;
  positive and negative zero remain distinct at the IR level; numeric canonicalization is the
  optimizer's job, not the IR's).
- **R2.5** Type and shape inference MUST **reuse the ragged-array library's abstract (metadata-only)
  evaluation**, which infers forms and shapes without reading event data. It MUST NOT be reimplemented.
- **R2.6** Optimization MUST follow the **logical-vs-physical, cost-based** framing. Fusion,
  morsel-driven parallelism, and tree reduction are the execution-side techniques.
- **R2.7** Checkpoint and resubmission MUST use **content-addressed memoization**.
- **R2.8** The toolchain MUST target **free-threaded CPython** and build the Rust core with a current
  Python/Rust binding generator and wheel builder. The core MUST be safe to share across threads with a
  documented locking discipline, and its concurrency-critical section MUST be model-checked.

## R3 — Frontend and backends

- **R3.1** A user MUST be able to write ordinary deferred array expressions; a proxy records them into
  the core through a pluggable backend that supplies only form inference and evaluation. Backend
  independence MUST be provable: two backends produce an identical recorded graph and different results.
- **R3.2** Arbitrary user callables MUST be expressible as **external** nodes. Any genuinely opaque
  callable MUST be flagged as a preservation risk.
- **R3.3** Each node MUST carry **provenance** — filename, line, function, and the sub-expression source
  text — back to the user's analysis. An ill-typed operation MUST raise an error at the user's exact
  source line.

## R4 — Incremental optimizer and the anti-quadratic guard

- **R4.1** Reduction MUST run incrementally as the graph is built and MUST be deterministic
  (byte-stable output).
- **R4.2** A representative graph with on the order of ten thousand nodes (such as one produced by many
  systematic variations) MUST reduce to a number of nodes on the order of the number of stages in under
  one second.
- **R4.3 (The single most important performance guard.)** A CI benchmark MUST **fail if reduction time
  grows super-linearly** across a range of input sizes (for example 1k, 2k, 4k, 8k nodes). The benchmark
  MUST avoid timer-noise artifacts: the graphs MUST exhibit genuine growth (they MUST NOT accidentally
  intern to a constant size), the sizes MUST be large enough that the base case takes a measurable time
  (at least on the order of milliseconds), and the benchmark SHOULD assert that floor explicitly.
- **R4.4** Semantic equivalence of the reduced and un-reduced graphs MUST be proven (for example by a
  small reference interpreter in the core's test suite). Full equivalence against a real backend
  executor is proven at the execution milestone.

## R5 — Necessary-buffer (column) projection

- **R5.1** Each backend MUST compute the **minimal set of input buffers/columns** the recorded graph
  requires. A trivial "read everything" implementation is NOT acceptable for any backend, including the
  dense-array backend, which MUST implement a genuine field-touch projection.
- **R5.2 (Over-reading protection — mandatory tests.)** Tests MUST prove no **over-touching** (reading
  more buffers than the computation needs): reading one column reads only that column; a selection such
  as "the eta of jets with pt > 30" reads exactly the jet pt and jet eta buffers and never a sibling
  column. Projection MUST be correct whether or not the graph has been reduced.
- **R5.3** Predicate pushdown is out of scope for the initial system.

## R6 — Debugging, lowering, and source-mapped errors

- **R6.1** A zero optimization level MUST be a one-to-one operation-to-node lowering; higher optimization
  levels MUST fuse operation-runs between boundaries while every operation retains exact provenance, so
  the same error points at the same user line at any optimization level.
- **R6.2** A stage or operation failure MUST be raised as a **serializable** error carrying the failing
  operation, the user source-frame chain, the input forms, and the partition, all as plain data — so it
  survives a process boundary intact and is re-raised pointing at the user's analysis line (this
  addresses failure 8 in §2). It MUST NOT degrade to an opaque string.
- **R6.3** A deterministic **visualizer** MUST render the task graph, including provenance and the
  projected columns.

## R7 — Execution layer

- **R7.1** The core MUST own a minimal, data-only **execution contract** (executor, plan, task,
  partition, stop-condition, result). Reference executors live in the local-execution package.
- **R7.2 (Both executors required.)** The reference package MUST provide **both a thread-pool executor
  and a process-pool executor** behind one contract.
- **R7.3** A plan MUST reduce to a single result via a **deterministic, straggler-tolerant tree
  reduction**: a fixed combine-tree keyed by leaf order yields bit-for-bit results regardless of
  completion order, and one slow leaf blocks only its own path.
- **R7.4** Work MAY be a fixed task set or be pulled adaptively from a generator with **stopping
  conditions** (target events, wall-clock time, target precision, or an error budget). Adaptive
  reshaping (resizing work units based on observed behavior) MUST be supported.
- **R7.5** **File locality** MUST be honored: a given input is opened at most once per worker;
  partitioning SHOULD favor one-file-per-worker; straggling tails are acceptable.
- **R7.6** Under thousands of tiny tasks there MUST be no deadlock, stall, or race, verified including
  under free-threaded Python. A failure on a remote worker MUST surface to the driver via R6.2.
- **R7.7** Concurrency safety MUST be tested with real concurrency (threads and processes), not mocked.

## R8 — Checkpoint, resume, and error harvesting

- **R8.1** Plan serialization MUST be **versioned and deterministic**: an identical plan serializes to
  byte-identical output. The **canonical durable form is the serializable IR**, never a pickled Python
  object — except for a genuinely opaque callable, which MUST be tagged as a preservation risk.
- **R8.2** A plan MUST carry the columns to read, the partitions, the reduction specification, the
  stopping conditions, the file-locality hints, and the resource hints, plus a **content-addressed task
  identifier** (a hash over the computation's identity and the partition) that is safe against cache
  poisoning.
- **R8.3** A **content-addressed store** (local filesystem only initially) MUST provide atomic writes (no
  torn objects), an append-only manifest/journal, and a record of failed work. Resume MUST be correct
  under partial or interrupted writes: **no double counting and no lost partition**, the resumed result
  MUST equal an uninterrupted run **bit-for-bit**, and the resumed run MUST do **measurably less work**
  with skipped work logged.
- **R8.4** Error harvesting MUST record a failed partition as a reproducible descriptor (including the
  R6.2 provenance) and MUST support recovery policies: retry-n-times, retry-with-a-smaller-chunk,
  retry-elsewhere, and quarantine — with an **error budget** as a stopping condition. Retry-with-a-
  smaller-chunk MUST succeed where a whole-chunk attempt exhausted memory (which may be simulated).
- **R8.5** A serialized plan MUST run on a machine with **no user source files present** (proven by test).

## R9 — Analysis-preservation bundle

- **R9.1** A `build_bundle(graph, environment, datasets)` operation MUST capture: the canonical
  serializable IR; the source-mapped provenance; every external payload descriptor; auxiliary payloads
  by content hash in the content-addressed store (small ones MAY be embedded, large ones MUST be
  referenced and MUST NOT be inlined into the manifest); input dataset identifiers and per-file content
  hashes; the software environment (a lockfile and/or a container digest); configuration and random
  seeds; and a top-level **manifest** binding every component by hash. The manifest's own hash is the
  **bundle fingerprint**.
- **R9.2** A `reproduce(bundle)` operation MUST re-instantiate and run from references alone, producing
  the analysis results **bit-for-bit on a clean machine that has no access to the original code,
  environment, author, or input files** (inputs resolved only through content-addressed references). A
  missing referenced payload MUST fail with a precise "unresolved payload `<hash>`" error — never a
  silent wrong result.
- **R9.3** The bundle MUST be **self-fingerprinting**: changing any result-determining input (a
  correction set, model weights, a dataset file, a configuration value, a random seed, or the
  environment) MUST change the fingerprint, and changing nothing MUST reproduce an identical fingerprint.
  The fingerprint MUST NOT be sensitive to irrelevant inputs; in particular the manifest MUST NOT contain
  timestamps, absolute paths, or host names.
- **R9.4** An `inspect(bundle)` operation MUST render the analysis logic (the IR plus source-mapped
  provenance), list every external payload with its descriptor, and flag every opaque node as a
  preservation risk — **without executing anything**. `inspect` MUST be faithful to what `reproduce`
  runs (the same IR; no drift between the auditable view and the executed graph).
- **R9.5 (Externals are an extensible, validated plugin system — not a hardwired list.)** An external
  *kind* MUST be definable by a plugin that provides: a deterministic, content-based content hash; an
  evaluation function; an optional load/close resource lifecycle; and example payloads for validation.
  - **R9.5.1** A plugin's content hash MUST hash the **meaningful content**, not the raw file bytes. For
    a machine-learning model the hash MUST cover its weights (and graph structure); for a correction set
    the hash MUST cover its contents. Incidental formatting or metadata MUST NOT change the hash.
  - **R9.5.2** Plugin registration MUST **validate the hash function**: it MUST reject a hash that is not
    **deterministic across processes** (verified by hashing the same payload in fresh subprocesses,
    which catches any hash derived from process-local randomness, object identity, or wall-clock time)
    and one that is **vacuous** (distinct payloads colliding to one value, as a constant hash would).
  - **R9.5.3** `build_bundle` MUST verify that each stored payload hashes to its recorded identifier
    (safe against cache poisoning). A resource — a loaded model or a remote connection — MUST be loadable
    **once per worker** and released at the end of a run. The same evaluator MUST be used at build time
    and at reproduction so results match bit-for-bit.
  - **R9.5.4** Plugins for the standard external kinds (a model format and a correction format) MUST ship
    and MUST double as templates a user can follow to add their own external kinds.
- **R9.6** The preservation store is local-filesystem only initially. Analysis preservation (a portable,
  self-describing scientific artifact) is distinct from checkpoint/resume (same-environment execution
  portability); both are required, and both build on the content-addressed store.

## R10 — Standards (reuse; invent no formats)

- **R10.1** The system MUST reuse the HEP community's existing serialization standards rather than invent
  new ones: corrections in the standard correction-library JSON format; models in the open neural-network
  exchange format (ONNX); histograms via the unified histogram interface (UHI); statistical models, if
  any, in the HEP statistics serialization standard (HS3); the software environment as a container digest
  and/or lockfile; and datasets identified by stable IDs plus content hashes. Export to external
  analysis-preservation portals is a later-phase concern.

## R11 — Build matrix, packaging, and documentation (per-package baseline)

- **R11.1 (Matrix.)** CI MUST cover operating systems {Linux, macOS, Windows} × architectures
  {x86_64, arm64} × a set of currently-released CPython versions, and MUST include a free-threaded
  (no-GIL) build where one is officially released. Free-threaded builds that are only experimentally or
  intermittently shipped MUST NOT be in the blocking matrix. Rust-backed packages MUST build stable-ABI
  wheels where possible plus a dedicated free-threaded wheel, with a pinned and tested minimum Rust
  version. Bleeding-edge rows MAY be marked non-blocking where upstream wheels lag.
- **R11.2** Every package MUST ship: per-package CI (lint, types, and tests on the matrix), wheels, a
  release workflow, a documentation build that **passes with warnings treated as errors** and includes
  class-inheritance diagrams and a tracked "improvements/known-limitations" page, and a contributor
  guide that encodes the integrity rules and the local gate commands.
- **R11.3** Code MUST be highly readable — descriptive names and expository comments — and MUST conform
  to standard Python and Rust style and lint rules, modeled on well-regarded open-source codebases. CI
  MUST enforce style.

## R12 — Determinism and reproducibility gates (cross-cutting)

- **R12.1** Identical input MUST produce byte-identical optimized graphs and serialized plans across
  runs.
- **R12.2** Result reproduction MUST be **bit-for-bit** wherever it is claimed (chunked versus
  single-pass; interrupted-and-resumed versus uninterrupted; one machine versus another). Cross-platform
  floating-point stability MUST be managed explicitly (for example by rounding stored reference values to
  a fixed number of decimals), and any platform-specific mismatch MUST be fixed by adjusting the
  tolerance or rounding, never by skipping the test.

## R13 — Testing requirements (cross-cutting; in addition to per-milestone suites)

- **R13.1 (Topologies.)** Every package that touches the graph MUST test **diamond, star, and
  deeply-nested shapes with shared sub-DAGs**, asserting that a shared apex is interned and evaluated
  exactly once, that dead-code elimination keeps a node reachable by two paths, that reduction is
  sub-quadratic, and that projection reports each column exactly once.
- **R13.2 (Deep integration, not only unit tests.)** A graded set of realistic analysis tasks MUST be
  exercised end-to-end — recorded through the frontend, executed per partition through **every**
  executor, tree-reduced, and asserted **bit-for-bit** against a reference computed directly with the
  array library. This is a deeper level of integration than per-operation unit tests and is required.
- **R13.3 (Non-vacuity.)** Acceptance suites MUST be non-vacuous (they fail the stub for the right
  reason) and MUST assert that real signal exists (for example that a histogram actually fills bins).
- **R13.4 (Real external services and frameworks where feasible.)** Where an external dependency can be
  stood up in CI, it MUST be exercised for real, not only mocked. In particular, the external-plugin
  system MUST be validated against real machine-learning frameworks (for example a tensor framework and a
  gradient-boosted-trees framework) and against a **real model-inference server** running in a CI
  container, exercised over **more than one transport** (for example gRPC and HTTP).
- **R13.5 (Deployment ergonomics.)** The "**compile once, run on many datasets**" pattern MUST be a
  tested, first-class capability: a recorded-and-optimized analysis serialized once and re-targeted at
  many datasets without re-recording, with per-dataset content-addressed identities so a single store
  can hold them all without collision.
- **R13.6 (Timing tests.)** Any wall-time or scaling assertion MUST include a noise-floor sanity check
  (R4.3) and use sizes large enough to be meaningful; it MUST NOT assert on sub-millisecond timings.

## R14 — Deliverables and milestone shape

- **R14.1** A **Required Operations Catalog** plus runnable **canonical-analysis fixtures** MUST be
  produced first, extracted from real public analyses (not invented). Each catalog entry MUST be tagged
  with the analysis it came from and the milestone that must support it; anything not supportable
  initially MUST be recorded as later-phase with a rationale, never silently dropped. The fixtures MUST
  include a graded set of analysis-benchmark queries, a reduced end-to-end ttbar-style analysis that
  exercises a machine-learning model, scale-factor corrections, and systematic variations, and a second
  selection-plus-corrections-plus-systematics slice, each producing a stored reference histogram for
  bit-for-bit comparison.
- **R14.2** The plan MUST be expressed as **per-milestone agent-prompts** detailed enough for a
  less-capable model to execute: each with explicit implementation targets, an acceptance contract, a
  review focus, and an iteration budget.
- **R14.3** The public reference material to study (extract from it; do not imagine it) MUST include: a
  standard set of HEP analysis-description benchmark queries and a community benchmark implementation
  whose history quantifies the node-count explosion `graphed` must avoid; a CMS-Open-Data ttbar
  end-to-end "analysis grand challenge"; a teaching-grade full analysis exercise covering selection,
  scale factors, and systematics; a declarative analysis framework; and at least one production-scale
  analysis using substructure and corrections.
- **R14.4** A **graph-bloat note** MUST quantify the node-count explosion of the late-optimization
  approach, to set the reduction targets and the R4.3 benchmark.

## R15 — Integration with an established file reader (real-reader integration and regression)

- **R15.1 (Surface `graphed` through an established reader.)** `graphed` MUST be wired into the
  community's established columnar HEP file-reading library and surfaced as a **deferred backend
  alongside that library's existing lazy backend**, mirroring its call shape: a deferred **read** entry
  point and a deferred **write** entry point that parallel the library's existing lazy
  (`dask`-backed) ones. The integration MUST reuse the host library's own internals — file/path
  regularization, key filtering, and metadata/form inference — and MUST NOT reimplement them.
- **R15.2 (Isolation; not an upstream contribution.)** The integration MUST live on an **isolated
  branch of a fork**; it is an MVP demonstration and MUST NOT be proposed upstream (no pull request to
  the host project). It MUST be gated through the same orchestrator pipeline (R0) as every other
  milestone, with its own frozen acceptance suite.
- **R15.3 (Deferred reading.)** The read entry point MUST return a **deferred `graphed` array built
  from metadata/form alone** — no event data read at construction. Partitioning MUST support an
  explicit per-file step size, a steps-per-file count, and a **blind** mode that defers entry-range
  resolution to read time (partitions describe their range symbolically without opening files up
  front; the range is resolved when the partition is read). Necessary-buffer projection (R5) MUST
  report exactly the minimal columns the recorded graph requires.
- **R15.4 (Deferred writing.)** The write entry point, with compute **disabled**, MUST return a
  **task graph of write tasks** — each returning nothing and writing its own output partition — **not**
  an array. With compute **enabled** it MUST execute that task graph through a real reference executor
  (R7): the **process-pool executor by default**, with the thread-pool executor selectable. The two
  modes MUST be consistent (the disabled mode's graph, when run, produces the enabled mode's outputs).
- **R15.5 (Exercise the real deployable path.)** Integration analyses MUST be executed through the
  **reference executors of R7 (the process-pool executor)**, not through a direct in-process
  materialize shortcut, so the path under test is the path that ships. Error-harvesting/report-style
  behavior and resume MUST be expressed with the **native checkpoint machinery (R8)** and its
  semantics (content-addressed dead-letter set, resume that skips completed work, error budget) — they
  MUST NOT emulate the host reader's own report semantics.
- **R15.6 (Compile once, run on alternate inputs — demonstrated here.)** The compile-once/run-on-many
  capability (R13.5) MUST be demonstrated through this integration: a plan recorded against one input
  MUST run **unchanged** against a **different file location** and a **different partition count**, with
  the IR proven identical across the re-targetings and the result proven equal to a single-pass
  reference.
- **R15.7 (Regression coverage — the host suite runs too.)** CI for the integration branch MUST run
  the **host library's full existing test suite together with** the `graphed` integration tests, so a
  regression introduced by the integration's edits to the host library's public surface is caught — not
  only the `graphed` tests in isolation. The integration tests MUST follow the host library's own test
  conventions (its fixtures, data-fetching helpers, markers, and dependency groups) and MUST use the
  library's **real data fixtures** where provided. Tests requiring an external service the lightweight
  CI job does not provision (for example a remote-storage protocol server) MAY be **deselected** by
  marker, but MUST NOT be deleted, skipped in source, or otherwise weakened (R0.6).

## Out of scope (later phases — MUST NOT be built initially)

Distributed-scheduler executors for specific batch systems; treating systematic variations as a graph
axis; advanced adaptive reshaping; predicate pushdown; interactive debugging or time-travel; export to
external analysis-preservation portals; swapping the optimizer engine for a more capable one behind the
engine interface; distributed (non-local) checkpoint stores; self-hosting preservation bundles that
embed and launch a model-inference server; and **upstreaming or production-hardening the host-reader
integration** (it remains an isolated MVP demonstration branch — see R15.2).

---

# PART III — GLOSSARY

- **Task graph / IR.** The intermediate representation of an analysis as a directed acyclic graph of
  typed operations on arrays.
- **Stage.** A maximal fused run of array operations between boundaries; the unit `graphed` reduces the
  graph down to. **Boundary:** a source, a reduction, a repartition, a materialize/checkpoint, or an
  external/opaque operation.
- **Ragged / nested-tabular array.** A jagged array (variable-length lists, records, and nesting), as in
  per-event lists of particle records — the dominant HEP data shape.
- **Abstract (metadata-only) type evaluation.** Inferring the type/shape ("form") of every node by
  running the graph on metadata placeholders, without reading any event data.
- **e-graph / equality saturation.** A data structure that compactly represents many equivalent forms of
  an expression, and an optimization method that grows the set of equivalences under rewrite rules and
  then extracts the best form by cost.
- **Hash-consing / interning.** Giving structurally identical nodes a single shared identity at
  construction time, so duplicates are never stored.
- **Dead-code elimination (DCE).** Removing nodes not reachable from the graph's outputs.
- **Common-subexpression elimination (CSE).** Collapsing repeated identical sub-expressions to one node;
  here a free consequence of hash-consing.
- **Logical-vs-physical, cost-based optimization.** Separating *what* to compute from *how*, and choosing
  the physical plan by estimated cost.
- **Morsel-driven parallelism.** Splitting work into many small units ("morsels") consumed by a worker
  pool to keep all cores busy.
- **Tree reduction.** Combining partial results pairwise up a tree so the final reduction order is fixed
  and a slow leaf delays only its own branch.
- **Content-addressed store / memoization.** Storing each artifact under a hash of its content, so
  identical work is recognized and skipped and references cannot be poisoned.
- **External / external payload.** A node wrapping a non-array computation (a model, a correction set, an
  arbitrary callable) together with the metadata needed to identify and reproduce it.
- **Provenance / sourcemap.** The mapping from each node back to the user-source location (file, line,
  function, expression text) that created it.
- **Free-threaded CPython.** A build of Python without the global interpreter lock, allowing true
  multithreaded parallelism in-process.
- **Stable-ABI wheel.** A compiled Python wheel compatible across multiple interpreter versions; a
  free-threaded build needs its own dedicated wheel.
- **Bit-for-bit / byte-identical.** Exactly equal outputs (no tolerance), the strict form of determinism
  required for the optimized graph, serialized plans, and reproduced results.
- **Analysis-benchmark / analysis-description queries.** A standard, graded set of HEP analysis tasks
  (column histograms through object combinatorics) used as a functional-correctness ladder.
- **ttbar "analysis grand challenge".** A community end-to-end reference analysis on open collider data,
  notable for combining a machine-learning model, corrections, and systematic variations.
- **Correction-library format / ONNX / UHI / HS3.** The community standards for, respectively,
  scale-factor corrections (a JSON schema), neural-network model exchange, the unified histogram
  interface, and serialization of statistical models.
- **Dead-letter record.** An append-only log of work that failed, with a reproducible descriptor, so a
  poison input is recorded rather than lost.
- **Host reader / deferred backend of a reader.** The community's established columnar HEP file-reading
  library that `graphed` is integrated into, and the lazy/deferred array entry point it already exposes
  (its `dask`-backed interface) that the `graphed` integration parallels.
- **Blind partitioning.** A partitioning mode whose partitions describe their entry range symbolically
  and defer resolving it (opening the file to learn the entry count) until read time, so no files are
  opened when the partitions are formed.
