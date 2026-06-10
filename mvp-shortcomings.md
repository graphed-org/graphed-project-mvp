# MVP shortcomings — findings & remediation tracking

Status: captured 2026-06-09 from a full-codebase sweep (optimizer, executor, checkpoint, frontend,
CI workflows, uproot fork execution glue). Companion to `buffer-level-projection-plan.md`.
Remediation in progress — see the checkboxes per finding.

**TL;DR:** All gates are green, but three of the project's own headline promises are only
structurally satisfied, not behaviorally: (1) "incremental reduction" is an alias for full
reduction and is never invoked during graph building; (2) the optimized/fused graph never drives
execution — every partition re-records and re-walks the un-reduced op log in Python, precisely the
dask failure mode the project exists to avoid; (3) column projection is lossy for count-only
analyses and isn't auto-wired into reads. Below those, a concrete M0/A.5 compliance gap (no wheels
workflow, partial CI matrix) and a tail of component-level weaknesses.

Integrity constraint on all fixes: existing `tests/frozen/**` are untouchable. Every fix lands as
**new functionality with its own new frozen suite** (`tests/frozen/m10*/` per repo), keeping all
existing frozen tests passing unmodified.

---

## A. Architecture-level: the spec's headline vs. runtime reality

### A.1 — "Incremental reduction" is a pass-through alias  `[FIXED — graphed-core + graphed M10]`
`GraphStore::reduce_incremental` at `graphed-core/src/store.rs:185` is literally
`self.reduce(engine)`. Nothing in the frontend calls it during construction —
`graphed/src/graphed/session.py:58` reduces once, at `serialized_ir`/plan time. §A.1's central
claim ("reduces the graph incrementally as the user builds it, so a large un-reduced graph never
exists") is not what happens: the full un-reduced graph exists until compile time. The frozen test
(`graphed-core/tests/frozen/m4/test_reduce.py:124`) only asserts `reduce_incremental() == reduce()`
— equality, not incrementality. A semantic stub the integrity scanner cannot catch; the reviewer
approved it anyway.

**Fix:** a genuine `IncrementalReducer` in Rust (caches the reduced prefix + id map; per-step work
proportional to the delta + reduced size, not history), exposed via PyO3; `Session` steps it every
N records so a concise reduced view always exists and `serialized_ir` consumes it without a final
full-graph reduction. New frozen tests prove *equivalence at every step* AND *bounded per-step
work* (a work counter in the report), which the alias cannot pass.

### A.2 — Optimization never pays off at runtime  `[FIXED — graphed-core + graphed M10; fork rewired]`
`Session.walk` (`graphed/src/graphed/session.py:154`) evaluates the Python-side `self._ops` dict
node-by-node — one `backend.eval_stage` dispatch per *recorded* (un-reduced) op. The Rust store, M4
reduction, and fused `Stage` nodes are never consumed by `materialize`. In the deployable uproot
path (`tests/graphed_uproot_analysis.py` on the fork), each worker **builds a fresh `Session` and
re-records the whole analysis per partition**. Interpreter touchpoints scale as
O(unreduced-ops × partitions) — dask failures #2/#6/#7 reintroduced on the path R15.5 says "is the
path that ships." (M9's `reproduce` already interprets IR — the interpreter exists, the executors
just don't use it.)

**Fix:** an IR-driven execution bridge in `graphed`: compile a session's outputs to the serialized
**reduced** IR once; workers deserialize once (cached per worker) and evaluate the reduced node
list directly — no Session, no re-record, no form re-inference per partition. New frozen tests:
result equality with `materialize` on both backends; evaluation works from IR bytes alone (no
analysis function in the worker); backend dispatch count equals the *reduced* op count, not the
recorded count. Fork's executor glue rewired to use it.

### A.3 — Projection is column-level, lossy, and manually wired  `[FIXED — graphed + graphed-awkward M10; fork exposes necessary_buffers]`
Full analysis in `buffer-level-projection-plan.md`. Sharpened by this sweep: (a) the frozen M5 test
pins a count-only analysis to the **empty column set**, so feeding `necessary_columns` into the
reader for such an analysis reads zero branches and produces a *wrong answer*; (b) projection→read
plumbing is manual (`COLUMNS` hard-coded in the fork's helper).

**Fix:** additive buffer-level API — `project_buffers` in `graphed-awkward` returning per-source
`{column: DATA|OFFSETS}` needs (keeps both `data_touched` AND `shape_touched`, maps non-leaf form
nodes); `uproot.necessary_buffers` in the fork; reader honors offsets-only needs (TTree
`count_branch` when available; never an empty read for a count-only analysis). Column-level
`project` is unchanged (M5 frozen suite intact). New frozen tests: count-only → `{col: OFFSETS}`
(non-empty!), sum → data, mixed, buffer-level no-overtouch.

## B. Spec/DoD compliance gaps

### B.4 — No wheels workflow; partial CI matrix  `[FIXED — all repos; guarded by meta scripts/test_workflows.py]`
Every repo has only `ci.yml`: no wheel-building workflow anywhere, no arch dimension; matrices are
3 OS × CPython 3.11–3.13; only `graphed-core` has a 3.14/3.14t job (single OS). §A.5 demands
{3 OS × 2 arch × 3.11–3.14t} + abi3 + dedicated 3.14t wheels. The DoD and `state.json` over-claim.

**Fix:** extend matrices (3.14 + 3.14t across OS; linux-arm64 runners), add `wheels.yml` per repo
(pure-Python: build sdist+wheel; graphed-core: cibuildwheel/maturin incl. abi3 + 3.14t) — **build
only, no PyPI publish**. Guarded by a new frozen config-drift test in the meta repo asserting every
submodule's workflow coverage.

### B.5 — Coverage gate effectively waived for Rust  `[FIXED — cargo llvm-cov gate at 85% (measured 92.3%), lib.rs excluded as the Python-suite-covered binding layer]`
The ≥90% gate measures the thin Python re-export; the 2,220 lines of Rust have no coverage wiring.

**Fix:** `cargo llvm-cov` job in graphed-core CI with a threshold; meta config test asserts its
presence.

## C. Component-level weaknesses

### C.6 — Stage fusion isn't "maximal"  `[FIXED — opt-in reduce(maximal_fusion=True); default pinned by frozen M4]`
`stage_fusion` (`graphed-core/src/optimizer/mod.rs:167`) fuses an op into its consumer only when it
has exactly one use — any fan-out splits a stage, so diamonds produce more, smaller stages than the
glossary's "maximal fused run" promises.

**Fix:** fuse a multi-consumer op when *all* of its consumers are ops that land in the same stage
(boundaries still never crossed). Deterministic; existing frozen m4 assertions are directional
(`<` thresholds) so improved fusion keeps them green. New frozen tests: a diamond inside an op
region fuses to ONE stage; fan-out to a boundary still splits.

### C.7 — The e-graph does almost no optimization work  `[FIXED — commute rules for every symmetric op; + latent token-injectivity bug fixed]`
Six sound rules (commute +/×, ±0, ×1). Real HEP graphs rarely contain literal `+0`/`×1`; the
equality-saturation machinery contributes essentially nothing beyond argument-order
canonicalization for CSE.

**Fix:** broaden the *sound* rule set (commutativity of the symmetric ops actually in the op
vocabulary — and/or/min/max/eq/ne…); new frozen tests prove two graphs differing only in symmetric
argument order canonicalize to the same reduced form. (Domain-dependent/unsound rules stay
excluded, per M4.)

### C.8 — Executor combines run serially on the driver  `[FIXED — opt-in pooled_combines=True; default pinned by frozen M7]`
`tree_reduce` executes every `combine()` on the driver thread (`executors.py:97`); workers only
produce leaves. For heavy partials the driver is a serial bottleneck. First worker exception aborts
the whole run (retry/dead-letter only via `graphed-checkpoint`, by design).

**Fix:** schedule combines onto the same pool as leaves (deterministic pairing unchanged →
bit-identical results). New frozen tests: result equality + combine count + combines observed
off-driver (thread id / worker pid).

### C.9 — uproot integration rough edges  `[FIXED — Partition.blind in core; fork: sentinel retired (freeze-UPROOT-1 amendment), sources() accessor, projected write, O(#files) path table]`
- Blind partitions overload `Partition` fields as a sentinel (`entry_stop = -n_steps`). → **Fix:**
  first-class blind partitions in `graphed-core` (`Partition.blind(uri, tree, step, n_steps)`,
  explicit `is_blind`/`resolve(num_entries)`), sentinel retired in the fork.
- `graphed_write` writes ALL `_common_keys` (ignores projection), assumes a single source, reaches
  into private `session._sources`, opens every file at build time. → **Fix:** public
  `Session.sources()`; write the *projected* columns; clear multi-source error; blind build mode.
- `_write_partition` pickles the entire `out_paths` dict into every task (O(n²) aggregate). →
  **Fix:** per-task path derived from the partition key.
- `_GraphedTTreeSource.__call__` concatenates all files in memory on direct materialize. →
  Inherent to materializing a whole multi-file dataset as one array; the partitioned executor path
  (now IR-driven, A.2) is the supported large-data path. Documented, not "fixed".

### C.10 — Integrity scanner narrowness  `[FIXED — body-aware bare-pass/... detection for named targets]`
The stub regex (`graphed-orchestrator/src/graphed_orchestrator/integrity.py:25`) misses
`pass`-bodied targets (explicitly listed as a violation in the root CLAUDE) and, by nature,
semantic stubs like A.1.

**Fix:** detect `pass`-only bodies for named Implementation Targets (additive code; new frozen
test). Semantic stubs remain the reviewer's job — recorded here as a process lesson.

---

## Remediation order

1. A.2 — IR-driven execution (makes optimization real; aligns the shipped path with §A.1–A.3)
2. A.1 — genuine incremental reduction
3. A.3 — buffer-level projection (correctness, not just efficiency)
4. B.4 + B.5 — wheels, full matrix, Rust coverage (no PyPI publish)
5. C.6–C.10 — fusion, rules, parallel combines, uproot/Partition cleanups, scanner

All new functionality ships with new frozen suites (`tests/frozen/m10*/`); no existing frozen test
is modified.

---

## Remediation record (2026-06-09)

All of A, B, C remediated as milestone **M10** across the repos — every fix ships with a NEW frozen
suite (`tests/frozen/m10/` per repo; `tests/test_graphed_m10.py` in the fork); no pre-existing
frozen test was modified, with ONE recorded exception: the fork's
`test_blind_partitions_do_not_open_the_file` pinned the negative-`entry_stop` sentinel *encoding*
(not behavior) and was amended to pin the first-class `Partition.blind` representation under a
freeze-tag bump (`freeze-UPROOT-1`), human-directed, recorded in the fork's `.graphed/`.

Notable scope decisions:
- **A.1**: `Session(incremental=True)` is opt-in — the frozen M8 test pins
  `serialized_ir(optimize=True)` to the one-shot reduce path for default sessions; byte-equality of
  the two paths is pinned in the new suite.
- **C.6 / C.8**: maximal fusion and pooled combines are opt-in flags — the frozen M4/M7 suites pin
  the default behaviors (diamond apex stays its own stage; combines on the driver).
- **A.3 in the fork**: `necessary_buffers` + `resolve_read_branches` demonstrate the offsets-need →
  counter-branch translation (count served from `NMuon` without `Muon_Px` payload baskets). Full
  evaluator-side form reconstruction from counter-only reads (rebuilding a typetracer-compatible
  array from offsets + placeholder leaves) remains future work, as does RNTuple per-physical-column
  addressing (not exposed by uproot's public API).
- **B.4**: macOS x86_64 is covered by universal2 wheels (Intel CI runners are retired); Windows
  arm64 is not yet covered (runner availability). `release.yml`-style publishing (tag → TestPyPI,
  GitHub Release → PyPI) is allowed to exist but ordinary push/PR CI may never publish — enforced
  by `scripts/test_workflows.py`. **Nothing was published to PyPI in this remediation.**
- `_GraphedTTreeSource.__call__` still concatenates all files on a direct whole-dataset
  materialize — inherent to producing one in-memory array; the partitioned compiled-IR path is the
  supported large-data path (documented, not "fixed").

---

## Warning watch (added 2026-06-10, post M15–M19 — tracked, deliberately NOT fixed)

Two warning sources exist across the ten repos' suites; both were investigated and judged not
worth fixing now (details in `.graphed/tracking/torch-jit-deprecation.md`):

- **graphed-awkward, 1 RuntimeWarning (divide by zero), m17 frozen suite.** Deliberate inf/NaN
  input (`pt/(pt-pt)`) proving `gak.nan_to_num`; deterministic and self-documenting. Fixing means
  amending a frozen test for cosmetics; suppressing via config or in the eval dispatch would mask
  REAL numeric warnings. Leave as-is.
- **graphed-preserve, 70 DeprecationWarnings (torch.jit.{trace,trace_method,save,load}),
  m9 frozen suite, torch 2.12.** All from the TorchScript FIXTURE in
  `tests/frozen/m9/test_ml_plugins.py`; production graphed-preserve imports no torch (the
  externals-plugin machinery is format-generic; ONNX is the canonical model format per R10).
  Action trigger: torch announcing removal of `torch.jit` (or the matrix turning these into
  errors) → a recorded freeze amendment swaps the fixture to `torch.export` — a contained,
  one-file change whose content hashes change with the artifact format.
- **compile_ir output accumulation — FIXED 2026-06-10 (M22, same day as found):** outputs are
  now a property of the COMPILE REQUEST (`reduce`/`serialize`/`finalize` take `outputs=`;
  `serialized_ir`/`compile_ir` pass them explicitly), so compiles from one session are
  independent and byte-identical to fresh-session compiles. Frozen m22 suites in graphed-core
  and graphed pin it. The m21 one-session-per-compile note remains as historical record (still
  a valid pattern). Residue: the legacy `mark_output` side effect is retained for the frozen m8
  pin but is never read by the compile path.
