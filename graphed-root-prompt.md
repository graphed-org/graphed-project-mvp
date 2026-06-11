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

A second, subtler failure mode was observed in practice and motivates R0.10: the **semantic stub**.
An "incremental reduce" was once shipped as a one-line alias for the full reduce — it passed its test
because the test asserted only *equivalence of results*, a property an alias satisfies by
construction. No body-scanning detector catches this, and a reviewer missed it. The defense is in the
tests themselves: when a requirement names a property of *how* something is computed (incrementality,
fusion actually driving execution, work proportional to a delta), the acceptance suite must pin a
**witness** that only the genuine mechanism can produce — a work counter, a dispatch count, an
off-thread observation — not merely the input/output behavior.

## 6. Why integrate with an established file reader

Synthetic in-memory arrays are enough to prove the graph machinery, but they cannot prove that the
system is usable. `graphed`'s value only appears when it reads **real physics files** along the path a
physicist would actually take. The community's established columnar reader for ROOT files is
**`uproot`**, which exposes a deferred/lazy array backend (its `dask`-backed entry point). The
lowest-friction way to put `graphed` in physicists' hands is therefore to surface it **the same way
`uproot` already surfaces its existing lazy backend** — a parallel entry point with the same call shape
— so adoption requires no new vocabulary and the new backend is judged against a familiar baseline.
ROOT files store columnar event data in two on-disk container formats — the long-established **TTree**
and its successor **RNTuple** — and a physicist's files may use either; an integration that handled only
one would not be usable, so both must be covered.

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
  The automated integrity scan MUST detect placeholder **bodies**, not only raise-statements: a named
  implementation target whose entire body is a bare `pass`/ellipsis is a violation, while a bare body
  in un-named helper, protocol, or exception code is legitimate and MUST NOT be flagged.
- **R0.7** If a frozen test appears wrong, the implementer MUST NOT route around it; it MUST file a
  written **dispute** (recording the test, the requirement it contradicts, and a proposed correction)
  and stop. Honest incompleteness is preferable to a green gate obtained by cheating.
- **R0.8** Every implementer iteration MUST be logged to a per-milestone attempt record, and the
  reviewer's approval MUST be recorded. Stalls MUST escalate through the orchestrator's bounded-retry
  and escalation logic.
- **R0.9** Milestones MUST be built strictly in order; the next MUST NOT start until the current is done.
- **R0.10 (Witness tests against semantic stubs).** When a requirement names a property of *how*
  something is computed — incrementality, fused execution, work bounded by a delta — the frozen suite
  MUST pin a **mechanism witness** that a pass-through alias or re-derivation cannot satisfy (for
  example: a cumulative work counter equal to the node count regardless of how many steps fed it; a
  backend dispatch count equal to the *reduced* operation count; a combine observed off the driver
  thread). Asserting only input/output equivalence for such a requirement is a test-sanity failure:
  an alias for the non-incremental path satisfies equivalence by construction (see Part I §5).

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
- **R2.2** Only **sound** rewrite rules may be enabled. Domain-dependent or potentially unsound
  rewrites MUST be excluded. Within that constraint the rule set MUST NOT stop at a token pair of
  arithmetic operators: commutativity MUST cover **every symmetric operator in the frontend's
  recorded vocabulary** (addition, multiplication, the boolean conjunction/disjunction, equality and
  inequality, elementwise minimum/maximum, …), plus the additive/multiplicative identities — a rule
  set that fires on nothing a real analysis records optimizes nothing. The symmetric-operator list
  and the identity rules MUST be defined in **one shared constant** consumed by every reduction path
  (the saturation engine and any incremental canonicalizer), so the paths provably agree
  node-for-node. Asymmetric operators (subtraction, division, ordering comparisons) MUST be tested to
  NOT merge under commutation.
- **R2.3** **Dead-code elimination and common-subexpression elimination MUST live outside the rewrite
  engine.** Dead-code elimination is reachability from the graph's outputs. Common-subexpression
  elimination MUST follow from hash-consing at construction; it MUST be asserted, not re-derived.
