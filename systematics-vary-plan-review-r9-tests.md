# Review — `systematics-vary-plan.md` r9 — LENS: TEST ARCHITECTURE (round 1)

- **Lens:** test architecture — frozen-anchor non-vacuity/discrimination, mechanism witnesses
  (R0.10), no wall-clock/size gates in frozen tests (R0.10a), determinism-gate compatibility,
  freeze-order hazards, requirement↔anchor traceability, and buildability of the fixtures the
  anchors name.
- **Plan revision reviewed:** r9 (2026-07-30), all 1051 lines (Part I rationale, PART II §§1–12,
  §10 milestones m48–m51, Anchors appendix, revision history).
- **Date:** 2026-07-30
- **Verification roots used (fresh clones at the cited revisions; the stale workdir submodules were
  NOT used for any code fact):**
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, ff7c607) — probes run with
    `uv run` against its built extension
  - `/private/tmp/claude-501/graphed-exec-check` (`graphed-executors`, 201ea42)
  - `/private/tmp/claude-501/graphed-histogram-latest` (211cbbe)
  - `/private/tmp/claude-501/graphed-corpus-latest` (49650e4)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10, R0.10a, R0.11, R22.3)
  - companion evidence: `systematics-vary-codebase-analysis.md` (cba), `…-litsearch.md`,
    `…-worklog.md`
- **Owner-locked decisions were not relitigated.** Every finding below is either an internal
  inconsistency in how the plan *specifies* a test, a measured factual error, or a missing/weak
  anchor — never "prefer a different design".

Reproduction commands for the two measured findings are inlined with their evidence.

---

## Findings

### 1. HIGH — §8.2's bound label-transport mechanism does not exist: nothing constructs a `StageError` on a worker in the production plan path

**Section:** §8.2, §7.4, m49 anchor "§8.2 cross-process labeled StageError (incl. §7.4 dead-letter
label)".

**Detail.** §8.2 binds the transport as: *"the frontend's node-id → label map travels the same
process-closure channel that **already delivers per-node provenance to worker-side StageError
construction** (`debug/runner.py:20-45`; closures ship via the plan's OpSpec payload,
`aggregate.py:54,96-104`) — no `Plan`/`ExecResult` schema change; the worker sets
`StageError.variation` from the failing node id at construction."* The closure channel is real, but
the italicised premise is false: **no per-node provenance travels that channel, and the production
worker callable never constructs a `StageError` at all.** `_PartitionReduce.__call__` — the thing
that actually runs on a worker for an `aggregate_plan` — calls `evaluate_ir` bare and has no
provenance, no node map, and no error wrapping. The only `StageError` construction site in the
whole `graphed` package is the M6 *debug* runner, which requires a driver-side `Session`
(`lower(session, array)`, `session.source_value(nid)`) and is therefore not reachable from a
shipped plan. The one existing frozen test that gets a `StageError` out of a worker process does it
by shipping a closure that **rebuilds the analysis inside the worker** and calls `gd.run` there.