- **R2.4** Node identity MUST be by **structural hash-consing/interning**: structurally identical nodes
  share one identifier, and repeated sub-expressions add zero new nodes. Floating-point values in node
  keys MUST hash with a total order and a canonical bit pattern (every NaN interns to a single value;
  positive and negative zero remain distinct at the IR level; numeric canonicalization is the
  optimizer's job, not the IR's). Any **string encoding derived from a node's identity** — operator
  tokens fed to the rewrite engine, parameter encodings — MUST be genuinely **injective and losslessly
  invertible**, with separator characters escaped: two distinct parameter maps colliding onto one
  token can silently rebuild a node with the wrong parameters. Injectivity MUST be tested with
  hostile inputs (string parameter values containing the separator characters).
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
  (byte-stable output). **Incrementality MUST be genuine, not an alias for the one-shot reduce**
  (the alias was actually shipped once and passed an equivalence-only test — see Part I §5 / R0.10):
  - **R4.1.1** The builder MUST maintain a canonical (identity-eliminated, commutativity-deduped,
    hash-consed) view of the graph **as nodes are recorded**, applying the SAME shared rule set as
    the saturation engine (R2.2) constructor-locally, so each new node's canonical form depends only
    on its inputs' already-canonical forms.
  - **R4.1.2 (Witness — required by R0.10.)** Per-step work MUST be proportional to the **delta**
    (the nodes recorded since the previous step), never to the history; a cumulative work counter
    MUST be exposed and the frozen suite MUST assert it equals the total node count regardless of how
    many steps fed it.
  - **R4.1.3** Finishing the reduction from the maintained view MUST cost one linear pass over the
    canonical form and MUST produce output **byte-identical** to the one-shot reduce of the same
    recording.
  - **R4.1.4** The incremental mode MAY be opt-in at the session level, but the compile path of an
    incremental session MUST actually consume the maintained view (no silent fallback to a
    whole-history optimization at the end).
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
- **R4.5 (Fusion maximality.)** Single-use fusion (an operation fuses only into its sole consumer) is
  an acceptable, conservative default, but a **maximal** fusion mode MUST also be provided: a fan-out
  operation fuses when **all** of its consumers are operations landing in one stage, so a diamond
  inside an operation region becomes ONE stage with the apex as a shared member (computed once, never
  duplicated). Neither mode may ever fuse across a boundary; both MUST be deterministic and MUST
  evaluate to identical results. If the default is pinned by a frozen suite, the maximal mode MUST be
  opt-in rather than a silent behavior change.
- **R4.6 (Fused stages MUST be executable.)** The reduced graph's introspection surface MUST expose
  each fused stage's member operations as decoded, executable records — operation name, typed
  parameters, and resolved member/input references — and these MUST survive the durable codec (R8.1)
  round trip. A stage that can only report its member *count* cannot be executed from the IR, which
  silently forces executors back onto the un-reduced recording (the failure R7.8 exists to prevent).

## R5 — Necessary-buffer (column) projection

- **R5.1** Each backend MUST compute the **minimal set of input buffers/columns** the recorded graph
  requires. A trivial "read everything" implementation is NOT acceptable for any backend, including the
  dense-array backend, which MUST implement a genuine field-touch projection.
- **R5.2 (Over-reading protection — mandatory tests.)** Tests MUST prove no **over-touching** (reading
  more buffers than the computation needs): reading one column reads only that column; a selection such
  as "the eta of jets with pt > 30" reads exactly the jet pt and jet eta buffers and never a sibling
  column. Projection MUST be correct whether or not the graph has been reduced.
- **R5.3 (Buffer granularity, not only column granularity.)** Projection MUST also be available at the
  granularity of the buffers that compose a ragged array, distinguishing a **data** need (the leaf
  values are read) from a **structure-only** need (only the list offsets / index / option masks are
  needed — a multiplicity, a mask). The abstract-evaluation report already carries this distinction
  (touched-data versus touched-shape, per structural node); the projection MUST NOT discard the
  shape half or the non-leaf nodes.
  - **R5.3.1 (The count-only case is the acceptance pin.)** A count-only analysis (for example "the
    number of electrons per event") MUST project to a **non-empty structure-only need** on the
    counted collection. At column granularity this case necessarily collapses to the empty set —
    which is not merely inefficient but **wrong** if fed to a reader (zero buffers read, garbage
    result); the buffer view exists to make that case truthful.
  - **R5.3.2 (Consistency.)** Collapsing the buffer-level view to columns (keep the data-bearing
    entries) MUST reproduce the column-level projection exactly, pinned by a test over a shared
    expression corpus, so the two granularities can never drift apart. A data need subsumes its own
    structure; a redundant structure-only entry for a column whose data is read MUST NOT be emitted.
  - **R5.3.3** A reader integration MUST be able to **serve** a structure-only need more cheaply than
    a full column read where the format allows it (a TTree jagged branch's counter branch; an RNTuple
    index column) — see R15.8.
- **R5.4** Predicate pushdown is out of scope for the initial system.

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
  completion order, and one slow leaf blocks only its own path. Combines MUST be schedulable onto the
  **same worker pool as the leaves** (at least as an option): with combines pinned to the driver
  thread, the driver becomes a serial bottleneck for heavy partials. The pooled mode MUST use the same
  fixed combine-tree (bit-identical results, pinned by a tree-shape-capturing combine) and the frozen
  suite MUST observe a combine executing off the driver (R0.10 witness: a thread identifier or worker
  process id collected through the combine itself).
- **R7.4** Work MAY be a fixed task set or be pulled adaptively from a generator with **stopping
  conditions** (target events, wall-clock time, target precision, or an error budget). Adaptive
  reshaping (resizing work units based on observed behavior) MUST be supported.
- **R7.5** **File locality** MUST be honored: a given input is opened at most once per worker;
  partitioning SHOULD favor one-file-per-worker; straggling tails are acceptable.
- **R7.6** Under thousands of tiny tasks there MUST be no deadlock, stall, or race, verified including
  under free-threaded Python. A failure on a remote worker MUST surface to the driver via R6.2.
- **R7.7** Concurrency safety MUST be tested with real concurrency (threads and processes), not mocked.
- **R7.8 (The reduced serialized IR is what executes — the central anti-dask requirement at run
  time.)** A **compile** step MUST reduce the recorded graph once and produce a self-contained,
  serializable, picklable compiled artifact (the canonical IR bytes plus the source names it reads).
  Workers MUST evaluate that artifact directly: deserialize once per worker, then **one backend
  dispatch per *reduced* node** (fused stage members evaluated inline via R4.6) — **no per-partition
  re-recording, no build-session in the worker, no form re-inference**. Re-recording the analysis per
  partition re-introduces failures 2/6/7 of §2 on exactly the path that ships. Sources MUST bind by
  name (to data or a zero-argument loader); opaque external payloads are not embedded in the IR and
  MUST resolve through an explicit mapping keyed by payload content hash, failing loudly when one is
  missing. The frozen suite MUST pin (R0.10): evaluation from the compiled bytes alone with no
  recording in scope; the dispatch count equal to the reduced — not the recorded — operation count;
  and retargeting the same artifact at different inputs without recompiling.
- **R7.9 (Blind partitions are first-class.)** A partition whose entry range is deliberately unknown
  until read time MUST be representable **explicitly** on the partition type — carrying its step
  index and step count, resolvable against the file's actual entry count such that every entry is
  read exactly once across a file's steps — and MUST survive pickling and the durable plan codec.
  Encoding "blind" by smuggling a sentinel through an unrelated field (for example a negative entry
  stop) is FORBIDDEN: any consumer unaware of the convention silently misreads the range.

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
- **R8.6 (Outputs are a property of the COMPILE REQUEST.)** Compiling/serializing an analysis
  MUST scope the artifact to exactly the outputs of THAT request — never to accumulated
  session/store state — so sequential compiles of different expressions from one session are
  independent and BYTE-IDENTICAL to fresh-session compiles (pinned), deliberate multi-output
  requests carry every requested output, and concurrent compiles of different outputs from one
  shared store cannot cross-talk. The core reduce/serialize/finalize surfaces take the output
  set explicitly; there is NO public output mutator on the store — outputs exist only in compile
  requests and in the artifacts those requests produce (a reduced/deserialized store carries the
  outputs its request named).

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
  - **R11.2.1 (Wheels are built BY ordinary CI, published only by a human act.)** Wheel/sdist
    artifacts MUST be **built and validated on every push** for every matrix target (the Rust core:
    per-interpreter wheels on each OS/arch including the dedicated free-threaded wheel, each
    smoke-imported after install) and uploaded as CI artifacts. **Nothing triggered by a branch push
    or pull request may publish to any package index**; publishing MAY exist only behind an explicit
    human release act (a version tag to a staging index, a published release to the real index),
    behind protected environments. Where a hosted architecture runner does not exist, a fat/universal
    or cross-compiled wheel satisfies the target; an uncoverable target MUST be recorded as a known
    limitation, never silently dropped.
  - **R11.2.2 (Workflow drift guard.)** The superproject MUST carry an automated check, run in its own
    CI over the pinned package revisions, asserting that every package's workflows still cover the
    R11.1 matrix, still build wheel artifacts, and contain **no publish step reachable from push/PR
    CI**. A package weakening its own matrix must fail the *superproject's* build even while its own
    CI stays green.
- **R11.3** Code MUST be highly readable — descriptive names and expository comments — and MUST conform
  to standard Python and Rust style and lint rules, modeled on well-regarded open-source codebases. CI
  MUST enforce style.
- **R11.4 (The coverage gate must reach the non-Python core.)** The ≥ 90 % coverage gate (R0.4)
  measured by the Python tooling sees only the thin re-export of a Rust-backed package; the Rust code
  itself MUST carry its own line-coverage gate in CI (with an explicit threshold). A binding layer
  that the Python frozen suites exercise end-to-end in the same workflow MAY be excluded from the
  Rust-side measurement, with that justification stated next to the exclusion.

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

- **R15.1 (Surface `graphed` through `uproot`.)** `graphed` MUST be wired into **`uproot`**, the
  community's established columnar ROOT-file reader, and surfaced as a **deferred backend alongside
  `uproot`'s existing lazy backend**, mirroring its call shape: a deferred **read** entry point and a
  deferred **write** entry point that parallel `uproot`'s existing lazy (`dask`-backed) ones. The
  integration MUST reuse `uproot`'s own internals — file/path regularization, key filtering, and
  metadata/form inference — and MUST NOT reimplement them.
- **R15.1.1 (Both on-disk formats.)** Deferred reading MUST cover **both** ROOT columnar container
  formats — **`TTree` and `RNTuple`** — through the same `graphed` entry point, using the form/key
  inference appropriate to each (the integration MUST detect the container kind and route to the
  correct `uproot` machinery rather than assuming `TTree`). The acceptance suite MUST exercise reading
  from each format, including necessary-buffer projection (R5) on each.
- **R15.2 (Isolation; not an upstream contribution.)** The integration MUST live on an **isolated
  branch of a fork**; it is an MVP demonstration and MUST NOT be proposed upstream (no pull request to
  the `uproot` project). It MUST be gated through the same orchestrator pipeline (R0) as every other
  milestone, with its own frozen acceptance suite.
- **R15.3 (Deferred reading.)** The read entry point MUST return a **deferred `graphed` array built
  from metadata/form alone** — no event data read at construction. Partitioning MUST support an
  explicit per-file step size, a steps-per-file count, and a **blind** mode that defers entry-range
  resolution to read time, represented with the **first-class blind partition of R7.9** (no sentinel
  encodings; a reader MAY additionally honor a legacy sentinel found in previously serialized plans).
  Necessary-buffer projection (R5) MUST report exactly the minimal columns the recorded graph
  requires, and the per-partition read list MUST be **wired from the projection**, not maintained by
  hand — a test MUST pin that the executor's read set and the recorded graph's projection cannot
  drift apart.
- **R15.4 (Deferred writing — a specialization of the write base.)** The write entry point MUST be
  built as a SPECIALIZATION of the frontend's partitioned-write base (R17.1 — which therefore
  exists BEFORE this integration's writer is implemented): with compute **disabled** it MUST
  return the base's **task graph of write tasks** — each writing its own output partition and
  **reporting its part path** up the deterministic combine tree — **not** an array. With compute
  **enabled** it MUST execute that same task graph through a real reference executor (R7): the
  **process-pool executor by default**, with the thread-pool executor selectable. The two modes
  MUST be consistent (the disabled mode's graph, when run, produces the enabled mode's outputs).
  Partitions are BLIND (the driver opens no files; workers resolve and derive their own part
  index from the partition alone, R15.9); part files follow the base's deterministic naming; a
  step that resolves EMPTY (a file with fewer entries than the step count) is skipped — no empty
  part files are written (part numbering MAY then have gaps in that corner case).
- **R15.5 (Exercise the real deployable path.)** Integration analyses MUST be executed through the
  **reference executors of R7 (the process-pool executor)**, not through a direct in-process
  materialize shortcut, so the path under test is the path that ships. The per-partition work MUST be
  the **compiled-IR evaluation of R7.8** — the analysis compiled (reduced + serialized) at most once
  per worker and evaluated against each chunk — NOT a fresh build-session re-recording the analysis on
  every partition, which only *looks* like graph execution while re-introducing the interpreter-bound
  behavior of §2. Error-harvesting/report-style behavior and resume MUST be expressed with the
  **native checkpoint machinery (R8)** and its semantics (content-addressed dead-letter set, resume
  that skips completed work, error budget) — they MUST NOT emulate `uproot`'s own report semantics.
- **R15.6 (Compile once, run on alternate inputs — demonstrated here.)** The compile-once/run-on-many
  capability (R13.5) MUST be demonstrated through this integration: a plan recorded against one input
  MUST run **unchanged** against a **different file location** and a **different partition count**, with
  the IR proven identical across the re-targetings and the result proven equal to a single-pass
  reference.
- **R15.7 (Regression coverage — the `uproot` suite runs too.)** CI for the integration branch MUST run
  **`uproot`'s full existing test suite together with** the `graphed` integration tests, so a
  regression introduced by the integration's edits to `uproot`'s public surface is caught — not only the
  `graphed` tests in isolation. The integration tests MUST follow `uproot`'s own test conventions (its
  fixtures, data-fetching helpers, markers, and dependency groups) and MUST use `uproot`'s **real data
  fixtures** where provided, including fixtures for both `TTree` and `RNTuple`. Tests requiring an
  external service the lightweight CI job does not provision (for example a remote-storage protocol
  server) MAY be **deselected** by marker, but MUST NOT be deleted, skipped in source, or otherwise
  weakened (R0.6).