As a consequence the m49 anchor ("a failure raised inside the `jes_up` universe on a worker across
a process boundary re-raises driver-side carrying `variation == "jes_up"` AND the user's analysis
line (M6 contract extended, not altered)") is not buildable from what the plan binds. Either
(a) real work is required that no §10 target names — ship provenance + the node→label map inside
`_PartitionReduce` and wrap `evaluate_ir` so worker failures become attributed `StageError`s — or
(b) the test-author falls back to the m7 rebuild-in-worker pattern, in which case the anchor
witnesses a closure the test wrote itself rather than the varied plan's label transport, i.e. it
degrades to a near-vacuous witness of the production path. Neither is chosen by the plan, and the
choice changes m49's size materially.

**Evidence (all read/run this session, verification roots):**
- `graphed-latest/python/graphed/aggregate.py:56-64` — `_PartitionReduce.__call__`: `read_partition`
  → `evaluate_ir(self.ir, …)` → `self.reduce(values)`. No try/except, no provenance, no StageError.
- `grep -rn "StageError(" graphed-latest/python/graphed/` → exactly two hits:
  `debug/runner.py:37` (the constructor call) and `debug/errors.py:29` (the class). Nothing else in
  the package constructs one.
- `graphed-latest/python/graphed/debug/runner.py:57-69` — `run(session, array, …)` needs the live
  `Session` (`lower(session, …)`, `session.source_value(nid)`); `_chain()` at `:20-30` reads
  provenance off the `LoweredGraph`, which is built driver-side from the Session, not from plan
  bytes.
- `graphed-exec-check/tests/frozen/m7/test_remote_error.py:14-27` +
  `tests/frozen/m7/analyses.py:118-127` — the worker-side StageError exists only because the process
  callable does `Session(...)` → record → `gd.run(...)` *inside the worker*.
- `graphed-exec-check/src/graphed_executors/submit/engine.py:381-400` and
  `local/executors.py:294-300` — executors only *translate worker-death* into a StageError or
  *propagate* one that was raised; they never build one from an `evaluate_ir` failure.

**Suggested fix.** Split §8.2 into (i) the transport (node→label map as a new field on the shipped
process closure — true today) and (ii) the missing prerequisite: attributed worker-side errors for
the `aggregate_plan`/executor path (ship the per-node provenance the map keys against, wrap
`evaluate_ir`). Name (ii) as an explicit m49 target with its own anchor, or scope the m49 anchor to
the label-map round-trip plus a driver-side `debug.run` attribution test and say so.

---

### 2. HIGH — Two binding silent-wrongness guards have no frozen anchor at any milestone: §1.2 (labels out of node identity) and §6.1c (`.plan()` must refuse varied fills)

**Section:** §1.2, §6.1c; §10 m48/m49/m50/m51 anchor lists.

**Detail.**
- **§1.2** is load-bearing ("a label MUST NOT enter `NodeKey` params, tokens, or content hashes";
  "two variations with structurally identical content intern to the same nodes"). §5.2a even names
  the discriminating case — *"Labels structurally identical to a prior label dedup to Δ = 0 by
  §1.2 — that case is witnessed separately as the dedup feature"* — but **no milestone anchor
  lists that witness**, and no anchor asserts label-absence from a *varied* graph's IR. The §6.3
  goldens do not cover it: they pin an **unvaried** fill graph (golden GIR blob) and
  params-key *absence* on today's shapes. §4.3's impact-set assertion covers only the weight case
  and only partially. An implementation that stamps the label into every re-recorded node's params
  would pass m48–m51 as listed, while silently destroying interning, cross-label dedup, and the
  §7.3 checkpoint story.
- **§6.1c** exists precisely because `_SumFills` sums **all** staged fill nodes into one histogram
  and would therefore *silently merge universes* on the single-histogram `.plan()` path. The
  requirement ("`.plan()` on a varied `Histogram` raises, pointing at the group API") appears in no
  anchor list. A wrong implementation that leaves `.plan()` merging universes produces plausible-
  looking, physically wrong histograms and passes every listed anchor.

**Evidence:**
- Plan §10, m48–m51 anchor bullets read in full — neither a `.plan()`-refusal anchor nor a
  label-absence/dedup anchor appears; §5.2a's "witnessed separately" has no referent in §10.
- `graphed-histogram-latest/src/graphed_histogram/boost.py:85-97` (`_SumFills.__call__` sums every
  fill into one histogram) and `:99-117` (`_GroupReduce` keyed by label) — confirms §6.1c's stated
  hazard is real.
- `graphed-histogram-latest/tests/frozen/m29/test_multi_weight_fills.py:93-96` — the
  params-absence pattern the plan cites is `assert "n_weights" not in node["params"]` on a
  *single-weight* (i.e. unvaried) node; it does not constrain varied graphs.

**Suggested fix.** Add to m48: (a) *label-absence*: for a varied program, no node in
`session._store.nodes()` has any label string in `params`/token, and renaming every label leaves
`compile_ir(...).ir` **byte-identical** (a strong, cheap, deterministic discriminator); (b)
*dedup*: two labels whose members are structurally identical produce arena Δ = 0 and identical node
ids; (c) `.plan()` on a varied `Histogram` raises with a message naming the group API, plus a
positive control that `.plan()` on an unvaried `Histogram` still works.

---

### 3. MID — §3.3 and §5.2a pin exact integers that are wrong for the topology the prose describes (measured)

**Section:** §3.3 (m49 frozen benchmark), §5.2a (arena-delta witness).

**Detail.** §3.3 describes the topology as *"shared prefix + N varied suffixes where **each
variation is a separately marked output**"* and then pins `stages == N + 1` **and**
`reduced_nodes == 2N + 2`. §5.2a says *"a 50-op varied chain adds exactly 52 nodes"*. Both literals
come from cba §optimizer §2 — whose measured builder is *"per-variation `shift` + 50-op downstream
chain **+ 1 reduction**"* (cba line 274). The reduction node is not mentioned in either PART II
sentence, and it is exactly what makes the numbers come out. Built as the prose reads (marked op
outputs, no per-variation reduction) the same store reports `reduced_nodes == N + 2` and an
N=1→2 arena delta of **51**, so a test-author following §3.3/§5.2a verbatim freezes an assertion
that fails a *correct* reducer.

**Evidence (probes run this session against `/private/tmp/claude-501/graphed-latest`, `uv run`):**

```
# builder: source → 500-op shared prefix → per variation: shift + 50 ops [+ reduction]; reduce(all outputs)
red   N=16  stages 17  reduced 34   | N+1=17  2N+2=34      <- matches the plan's literals
red   N=128 stages 129 reduced 258  | N+1=129 2N+2=258
nored N=16  stages 17  reduced 18   | N+1=17  2N+2=34      <- prose-as-written: reduced = N+2
nored N=128 stages 129 reduced 130
arena delta N=1->2:  with reduction 52   without reduction 51
```
(`stages`/`reduced_nodes` are the real report keys — `graphed-latest/src/lib.rs:450-451`.)
cba §optimizer §2 table (N=16 → 34 reduced / 17 stages; N=128 → 258 / 129) reproduces exactly,
confirming the plan's numbers are the measured ones *for the reduction-terminated topology*.

**Suggested fix.** State the builder explicitly in §3.3 and §5.2a: source → shared prefix of D ops →
per universe {one varied fork op, K chain ops, **one reduction node**}, all universes marked as
outputs, `N` counting nominal. Then the literals `stages == N+1`, `reduced_nodes == 2N+2`, and
Δ = D+2 = 52 are correct as written (and are the realistic shape, since a fill *is* a reduction).

---

### 4. MID — m49's headline reference-matrix anchor does not say which of two very different builds it is, and the executors repo lacks the fixtures either would need

**Section:** §10 m49, first anchor ("The full 15-reference matrix through the frontend
(fingerprint-exact, as m48) AND through a process-pool executor — fingerprint-exact vs the
references"); §5.2b ("bound to the reference-matrix run itself").

**Detail.** m49's repos are `graphed` + `graphed-executors`, and the process-pool half necessarily
lives in `graphed-executors` (the `graphed` repo contains no process pool — grep for
`ProcessPool|concurrent.futures` under `graphed-latest/python` and `tests/frozen` returns nothing).
In `graphed-executors` as it stands:
- **The 15 stored references are not reachable.** `graphed-corpus`'s wheel ships only
  `src/graphed_corpus`; the reference JSONs live in the repo directory `corpus/references/` and are
  not package data. The consolidated `graphed` repo works around this by vendoring them at
  `tests/_corpus/references` (23 files) and putting `tests/_corpus` on the pytest `pythonpath`.
  `graphed-executors` has no such copy, and none of its existing frozen tests ever calls
  `load_reference` — the house pattern there is to *recompute* the corpus fixture in-process and
  compare (m7/`adl.py`, m41/`test_adl_no_regression.py`).
- **`graphed-histogram` is not a dependency**, so a varied-*fill* anchor (the §4.2/§6.1 lowering,
  which is the point of a weight-variation matrix) cannot even be collected there. The alternative
  is the m7 pattern (materialize per chunk, fill eagerly in the reduce closure), which reproduces
  the references but exercises none of §4.2/§6.1/§6.2 — a materially weaker test.

**Evidence:**
- `graphed-corpus-latest/pyproject.toml:28-30` — `[tool.hatch.build.targets.wheel] packages =
  ["src/graphed_corpus"]`; references live at `graphed-corpus-latest/corpus/references/` (23 JSON
  files) outside the packaged tree; `tests/frozen/m05/conftest.py:21` resolves them by repo path.
- `graphed-latest/tests/_corpus/references` — 23 vendored JSONs; `graphed-latest/pyproject.toml:115-117`
  puts `tests/_corpus` on `pythonpath`.
- `graphed-exec-check/pyproject.toml:20-35` — deps `graphed`; dev extra
  `graphed[awkward,numpy]`, `graphed-corpus`, numpy, awkward. **No `graphed-histogram`**; no mention
  of it anywhere in the repo (`grep -rn histogram .github/workflows pyproject.toml` → no hits).
- `graphed-exec-check/tests/frozen/m7/adl.py:124-144` — the existing executor pattern:
  `s.materialize(query(ev))` per chunk then an eager `hist1d(...)`, compared against
  `adl_full_counts` (recomputation), never a stored reference.

**Suggested fix.** In §10 m49, say explicitly: which repo holds which half; that the executor half
compares fingerprints against corpus fixtures **recomputed in-process** via `graphed_corpus`
(the m7 house pattern) or that the 15 JSONs get vendored; and, if the executor half must exercise
varied fills, that `graphed-histogram` is added to `graphed-executors`' dev extra as part of m49.
Also state which run the §5.2b read witness binds to under that split.

---

### 5. MID — traceability gaps: binding PART II requirements with no milestone anchor

**Section:** §2.1 (stacking), §2.2 (`Varied.apply`), §6.1a (per-output label sets), §9.1
(`graphed.variations` + numeric-tag parsing), §7.2 (schema-unchanged).

**Detail.** Each of the following is binding text with no anchor in §10 (checked bullet-by-bullet):
- **§2.1 stacking** — "when the target already carries variations, the result inherits those labels
  … a new label's member is the provided value's central universe". This was an r1 BLOCKER fix (the
  corpus b-tag-on-JES case) and §2 is an **m48** target, but m48's anchors cover only §2.4
  ("Varied-meets-itself"), not stacking. Stacking is exercised only implicitly by m49's 15-reference
  matrix, one milestone later — so m48 could ship without it, green.
- **§2.2 `Varied.apply(fn)`** and its specific error contract ("`fn` MUST return an `Array`; if it
  returns a `Varied` … raises with guidance") — no anchor.
- **§6.1a** — "an output no variation reaches returns a bare `hist` (NOT `{"nominal": hist}`)" and
  "absent labels are absent, never silently duplicated from nominal". Both are precise, discriminating
  rules about a *varied* program's result shape; the §6.3 goldens only cover fully-unvaried programs.
- **§9.1 `graphed.variations(ctx)`** including the parsed float value for numeric tags — and note
  §9.1 requires **two** parsers (canonical e-form `m?\d+(em\d+)?` *and* the datacard p-form
  `m?\d+(p\d+)?`). m50's anchor mentions only "`inspect()` label listing"; m48's introspection
  anchor lists `graphed.universe`/`labels`/`nominal` and not `variations`. The parsed-value path is
  load-bearing (§6.2 explicitly refuses to give numeric ordering from bin index) and is exactly the
  kind of small parser that rots untested.
- **§7.2** — "`ExecResult`/`Plan`/monitor schemas do not change in m48–m50" has no
  schema-absence anchor (the §6.3 params-absence pattern is the natural vehicle).

**Evidence:** plan §10 m48–m51 anchor bullets, read in full, cross-checked against every bullet of
§§1–9. (Converse check is clean: I found **no orphan anchors** — every anchor traces to a PART II
requirement.)

**Suggested fix.** Add one anchor each: m48 stacking (`vary` on an already-varied target: label
order = inherited-then-new, the new label's member is the provided value's nominal universe,
one-knob-per-label); m48 `.apply` contract incl. the Varied-return refusal; m48 §6.1a shape rules on
a mixed varied/unvaried output set; m50 `graphed.variations` incl. both numeric parses and a
non-numeric tag returning no value; m48 schema-absence for §7.2.

---

### 6. MID — m51's superset-row anchor names a self-derived reference (the trap §5.2a warns about)

**Section:** §10 m51, first anchor; §6.4a.

**Detail.** The anchor is *"a varied selection writes exactly the OR-of-selections row set — every
universe's rows present, no row outside the union (**frozen vs per-label in-memory row sets**)"*,
while §6.4a says the OR itself "is recorded as ordinary graph ops over the per-label masks". If the
per-label row sets used as the reference are produced by the same varied graph, the assertion
reduces to "the OR of these masks equals the OR of these masks" for any mask-computation bug — the
same family as the `delta == len(cone)` self-derived comparison review r0 caught in §5.2a. It still
catches a writer that drops or adds rows, but not a wrong per-label selection, which is the thing
skim augmentation exists to preserve.

**Evidence:** plan §10 m51 bullet 1 and §6.4a as written; §5.2a's own statement of the trap ("a
self-derived `delta == len(cone)` comparison is tautological, review r0"). The house pattern for an
independent reference already exists —
`graphed-histogram-latest/tests/frozen/m23/test_group_plan.py:60-66` (`_eager(...)` computed with
plain numpy/bh) and `graphed-exec-check/tests/frozen/m7/adl.py:156-158` (corpus recomputation).

**Suggested fix.** Word the anchor as: the reference per-label row sets are computed **eagerly with
awkward, outside graphed**, from the same input events; the written row set must equal their union,
and each universe's reconstructed rows must equal its eager row set.

---

### 7. MID — §9.2's m50 preservation anchor names a comparison form but no constructor, and today's bundle API is single-output only

**Section:** §9.2, §10 m50 ("§9.2 one-bundle-N-labels preservation (m9 comparison form) +
`inspect()` label listing").

**Detail.** §9.2 requires "a bundle built from a variation-expanded graph reproduces **all** labels
from ONE bundle … `np.array_equal(reproduce(bundle)[label], build_time[label])`". Today
`build_bundle` takes a strictly singular `value=` / `weight=` / `histogram=` triple (and raises
unless `weight` and `histogram` are given together), and `reproduce` returns a single array. So the
anchor presupposes an API surface — a varied/multi-output `build_bundle` and a mapping-returning
`reproduce` — that the plan never pins. The plan is careful about exactly this elsewhere ("helper-verb
spellings pinned at m48 freeze", "`graphed.read_varied(path)`-shaped; spelling at freeze",
"appended names … exact spelling pinned at m51 freeze"); §9.2 has no such clause, and the test-author
freezes before the implementer exists.

**Evidence:** `graphed-latest/python/graphed/preserve/bundle.py:103-123` (`build_bundle(…, value,
weight=None, histogram=None, …)`, with the "weight= and histogram= must be given together" guard)
and `:206-210` (`def reproduce(bundle) -> Any: """… return its histogram."""`);
`graphed-latest/tests/frozen/preserve/m9/test_reproduce.py:19-23` (the single-array comparison form
the plan cites).

**Suggested fix.** Add to §9.2: the varied `build_bundle` input shape (a `Varied` value/weight, or a
per-label mapping) and `reproduce`'s return type for varied vs unvaried bundles — **spelling pinned
at m50 freeze** — plus the explicit backward-compat statement that an unvaried bundle still returns
a bare array (which the "existing m9 frozen tests are untouched" clause already implies but does not
say).

---

### 8. MID — R0.10a is applied inconsistently: §3.3 puts a wall-clock ratio (and an absolute per-size budget) inside a frozen test while m50/m51 invoke R0.10a to bar exactly that

**Section:** §3.3; §10 m50 ("R0.10a: no wall-clock in frozen tests") and m51 ("R0.10a — no size
thresholds in frozen tests").

**Detail.** §3.3 pins "a linear-growth bound (`time(128)/time(16) < 24.0`, the m4 threshold style)"
in a **frozen** file, and "replicating the `test_benchmark.py:10,40-53` pattern" also imports that
file's absolute `elapsed < 1.0` per-size budget. R0.10a's forbidden shape (a) is wall-clock
comparisons in frozen tests, and its closing line is categorical: "measurement of a perf *claim* is
R0.11; a frozen *gate* must not depend on it." The plan cites R0.10a twice, to demote m50's
sibling-vs-axis timing and m51's compression win — so §3.3 reads as an unacknowledged
contradiction, and a TEST_SANITY reviewer has no written basis to accept it. There *is* a
legitimate carve-out (the project plan's M4 mandates a CI benchmark that fails on super-linear
reduction time, and `tests/frozen/core/m4/test_benchmark.py` is the frozen precedent, complete with
a `base = max(times[SIZES[0]], 1e-4)` noise floor) — the plan simply never says so.

**Evidence:** `graphed-root-prompt.md:203-215` (R0.10a in full);
`graphed-latest/tests/frozen/core/m4/test_benchmark.py:34-53` (the frozen wall-clock ratio + the
1 s per-size budget + the noise floor); plan §3.3, §10 m50 bullet 2, §10 m51 bullet 3. Measured
headroom for the proposed shape: cba §optimizer §2 records 3.1 ms at N=16 and 16.7 ms at N=128
(ratio ≈ 5.4 against a 24.0 threshold).

**Suggested fix.** One sentence in §3.3: this benchmark is the project-plan-M4 anti-quadratic
carve-out to R0.10a (the only frozen wall-clock gate in the milestone set), it replicates the m4
noise floor and best-of-N timing, and the threshold's headroom is the measured 5.4× (cba §optimizer
§2). Everything else stays structural.

---

### 9. LOW — §2.3c's "frozen exhaustiveness test" is ambiguous against the repo's literal-list house style

**Section:** §2.3c, §10 m48 ("§2.3 dunder-parity and gak-classification exhaustiveness tests").

**Detail.** "every public gak function classified; no silent default" is only enforceable if the
frozen test enumerates the public gak surface **dynamically** and asserts each name has a
classification. The existing house pattern for gak parity pins an explicit literal tuple of names,
which would leave a future gak function silently unclassified — the exact failure the requirement
names. The trade-off matters and the plan should choose: a dynamic check is self-repairing (a new
gak function is fixed in `src`, never by touching the frozen test), a literal list is not
exhaustive. Same question for the dunder inventory ("enumerated at implementation from
`array.py`").

**Evidence:** `graphed-latest/tests/frozen/awkward/m24/test_interface_parity.py:37-78` — the
anti-drift pin iterates a hand-written 41-name tuple.

**Suggested fix.** Say "dynamically enumerated from gak's public surface at test time" (and likewise
for the `Array` dunder inventory), so the gate stays exhaustive and future additions are fixed in
source rather than by editing a frozen test.

---

### 10. LOW — the m48 ttgamma note ("no constant-Array constructor exists") is measurably too strong; `gak.full_like` exists and is parity-pinned

**Section:** §10 m48 ("the ttgamma flat SF weight is a constant — expressible only as arithmetic on
an existing per-event Array (no constant-Array constructor exists, cba §histogram §1)"); §4.1.

**Detail.** The note exists to spare the test-author a mid-freeze discovery, so it should point at
the best available spelling. `gak.full_like(arr, 0.98)` records a real graph op producing a
constant-valued Array shaped like an existing one — strictly better than `x*0 + 0.98` for
reproducing the ttgamma reference (`weight = np.full(n, sf)`), and it is already pinned by the m24
anti-drift parity list. The cba claim the note inherits was scoped to the session/array modules and
did not cover `graphed/awkward/functions.py`.

**Evidence:** `graphed-latest/python/graphed/awkward/functions.py:612-616` (`def full_like(arr,
value, *, dtype=None)` → `record_op("ak.full_like", …)`; also `ones_like` at `:421`,
`zeros_like` at `:415`); `tests/frozen/awkward/m24/test_interface_parity.py:74-76` (`full_like`
in the pinned parity list); cba line 196 (the grep that produced "no constant-Array constructor"
covered only session/array modules);
`graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:95` (`weight = np.full(int(ak.sum(sel)), sf)`).

**Suggested fix.** Reword the note: the flat SF is expressible in-graph as
`gak.full_like(<a per-event Array>, sf)` (or arithmetic on one); what does not exist is a
constant Array from *nothing*, which is the §11 parking.

---

### 11. LOW — §10's frozen-layout line leaves the consolidated-repo package directory unspecified, and the repo's per-subtree isolation needs a `pythonpath` edit for cross-dir helpers

**Section:** §10 preamble ("consolidated `graphed` = `tests/frozen/<pkg>/m48…`").

**Detail.** `<pkg>` is never resolved for m48/m49, though the consolidated repo's frozen tree is
partitioned by package (`awkward/ checkpoint/ core/ corpus/ debug/ frontend/ numpy/ preserve/`) and
the choice has mechanical consequences: pytest runs per subtree at per-milestone granularity, and
any helper imported **across** directories must be added to `pyproject.toml`'s `pythonpath` list.
The corpus-reference anchors will need `tests/_corpus` (already listed) plus, likely, a shared
`vary` fixture module. Naming the target directories now avoids the duplicate-basename collisions
the repo has already been bitten by (documented in the same pyproject comment).

**Evidence:** `graphed-latest/tests/frozen/` (8 package subdirs);
`graphed-latest/pyproject.toml:103-130` (testpaths, the per-subtree isolation comment naming the
m39/m40 and m5/m40 basename collisions, and the explicit `pythonpath` list of cross-dir helper
providers).

**Suggested fix.** Pin the directories in §10 (e.g. `tests/frozen/frontend/m48…`,
`tests/frozen/frontend/m49…`, `tests/frozen/preserve/m50…`, `tests/frozen/awkward/m51…`) and note
that any cross-dir helper must be added to `pythonpath`.

---

### 12. LOW — stale revision reference in §6.4b after the r9 encoding switch

**Section:** §6.4b.

**Detail.** "Labels are valid identifiers by construction (**§1.1 r8 canonicalization** — a dotted
spelling never reaches a label)". r9 replaced the r8 p-form canonical with the e-form; the
substance still holds, but a reader chasing "r8 canonicalization" lands on the superseded rule.
(The rest of the r9 propagation is clean — see the clean-lens notes.)

**Suggested fix.** "§1.1 canonicalization (r9 e-form)".

---

### 13. NIT — §1.1 leaves the canonical spelling of zero / negative zero unspecified

**Section:** §1.1; §10 m48 grammar anchor.

**Detail.** The m48 anchor must freeze the grammar exhaustively, and `"0"`, `"0.0"`, `"-0"`,
`"-0.0"` have no stated canonical form (`0` vs `m0`). Any choice is fine — the numeric-equality
rule rejects a mixed family either way — but a frozen grammar test needs the answer written down.

**Suggested fix.** One clause in §1.1: zero canonicalizes to `0`; a signed-zero spelling is
accepted and canonicalizes to `0` (or is rejected — either, stated).

---

## Clean-lens notes (checked, nothing to report)

- **(d) Determinism-gate compatibility — clean.** §3.2's "two fresh processes under differing
  `PYTHONHASHSEED` → byte-identical `compile_ir` output" is buildable and has an in-repo precedent
  (`graphed-latest/tests/frozen/awkward/m40/test_pack_key.py:160-167` spawns subprocesses
  overriding only `PYTHONHASHSEED`), and `compile_ir(...).ir` is already consumed as bytes
  (`aggregate.py:96`). §5.5's content-seeded randomness plus "run-to-run byte-identical" is the right
  claim shape, and the JER anchor deliberately asserts *bidirectional migration and pairwise
  distinctness*, not exact counts, so it survives RNG-stream differences across matrix legs. The
  reference comparisons are ULP-safe: `bin_values`/`fingerprint` round to `STABLE_DECIMALS = 6`
  (`graphed-corpus-latest/src/graphed_corpus/histograms.py:20,35-42`), so partition-order float
  summation cannot flip them — and r1 already downgraded the "bit-for-bit" claim to run-to-run only.
- **(e) Freeze-order after the r9 e-form switch — clean apart from finding 12.** The m48 grammar
  anchor is explicitly rewritten to r9 semantics and even records *why* ("freezing an earlier
  revision's rejections would hard-block this grammar"); m51's round-trip fixture uses the canonical
  `murf_5em1`; §9.1 keeps a p-form parse so legal datacard tags stay introspectable; §6.2's
  lexicographic-order caveat (`murf_10` before `murf_2`) is still correct under e-form. I found no
  anchor that freezes superseded r8 semantics.
- **(f) Orphan anchors — none.** Every m48–m51 anchor traces to a PART II requirement. The gaps are
  one-directional (finding 5).
- **Anchor spot-checks all held** (file:line read this session):
  `boost.py:88-98,100-122,166-174`; `m29/test_multi_weight_fills.py:82-99,93-99`;
  `m23/test_group_plan.py:68-77` (the `part_reads` read-counting source the §5.2b witness
  copies); `array.py:344-375,377-379`; `aggregate.py:54,89-93,96-104`;
  `checkpoint/runner.py:100-109`; `m4/test_systematics.py:28-53`; `m4/test_benchmark.py:10,40-53`;
  `preserve/m9/agc.py:38-66,94-118`; `corpus/m05/test_systematics.py:26-38`;
  `preserve/m9/test_reproduce.py:19-23`; corpus fixture counts (15 systematics references =
  ttbar 2 regions × 5 variations + ttgamma 5; the m48 weight subset is exactly 9).
- **§4.3's structural rewrite works.** The impact-set formulation is a real improvement over the
  equal-counts tautology and doubles as a partial §1.2 witness — but only partial, hence finding 2.
- **m50's structural demotion of the scaling claim is correct** (1 histogram object / 1 combine
  payload entry vs `N+1`, countable at the `_GroupReduce` seam) and R0.10a-compliant; likewise
  m51's demotion of the compression win to an R0.11 report measurement.
- **§5.4's refusal anchor carries a positive control** — exactly the discrimination this lens asks
  for; it should be the template for the other refusal anchors (§6.1c, §6.4f numpy).

---

## Verdict

**DIRTY.** Two HIGH findings must be resolved before freeze: §8.2 binds a worker-side error
mechanism that does not exist (finding 1), and two silent-wrongness guards — §1.2 label-identity and
§6.1c's `.plan()` refusal — have no frozen anchor anywhere in m48–m51 (finding 2). Five MID findings
(a measurably wrong pair of pinned integers, an under-specified cross-repo m49 anchor, five
un-anchored binding requirements, a self-derived m51 reference, an unpinned preservation
constructor) plus the R0.10a inconsistency would each cause avoidable churn at TEST_SANITY.

Everything else in this lens is in good shape: the r9 encoding switch is correctly propagated into
the anchors, determinism-gate compatibility is sound, the anti-tautology fixes from r1 held up under
re-examination, and no anchor is an orphan.