- **R15.8 (Buffer-level projection reaches the reader.)** The integration MUST expose the
  buffer-granular projection of R5.3 alongside the column view, and MUST translate a structure-only
  need into the cheapest read the format offers: for a `TTree` jagged branch, the **counter branch**
  (the list lengths without the payload baskets), proven equal to counting the fully-read branch;
  where no counter exists, or where the host API does not expose an `RNTuple` index column
  independently, the fallback is the branch itself and the limitation MUST be recorded, not silently
  papered over. A count-only analysis MUST therefore have a truthful, non-empty read specification
  end-to-end (R5.3.1).
- **R15.9 (Host-integration hygiene.)** The integration MUST consume only **public** frontend/host
  surfaces (no reaching into another package's private internals — required accessors are added to the
  frontend instead). The write entry point MUST reject an array recorded over more than one reader
  source with a clear error rather than silently picking one; MUST write only the array's **projected**
  branches (a bare source read projects to every branch, reproducing whole-source writes); and MUST
  keep per-task static data bounded by the number of *files*, not the number of *partitions* — a
  worker derives its own output-part index from its partition plus a per-file base table, instead of
  every task pickling a full partition-to-path map.

## R16 — Array-library user-facing parity (the numpy backend grows to a usable array library)

The trivial seam-prover backend MUST be grown into a genuinely usable deferred array library with
user-facing parity to the established chunked-array library's core surface, WITHOUT compromising the
frontend's backend-agnosticism. Built as gated milestones in plan-priority order (foundation →
reductions/creation → manipulation/indexing → escape hatches), each with its own frozen suite.

- **R16.1 (Backend-idiom factorization — THE design rule.)** The shared frontend array proxy MUST
  stay **backend-idiom-neutral**: it carries only what every backend idiom shares — operators/dunders,
  the ufunc-dispatch hook, field access, and *protected infrastructure* (form-metadata lookup, the
  axis-normalizing reduction/scan recorders, slice/int indexing). Idiomatic user surfaces are
  backend-owned: a backend hands its own proxy subclass to the build session through an
  **`array_type` factory** (every session builder returns it), and the numpy backend's subclass
  completes the method/property idiom (`.shape/.dtype/.ndim`, `.sum()/.std()/...`, the numpy
  API-function protocol), while the ragged-array backend deliberately supplies NO proxy — its idiom
  is **functions over arrays** (its function namespace), never member functions. A frozen test MUST
  pin that no numpy-idiomatic member appears on the shared proxy class.
- **R16.2 (Full elementwise tier; the host library does the inference.)** Every single-output ufunc
  the host array library offers MUST record one canonical backend-agnostic op (aliases canonicalized
  so they intern); the frontend dispatches by ufunc NAME and never imports the host library. The
  numpy backend MUST infer result forms at record time by evaluating each op on **zero-length meta
  arrays** (length-one unit metas where reductions reject empties), so dtype promotion,
  broadcasting, and type errors are the host library's own — never hand-rolled — and ill-typed
  programs fail at record time with a provenance-located error. Evaluation and inference MUST share
  one op table so they cannot drift.
- **R16.3 (The structural reduction rule.)** A reduction over the partitioned axis (axis None or 0)
  MUST record a **boundary reduction node** (executed by the tree reduction of R7); a reduction over
  an inner axis is partition-local and MUST record a **fusible op**; cumulative scans are always
  fusible (partition-local semantics, documented). Negative axes resolve against the form's rank and
  are refused without one; non-default `keepdims`/`ddof` are recorded present-only so defaults
  intern. The same boundary logic applies to axis-0 slicing/integer indexing/gather/concatenation
  and to whole-axis analytics (unique/bincount/histograms); inner-axis variants stay fusible.
- **R16.4 (Creation, random, and tree-reducible monoids.)** Concrete creators (zeros/ones/full/
  empty/arange/linspace) record **deterministically named sources** so identical creations intern to
  one node; `*_like` creators are fusible ops; `empty` IS zeros (uninitialized memory would break
  byte-identity, R12). Random sources MUST be seeded AND named by (seed, draw index): same seed ⇒
  identical values and identical serialized IR. Reduction monoids (chunk/combine/empty/finalize —
  the process/combine/empty quadruple of R7) MUST agree with the whole-array reference over ANY
  chunking and ANY combine-tree shape, with `empty()` a true identity; kinds that are not
  tree-reducible (median) MUST be refused, not approximated.
- **R16.5 (Axis-0 geometry rules.)** In the axis-0-partitioned MVP the partitioned axis can never be
  moved, squeezed, displaced, or given a concrete length at record time: reshape requires a leading
  -1; transpose/swapaxes/expand_dims touching axis 0, squeeze without an explicit inner axis, tuple
  subscripts indexing axis 0, and stack/vstack (which create an inner unknown-length dim) MUST be
  refused at record time with clear errors. These are Phase-2 (N-D chunking) capabilities, not bugs.
  Deferred arrays MUST NOT be iterable (the legacy iteration protocol over int indexing would record
  forever).
- **R16.6 (Opaque escape hatches stay typed and preserved.)** A multi-input blockwise `apply` MUST
  record ONE External node over N inputs (single-input interns with the M2 map), carrying the
  backend's payload descriptor. The numpy backend MUST offer a **gufunc-signature** form whose
  signature makes the opaque callable typable at record time (core dims bound against operand
  forms; mismatches/unbound outputs fail before any data; declared output dtype) and whose
  descriptor carries the signature as its `io_schema`. The column-projection on-fail policy (R5)
  applies through these nodes unchanged.
- **R16.7 (Scope guard.)** Chunk-aware storage I/O and in-partition linear algebra (the plan's
  P3.9), and everything needing N-D chunk geometry — rechunk, cross-chunk reshape, distributed
  linalg/FFT, map_overlap, `__setitem__`, masked arrays, persist, backend dispatch to GPU array
  libraries (the plan's P4) — are **Phase 2 by user decision** and MUST NOT be built in the MVP.

## R17 — Ragged-array-library user-facing parity (the awkward backend grows to a usable library)

The reference ragged-array backend MUST reach user-facing parity with the established distributed
ragged-array library's core surface, under the R16.1 factorization (its idiom is FUNCTIONS over
arrays — the function namespace IS the user surface; no proxy, no member functions). Built as
gated milestones in the user-directed order: partitioned I/O FIRST, then foundation → structure →
behaviors → conveniences.

- **R17.1 (Partitioned parquet I/O on a COMMON base.)** Parquet reading/writing MUST share one
  backend-agnostic base in the frontend package (discovery — directories/globs sorted, explicit
  lists order-preserving; metadata-only row counts and schema; blind/eager partitioning on the
  first-class blind Partition of R7.9, blind opening NO file — witnessed against nonexistent
  paths; lazy deferred sources whose identity carries the file list; the deferred write plan
  whose compute-disabled task graph, when run, IS the compute-enabled mode per R15.4, with a
  dependency-free key-ordered sequential reference runner and any R7 executor pluggable; writer
  part indices derived from the partition alone per R15.9), specialized per backend with ONLY the
  schema→form translation and the per-partition array codec. The arrow/parquet library is an
  OPTIONAL extra. Write tasks evaluate the COMPILED IR (R7.8), never a re-recorded session.
- **R17.1.1 (The read list: syntactic accesses, buffer-refined.)** A writer's per-task read list
  MUST cover every source field the recorded graph SYNTACTICALLY accesses — compiled-IR
  evaluation replays every node, so a record-constructor's untouched legs (a zip whose only
  consumed property is one derived quantity) must still be readable; the buffer projection alone
  UNDER-SUPPLIES evaluation and MUST NOT be the sole wiring. Each accessed field is then refined
  BY the buffer projection (R5.3): data needs read their leaves; a structure-only need reads its
  CHEAPEST CARRIER — one leaf at-or-under the path, since parquet has no standalone counter
  column (the parquet analogue of R15.8). The column view alone under-specifies structure; the
  buffer view alone under-supplies evaluation; the wiring is their merge.
- **R17.1.2a (The partitioned-source protocol; ONE generic writer.)** The write base MUST include
  a read-side protocol — ``partitions(steps_per_file)`` returning BLIND partitions and
  ``read_partition(partition, columns, resources)`` with open-once resources — that source DATA
  objects implement, and the ragged backend's generic parquet writer MUST dispatch on it: any
  reader integration's deferred arrays then write partition-wise through the SAME entry point
  (``to_parquet(reader_array, ...)``) with NO integration-specific writer function and NO
  whole-dataset materialization (witnessed: the source's whole-dataset loader is never invoked).
  Behavior dicts MAY be forwarded to workers as an importable ``"module:attr"`` reference (they
  often contain lambdas, which do not pickle).
- **R17.1.2 (The rectilinear specialization refuses ragged data.)** The numpy backend's parquet
  surface accepts ONLY fixed-width primitive columns; a jagged/nested column is refused at
  construction with an error naming the column and pointing at the ragged backend. (This amends
  R16.7 by user decision 2026-06-10: parquet I/O alone enters the numpy MVP; zarr/store and the
  rest of P3.9/P4 stay Phase 2.)
- **R17.2 (Foundation.)** The ragged backend MUST implement the FULL R16.2 canonical ufunc tier
  (the host library takes numpy ufuncs; the typetracer infers every form) and every reducer the
  established library offers (incl. mean/std/var(ddof)/min/max/prod/count_nonzero/ptp/moment/
  softmax and the two-array corr/covar/linear_fit), each under the R16.3 STRUCTURAL RULE mapped
  to ragged semantics: axis None/0 (the event axis) records a boundary reduction node, inner
  (per-event) axes record fusible ops — witnessed in BOTH directions per kind; name-based
  boundary classification of reducers is forbidden. Typetracer shims MUST stay inside the host
  library's own inference (mask_identity-style flags, composition of its kernels) — never
  hand-rolled (§A.2).
- **R17.3 (Structure tier.)** The structure functions of the established library's surface
  (sort, mask, pad_none, is_none, singletons, unflatten, regular conversions, full_like,
  nan_to_num, isclose, arg-variants, run_lengths, without_field, multi-output broadcast_arrays/
  unzip as tuples of recorded nodes, eager to_list sugar) recorded through ONE dispatch shared by
  inference and evaluation, all partition-local fusible, all projectable. A list of field names
  on the COMMON proxy records one fusible record-subset op (order significant, interning).
- **R17.4 (Behaviors.)** A behavior dict registered on the backend MUST make behavior PROPERTIES
  (the four-vector pattern) work through plain attribute access: the record-naming op rewraps
  with the behavior on both the typetracer and real paths; field access falls back from record
  fields to attribute lookup; properties record with typetracer forms, evaluate exactly, and
  remain PROJECTABLE down to exactly the leaves they read. Unknown attributes without a behavior
  fail at record time. Parameters (with/without) ride along; high-level attrs do not (Phase 2).
- **R17.5 (Conveniences.)** Introspection (fields/type/backend) answers from the recorded form
  and session, recording NOTHING (node-count witnessed); head/sample are eager peeking sugar over
  the common slice op. The common slice/index ops MUST evaluate on every backend that ships them.
- **R17.6 (Scope guard.)** Phase 2 by user decision: the host library's function-dispatch
  protocol (`ak.f(deferred)` routing — "this is an MVP and dispatch is largely syntactic sugar");
  repartition/divisions; persist; Scalar/Record collection classes; setitem/delitem sugar; the
  string accessor; dataframe/dask interop; tuple getitem; enforce_type/to_packed; text I/O;
  row-group-exact parquet range reads; recorded attrs.

## R18 — Deferred histogramming (its own package + the hist integration)

Histogramming is the terminal operation of real HEP analyses (every ADL benchmark query ends in a
fill); it MUST be built BEFORE any analysis-benchmark port, as follows:

- **R18.1 (Its own package; graphed's evaluation idiom — NOT dask's.)** Deferred histogram
  filling is a SEPARATE package (`graphed-histogram`, the dask-histogram analogue) with the full
  per-repo spine — never folded into a backend. A `.fill(...)` RECORDS and returns self (fills
  accumulate). There is NO `compute()` helper: evaluation is graphed's own machinery — `plan()`
  exports the task graph and an R7 executor's `run(plan).value` IS the aggregated histogram; the
  reference `session.materialize(fill_node)` evaluates one fill eagerly. The recording surface
  mirrors dask-histogram: a deferred `boost_histogram.Histogram` subclass,
  `factory(*arrays, histref=)`, and numpy-like `histogram`/`histogram2d`/`histogramdd`.
- **R18.2 (Fills are an External FAMILY; backends know nothing.)** Each fill records as an
  External node whose `PayloadDescriptor.content_hash` is the SHA-256 of a CANONICAL, VERSIONED,
  declarative axes/storage encoding (JSON params — never pickle; UHI in, UHI out; axis user
  attributes such as hist's name/label live in the boost axis ``__dict__`` and are part of the
  identity). Recording goes through the frontend's caller-supplied-descriptor seam
  (`record_external(descriptor=, form=)` — R8-family: the backend is NOT consulted); evaluation
  resolves through `evaluate_ir(externals=)` by content hash. Identical fills MUST intern.
- **R18.3 (Aggregation rides the existing seams.)** The `plan()` task graph fills partition by
  partition through the COMPILED IR over the partitioned-source protocol (the whole-dataset
  loader is never invoked — counter-witnessed) and tree-reduces by NATIVE histogram addition
  (every standard boost storage is a monoid under `+`) — R15.4 semantics, any R7 executor. Int64
  counts are exact under any combine tree; float storages are deterministic per fixed-tree
  executor configuration (documented, pinned). In-memory sources evaluate via the reference
  materialize (multi-fill: the zero/add monoid helpers over per-fill materializes).
- **R18.3a (Process-boundary witnesses; behaviors under control.)** The frozen suite MUST
  witness, across a REAL spawned process pool: a WEIGHTED (Weight-storage) fill equal to the
  sequential result EXACTLY (values AND variances) and to the eager twin — weighted fills are
  HEP's most common case; and a ragged-backend fill equal to its eager twin. Worker evaluation
  backends are a zero-arg factory/class or an importable ``"module:attr"`` reference resolved IN
  the worker — the REQUIRED form for behavior-carrying backends (behavior dicts contain lambdas
  and do not pickle). Losing behaviors MUST be LOUD: the default (the session backend's class
  constructed bare) failing on a recorded behavior property is PINNED — a silently wrong
  histogram is never acceptable (the dask-awkward lesson).
- **R18.4 (The hist integration lives in the hist FORK.)** `hist.graphed` (in the `hist` fork,
  mirroring `hist.dask`'s MRO sandwich) supplies `Hist`/`NamedHist` with QuickConstruct and
  named-axis fills; an executor's result wraps back into a REAL in-memory `hist.Hist` via
  `hist.Hist(value)` with names/labels intact (axis user attributes ride the canonical spec).
  The fork's CI runs the FULL hist suite alongside the integration tests (the R15.7 pattern).
  Pinned bit for bit against eager twins over the rectilinear backend, the ragged backend
  (ragged fills flatten completely), and a real reader TTree.
- **R18.5 (Out of scope.)** Growth axes; dask-style persist/delayed collection protocols
  (the durable artifact is the compiled IR / DurablePlan).

## Out of scope (later phases — MUST NOT be built initially)

Distributed-scheduler executors for specific batch systems; treating systematic variations as a graph
axis; advanced adaptive reshaping; predicate pushdown; interactive debugging or time-travel; export to
external analysis-preservation portals; swapping the optimizer engine for a more capable one behind the
engine interface; distributed (non-local) checkpoint stores; self-hosting preservation bundles that
embed and launch a model-inference server; **upstreaming or production-hardening the `uproot`
integration** (it remains an isolated MVP demonstration branch — see R15.2); the **N-D-chunking
parity tier** (R16.7 — storage I/O *except parquet, which R17.1.2 pulled into the MVP by user
decision*, linear algebra, rechunk/reshape-across-chunks, overlap halos, mutation, masked arrays,
GPU-array dispatch); and the **ragged-parity Phase-2 set** (R17.6: dispatch-protocol routing,
repartition/divisions, persist, collection classes, setitem sugar, string accessor, dataframe
interop, recorded attrs).

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
- **`uproot` / deferred backend of a reader.** `uproot` is the community's established columnar
  ROOT-file reader that `graphed` is integrated into; its lazy/deferred array entry point (the
  `dask`-backed interface) is what the `graphed` integration parallels.
- **`TTree` / `RNTuple`.** The two on-disk columnar container formats a ROOT file may use to store event
  data: the long-established `TTree` and its successor `RNTuple`. The integration must read both.
- **Blind partitioning.** A partitioning mode whose partitions describe their entry range symbolically
  and defer resolving it (opening the file to learn the entry count) until read time, so no files are
  opened when the partitions are formed. Blind partitions are first-class on the partition type
  (explicit step index + step count, R7.9) — never a sentinel smuggled through another field.
- **Buffer need (data vs. structure-only).** The two granularities of "this analysis reads that
  column": a **data** need reads the leaf values (and brings their structure along); a
  **structure-only** need reads just the list offsets / index / option masks — a multiplicity or a
  mask — servable from a counter branch or index column without the payload (R5.3).
- **Compiled artifact.** The product of the compile step (R7.8): the reduced, canonical, serialized
  IR plus the source names it reads — self-contained, picklable, evaluable on a worker with no
  build-session and no user code, and retargetable at new inputs without recompiling.
- **Witness test.** A frozen test that pins the *mechanism* a requirement names, via an observable
  only the genuine mechanism produces (a work counter, a dispatch count, an off-driver thread id) —
  the defense against semantic stubs, which satisfy input/output equivalence by construction (R0.10).
- **Semantic stub.** An implementation that satisfies a requirement's tests without implementing the
  requirement's mechanism — the canonical example being an "incremental" reduce aliased to the
  one-shot reduce, green under an equivalence-only test.
- **Counter branch.** In a `TTree`, the small branch holding a jagged branch's per-entry list lengths;
  reading it alone yields multiplicities without decompressing the payload baskets (R15.8).
- **Backend-idiom factorization.** The design rule (R16.1) that the shared frontend proxy carries
  only what every backend idiom shares, while each backend completes its own user surface — the
  numpy backend through a proxy subclass supplied via the `array_type` factory (methods,
  properties, numpy API dispatch), the ragged-array backend through a function namespace (its
  arrays never grow member functions).
- **Meta array (zero-length stand-in).** A length-zero (or, for reductions, length-one) array
  carrying a form's dtype and trailing shape, on which an op is evaluated at record time so the
  host library itself performs promotion/broadcasting/type checking (R16.2).
- **Structural reduction rule.** The recording rule (R16.3) that consuming or restructuring the
  partitioned axis makes a node a stage boundary (tree-reduced), while inner-axis work stays
  partition-local and fusible.
- **gufunc signature.** The "(i),(i)->()" core-dimension notation that makes an opaque callable
  typable at record time and is preserved as the External node's `io_schema` (R16.6).
- **Behavior (ragged records).** The host ragged library's mechanism attaching methods/properties
  to named record types (the four-vector pattern); registered on the backend, carried through the
  typetracer, resolved by attribute-access fallback, and projectable to the leaves a property
  actually reads (R17.4).
- **Cheapest carrier.** The single leaf column read to satisfy a structure-only (offsets) need in
  a format with no standalone counter column — parquet's analogue of the counter branch (R17.1.1).
- **Blind partitioning (parquet).** The R7.9 blind partition applied to parquet datasets: no file
  is opened at partition time; ranges resolve against metadata row counts at read time (R17.1).
- **Partitioned-source protocol.** The write base's read-side protocol (R17.1.2a): a source data
  object describes its own (blind) partitioning and reads one partition at a time, so generic
  writers and partition-wise consumers never materialize a dataset through its lazy loader.
