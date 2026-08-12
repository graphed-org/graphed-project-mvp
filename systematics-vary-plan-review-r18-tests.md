# systematics-vary plan — review round 10, TEST ARCHITECTURE lens

- **Plan revision reviewed:** r18 (`systematics-vary-plan.md`, 4209 lines, read in full: header, PART I,
  §§1–12, milestones §10, anchors appendix, revision history).
- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, traceability (requirement ↔ anchor), and testability-as-stated (can the test-author
  actually build the named fixture).
- **Date:** 2026-07-30.
- **Verification roots used (all facts below were measured by me in this session):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (incl. its `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (incl. its `.venv`, boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
  - probe scripts under the session scratchpad (`probe33.py`, `probe_nodes.py`, `probe_props.py`,
    `probe_surface.py`)
- **Scope note:** owner-locked decisions (naming, functional surface, e-form encoding, event-context
  attachment, record-time expansion, m48–m51 scope, the Phase-2 pull-in) were not relitigated. No
  "OPEN ITEMS (owner)" block is present in the header.

---

## Findings (ordered by severity)

### 1. BLOCKER — the r18 PROPERTY disposition rule (§2.2) and the m48 property gate (§2.3a) are measurably wrong for `NumpyArray.T`: they freeze an assertion a correct implementation must fail, and the rule they encode silently drops universes

**Sections:** §2.2 (r18 property discovery rule), §2.3a ("The PROPERTY half is enumerated too"),
§10/m48 anchor "plus the PROPERTY half of §2.2's r18 disposition rule".

**What the plan binds.** §2.2: "for every non-underscore property on `type(graphed.nominal(v))`,
**`node_id` and `session` raise `AttributeError`** … and **every other property is answered EAGERLY
on the nominal member**". §2.3a turns that into a frozen gate: "a third enumeration over
`inspect.getmembers(type(graphed.nominal(v)), lambda m: isinstance(m, property))` … asserting each
discovered name resolves per §2.2 — … every other property answers eagerly on the nominal member and
**records NO node (witnessed by a `Session.node_count()` delta of 0 across the access)**." m48's
anchor repeats it and names `varied.dtype` as the representative, citing the motivating property set
as `shape`/`dtype`/`ndim`/`T` at `python/graphed/numpy/array.py:78,82,86,160`.

**Measured (this session, `graphed-latest@ff7c607`).** `T` is in that enumerated set and it is **not**
metadata — it is a property that RECORDS a graph op:

```
$ .venv/bin/python  # Session(NumpyBackend()); a = gnp.arange(sess, 0, 12)
props: ['T', 'dtype', 'ndim', 'node_id', 'session', 'shape']
  .T:     node_count delta=1 -> NumpyArray node 1
  .dtype: node_count delta=0 -> Int64DType int64
  .ndim:  node_count delta=0 -> int 1
  .shape: node_count delta=0 -> tuple (None,)
```

Source: `python/graphed/numpy/array.py:159-161` — `@property def T(self) -> Array: return
self.transpose()`, and `transpose` is `self._session.record_op("transpose", [self], params)`
(`:150-156`). The plan's own citation `:160` IS `T`.

**Consequence, both halves.**
(a) *The gate is red against a correct implementation.* A correct `Varied` must BROADCAST `T` (a
per-label transpose, exactly the §2.3a disposition given to `Array`'s methods), so `varied.T` returns
a `Varied` and the access records ≥1 node — failing both the "answers eagerly on the nominal member"
and the "`node_count()` delta of 0" clauses. Frozen ⇒ Test Dispute or an integrity violation.
(b) *Worse, the rule as written mandates the failure it exists to prevent.* An implementer who obeys
it makes `varied.T` return the NOMINAL universe's transpose — a single `Array` — silently discarding
every non-nominal universe. That is verbatim the §2.5 "confidently wrong" class the r18 rule was
introduced to close (the §2.2 rationale: "would resolve through the label-mapping field access,
recording a graph node named `\"dtype\"`").

The enumeration cannot dodge `T`: it is bound as "a discovery rule over properties, not a two-name
list", and the fixture must be numpy-idiom because the floor names `varied.dtype`.

**Suggested fix.** Split the property disposition the same way §2.3a already splits methods, keyed on
what the property does rather than on its being a property: properties answered from the form
(`_form_meta`-backed: `shape`/`dtype`/`ndim` — measured delta 0) are *eager-metadata*; properties that
record (`T`, and any future one) are *broadcast* and return a `Varied` whose `graphed.labels` match the
input's; `node_id`/`session` raise. The gate then asserts per discovered name according to its bound
class, with a behavioural probe per class — `varied.dtype` as the eager representative (delta 0) and
**`varied.T` as the broadcast representative** (returns a `Varied`, labels preserved). Note also that
`_form_meta` (`python/graphed/array.py:283-290`) FALLS BACK to recording a `field` op when the form
does not model the name, so "answered from the form" must be stated as the criterion, not assumed.

---

### 2. HIGH — m48's §7.2 "schema absence" anchor is vacuous as worded: all three named schemas are dataclasses, so their key sets cannot differ between a varied and an unvaried program

**Sections:** §7.2 ("`ExecResult`/`Plan`/monitor **schemas** do not change … the absence is a frozen
m48 anchor … worded over **schema KEY SETS**"), §10/m48 anchor "§7.2 schema absence: the
`ExecResult`/`Plan`/monitor payload schema **KEY SETS** are identical for a varied and an unvaried
program".

**Measured.** All three are dataclasses whose field names are class-level constants:

- `Plan` — `python/graphed/core/execution.py:206-217`: `process, combine, empty, tasks, next_tasks,
  stop, open_once`.
- `ExecResult` — `:219-224`: `value, n_partitions, n_combines, stopped`.
- the monitor payload — `TaskEvent`, `:335-351` (`@dataclass(frozen=True)`): `phase, key, worker, t,
  partition, n_entries, bytes_read, error`; `emit_task` passes the instance straight through
  (`:378-384`), there is no per-event dict construction.

A varied program and an unvaried program therefore produce instances of the *same classes*. Their
field-name sets are equal by construction — including after an implementer ADDS a field, which is the
only thing the anchor exists to detect. The anchor passes tautologically.

This is the same defect class the plan already repaired for §6.3 in r17 (the placeholder
`assert "<new key>" not in node["params"]` replaced by a literally spelled key-set equality); the
repair was not applied here.

**Second-order consequence.** §6.1a's r18 reasoning for introducing `graphed_histogram.unpack`
rests on "adding a `Plan` field is foreclosed by §7.2's m48 schema-KEY-SET anchor". As worded that
anchor forecloses nothing — an added `Plan.variation_layout` field is invisible to it.

**Suggested fix.** Word the anchor as a literal-expected-set equality, the §6.3 shape:
`{f.name for f in dataclasses.fields(Plan)} == {"process","combine","empty","tasks","next_tasks",
"stop","open_once"}`, likewise for `ExecResult` and `TaskEvent`, spelled out in the test rather than
read back from the class or compared against a sibling run. (The varied-vs-unvaried comparison may
ride along as a sanity assertion, as m05's equal-counts does in §4.3.)

---

### 3. HIGH — m49's §8.2(i) image-cardinality clause freezes the wrong integer: the record→reduced map's image over the §3.3 topology is **2N+2** distinct reduced ids, not N+1 — and its companion set-membership clause is false for the source record

**Section:** §10/m49 "**Plus a PARTITIONING clause the §3.3 topology makes exact, r18** … the map's
image over the topology has exactly **N + 1** distinct reduced ids — matching the `stages == N + 1`
shape §3.3 already pins"; same bullet, "every surviving record id maps to a `(reduced_id,
member_index)` whose reduced id is **in the compiled output/stage set**".

**Measured (this session, `graphed-latest@ff7c607`, the §3.3 builder verbatim: D=500 prefix ops,
per universe {1 fork, K=50 chain ops, 1 terminating reduction}, every reduction an output):**

```
N=16   report: stages 17, reduced_nodes 34, reachable 1333   kinds: {source: 1, stage: 17, reduction: 16}
N=128  report: stages 129, reduced_nodes 258, reachable 7157 kinds: {source: 1, stage: 129, reduction: 128}
```

The reduced graph is `1 source + (N+1) stages + N reductions = 2N+2` nodes — which is exactly the
`reduced_nodes == 2N + 2` literal §3.3 already pins. Since the accessor is bound as
`record_node_id -> (reduced_node_id, member_index | None)` over *every surviving record id*, its image
over this topology contains the source's reduced id, all N+1 stage ids and all N reduction ids: **34
at N=16, 258 at N=128**. A test-author freezing `len(set(...)) == N + 1` freezes an assertion a
correct implementation fails by a factor of ~2.

The same bullet's set-membership clause is false for one record too: the source's reduced node is
neither an output nor a stage (`kind == "source"`), so "whose reduced id is in the compiled
output/stage set" refuses a correct map's answer for the source record id.

**Suggested fix.** Either scope the cardinality to what it is actually about — "the image of the
**op** record ids (prefix + per-universe chains) is exactly **N + 1 distinct STAGE ids**" — or state
the whole-topology number as `2N + 2` and cite `reduced_nodes`, not `stages`. Correspondingly widen
the membership clause to "the compiled reduced-node set" (source/stage/reduction), or restrict it to
op records. The anti-degeneracy purpose r18 states is already carried by the sibling clause "each
universe's chain maps to a reduced id DISTINCT from every other universe's", which a constant map
fails; the cardinality clause only needs to be *true*.

---

### 4. HIGH — two m48 anchors are specified over fill programs that cannot execute: they mix a per-event and a per-object value in two AXES, and the plan binds broadcast only for weight factors

**Sections:** §10/m48 "**§6.1d link-kind (1) ancestor-VALUE re-indexing, asserted over the VALUE**
(r18) … `h.fill(events.MET.pt, sel.Jet.pt)` with `sel = events[varied_mask]` compared ELEMENTWISE";
and "`graphed.universe(ctx, label)`/`graphed.nominal(ctx)` return a context that is a CHILD … —
**asserted over the resulting VALUE** (r15)", whose §2.2/§6.1d program is
`h.fill(graphed.nominal(sel).Jet.pt, sel.MET.pt)`.

**Measured.** The evaluator flattens **each axis input independently** and hands them to
boost_histogram: `axes = [_flat(v) for v in values[: self.n_axes]]` then `h.fill(*axes, …)`
(`graphed-histogram src/graphed_histogram/boost.py:39-47,58-71`). boost_histogram then requires equal
lengths across axes — measured, bh 1.8.0:

```
bh.Histogram(Regular(3,0,10), Regular(3,0,10)).fill(np.arange(3.0), np.arange(5.0))
-> ValueError: spans must have compatible lengths
```

In both named programs, axis 1 and axis 2 have different granularity: `events.MET.pt` is per-event
(one entry per row) while `sel.Jet.pt` is per-object (n_jets entries after `_flat`). §6.1d's
re-indexing rule fixes the *row count* (`|events|` → `|sel|`) but not the *structure*, and the
broadcast seam §6.1d binds is scoped to weight factors only ("**Every weight factor** the fill applies
… is broadcast to the fill's value structure"); nothing broadcasts one axis value against another.
So a correct implementation raises at execution on both fixtures, for a reason that has nothing to do
with what the anchors assert.

A test-author will discover this mid-freeze and will most likely "repair" it by making the fixture
one-jet-per-event (silently weakening the re-indexing assertion to a degenerate case) or by flattening
one side (which §6.1d explicitly forbids for per-object fills).

**Suggested fix.** Restate both fixtures so the two contexts meet on inputs of the SAME granularity —
the mechanism under test (ancestor-value re-indexing / universe projection) does not need a per-object
axis:
- link kind (1): `h.fill(events.MET.pt, sel.MET.pt)` (both per-event; without re-indexing the two
  arrays have different row counts and the fill fails, so the anchor still discriminates), or a
  one-axis `h.fill(events.MET.pt)` whose *weight* comes from `sel` (unification without re-indexing
  then length-mismatches).
- link kind (3): `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)`, compared elementwise against the
  manually projected reference.
If a mixed-granularity multi-axis fill is intended to be supported at all, §6.1d must bind the
broadcast of axis values against each other — but that is new scope, and nothing else in m48–m51 asks
for it.

---

### 5. MID — m48's anchor still freezes §2.3e(3)'s superseded "the refusing class is **exactly** `{gak.join}`", which r18 replaced with containment + a monotone count

**Sections:** §2.3e(3) (r18): "**`gak.join` IS IN the *refusing* class and the refusing COUNT is ≥ the
freeze-time count** — containment plus a monotone count, **never an exact set** (r18 — r16 wrote
'exactly `{gak.join}` at freeze time' while the same sentence provided for a future gak boundary verb
arriving with its classification in `src`; both cannot hold…)". §10/m48, the gak-classification bullet,
still reads: "asserts the exempt set is exactly {*eager-metadata*, *refusing*} **plus §2.3e(3)'s
MEMBERSHIP floor** (**the refusing class is exactly `{gak.join}` at freeze time** — measured, the only
boundary verb among gak's 65 public functions … r16 …)".

The §10 anchor list is explicitly "the acceptance skeleton the test-author starts from"; freezing the
r16 wording re-installs precisely the maintenance trap r18 removed (a frozen `refusing == {gak.join}`
equality reds the moment a future gak boundary verb arrives with its classification in `src`, which is
where the self-repairing rule wants it). Measured, gak's public surface is 65 functions with `join` at
`python/graphed/awkward/functions.py:18` as the only boundary verb today — so the operand is right and
only the *shape* of the assertion is stale.

**Suggested fix.** Replace the parenthetical in the m48 bullet with §2.3e(3)'s r18 form: "`gak.join`
IS IN the refusing class and `len(refusing) >= <freeze-time count>`", keeping the eager-metadata
return-annotation clause and the broadcast-count floor as they are.

---

### 6. MID — m50's new MIXED-MODE anchor cannot discriminate the per-output MODE field it is introduced to witness (and the same fact contradicts §6.1a/§9.1's `unpack(value)` arity)

**Sections:** §6.1c ("the **layout records the per-OUTPUT MODE** (sibling / axis) — the information
the frontend unpacker … needs to choose between `{label: hist}` and a bare histogram … A mixed-mode
plan is m50's anchored case, since **in a single-mode plan the shape is inferable from the key form
alone** and the MODE field could be omitted entirely"); §10/m50 "**MIXED-MODE PLAN — the per-OUTPUT
MODE's only reason to exist (r18)**".

**Why it does not discriminate.** §6.1c binds the slot keys as `(output, label)` in sibling mode and
`(output, None)` in axis mode, and labels are non-empty strings by §1.1. The key form is therefore
**per output**, so in a MIXED plan too, an unpacker can decide each output's shape from its own slot
keys alone: any `(output, None)` slot ⇒ bare axis-mode histogram; `(output, str)` slots ⇒
`{label: hist}` (or a bare hist for the single-`"nominal"`-slot unvaried case, since a varied output
always carries ≥2 labels). An implementation that never records the MODE passes the m50 mixed-mode
anchor exactly as it passes every single-mode anchor. The anchor's stated *raison d'être* is not met;
§6.1c's MODE requirement has no discriminating witness anywhere in m48–m51.

**The dilemma shows up again as an arity contradiction.** §6.1a and §9.1 spell the unpacker
`graphed_histogram.unpack(value) -> dict[str, bh.Histogram | dict[str, bh.Histogram]]` while
describing it as operating "over the executed plan value **plus the plan's layout**". Measured, the
layout is not reachable from the value: `ExecResult.value` is exactly the combine output
(`python/graphed/core/execution.py:219-224`), `Plan` has no layout field (`:206-217`), and `layout`
lives on the `_GroupReduce` instance that is the plan's `process`
(`graphed-histogram src/graphed_histogram/boost.py:100-117,254-292`). So either the value suffices
(and the layout mention — and the MODE field — are redundant), or the bound one-argument spelling is
unimplementable. m48 freezes an anchor "worded over §6.1a's bound UNPACK verb", so the test-author must
pick one.

**Suggested fix — pick one horn explicitly:**
- *(lazier, and consistent with the measured key space)* bind `unpack(value)` over the slot-keyed
  value alone, delete the per-output MODE from §6.1c (and from m50's target line), and re-word the m50
  mixed-mode anchor as what it genuinely witnesses: mixed-mode unpacking + `_GroupZero`'s per-slot
  spec across two DIFFERENT specs, which nothing else in m48–m51 reaches; or
- keep the MODE field, bind the unpacker's second operand explicitly (`unpack(value, plan)` /
  `unpack(value, layout)`, spelling pinned at m48 freeze), and give the MODE a discriminating anchor —
  e.g. an axis-mode output whose single slot is asserted to be MODE-tagged in the layout, so a
  key-form-only implementation is red.

---

### 7. LOW — m48's §1.2 anchor asserts over a "token" that no public surface exposes

**Section:** §10/m48 "**§1.2 label-out-of-identity** … NO node in the store carries any label string
in its **params or token**".

**Measured.** `GraphStore.nodes()` yields dicts with keys `{id, output, inputs, kind, name, params}`
(plus `n_members`/`members` for a `stage`); there is no `token` key, and the PyO3 surface exposes no
token accessor (the `#[pymethods]` block on `GraphStore` is `add_source`/`add_op`/`add_reduction`/
`add_external`/`add_exchange`/`add_join`/`node_count`/`to_dot`/`serialize`/`deserialize`/`nodes`/
`outputs`/`reduce`/`reduce_incremental`/`reduction_report`). The token is derived from kind+name+params
(`src/node.rs:107-137,231-236`), so `name` + `params` is the writable substitute — and the anchor's own
second clause ("renaming every label leaves `compile_ir(...).ir` byte-identical") strictly subsumes the
token half anyway. Two smaller notes for the same anchor: a reduced `stage` node keeps its content in
`members` (each with its own `name`/`params`), not in `params`, so an implementation of "no label in
params" must recurse into `members`; and the m29 house pattern for reaching the store from a frozen
test is the private `s._store.nodes()` (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84,95`).

**Suggested fix.** Re-word as "no node's `name` or `params` (including a stage's `members`' names and
params) contains any label string, and renaming every label leaves `compile_ir(...).ir` byte-identical",
dropping "token" or noting it is covered by the byte-identity clause.

---

## Lens areas checked and found CLEAN (no finding)

- **(c) R0.10a.** §3.3's `time(128)/time(16) < 16.0` is the single frozen wall-clock gate and is
  explicitly named as a carve-out backed by the M4 mandate; I re-measured the topology at
  `graphed-latest@ff7c607` (N=16 → 4.08 ms / 1333 reachable nodes; N=128 → 22.26 ms / 7157) — ratio
  5.45, consistent with the plan's 5.64 and ~2.9× under the gate, and `reachable_nodes` IS in
  `reduce()`'s report (so the self-scaling variant §3.3 offers is buildable). m4's own style is
  reproduced correctly (`tests/frozen/core/m4/test_benchmark.py`: `SIZES` 8× span, gate `24.0`,
  best-of-3, `base = max(times[SIZES[0]], 1e-4)`). Every other performance claim (§6.2 axis scaling,
  §6.4c compression, m50's N≈100 comparison, m51 skim sizes) is demoted to an R0.11 implementer report,
  and m50's scaling anchor is structural (combine-payload entry counts), not timed.
- **(d) Determinism.** m48's two-fresh-processes/differing-`PYTHONHASHSEED` `compile_ir` byte-identity,
  m49's plan-byte + `task_id` twin, and m51's manifest-byte anchor are all in the strong R22.3 form;
  the m49 fixture constraints (BY-VALUE `DurablePlan` via `OpSpec.from_callable`, module-level closure
  operands) are exactly the two conditions that make that anchor neither green-by-accident nor red
  against a correct implementation. §6.4g's byte-identity is correctly bound as a SAME-PROCESS
  comparison rather than a committed parquet blob.
- **(f) Traceability.** I walked every binding PART II clause against §10. The previously-open gaps are
  closed: §2.5's diagnostic channel, §5.3's stats verb, §3.4, §5.4, §5.5(a)/(b), §6.1b arity, §6.1c
  `.plan()` refusal + indices layout (witnessed by the §1.2 dedup/replication clause), §6.2's carrier
  and declaration contract, §6.4a's two predicates with per-predicate positive controls, §6.4b's field
  flattening + collision, §6.4d's negative anchor, §7.3/§7.4, §8.1's `__hash__`, §8.2(i)-(iii), §9.1's
  full verb list (each with a milestone and a "spelling pinned at freeze" clause) and §9.2 all carry at
  least one anchor, and no anchor traces to nothing. Item 2 above is the one place where an anchor
  exists but does not actually constrain its requirement.
- **(g) Testability of fixtures.** Spot-verified the load-bearing ones: the corpus ships 23 reference
  JSONs of which 15 are systematics (m48's 9 = ttbar 4j1b/4j2b × {nominal, btag_up, btag_down} +
  ttgamma × {nominal, pho_up, pho_down} — all present by name); every gak function the corpus port
  needs exists (`prod`, `sum`, `with_field`, `num`, `firsts`, `local_index`, `full_like`, `flatten`,
  `zip`, `where`, `values_astype`); `bin_values`/`fingerprint` work off `h.values()` so a
  `bh.Histogram` from `graphed-histogram` is directly comparable; §5.2b's read-counting source has a
  working frozen precedent (`graphed-histogram tests/frozen/m23/test_group_plan.py:31-44,68-77`,
  `assert len(src.part_reads) == 4`); §6.3's literal params key set is measured-correct
  (`{"spec","n_axes","weighted","sampled"}`, `graphed-histogram src/graphed_histogram/boost.py:198-212`,
  `n_weights` added only when `len(weights) > 1`); §2.3d's discovery surface reproduces exactly
  (annotation-wide filter over `graphed.__all__` → `['aggregate_plan','apply','join','join_plan',
  'pack_key','read_columns','repartition','shuffle_plan']`, 8 verbs; gak public = 65;
  `dir(Array)` public = 6; `NumpyArray` public = 32). The m48 cross-repo edit is sound: measured,
  `graphed-histogram`'s CI already installs `graphed … @main` from a git URL
  (`.github/workflows/ci.yml:14,37`), so the vendoring requirement is the only fixture edit m48 needs.
- **(e) Freeze order.** The r7 and r18 sweeps hold: every sibling-mode-only claim (§6.1a shapes, §6.1b
  arity, §1.2's two clauses) carries its scoping; §6.1c's `.plan()` refusal is deliberately general and
  m50 does not contradict it; m48's per-class disposition floor is CONTAINMENT so m51's added
  *accepting* member cannot red it; `to_parquet` is out of m48's table entirely; m48 defers §5.4's
  message shape to m49; §1.1's grammar anchor is written over the r9 e-form with the superseded
  rejections removed (the unconstructible "label == `nominal`" case is correctly gone). Finding 5 is
  the one residual stale-wording instance.
- **(a)/(b) Non-vacuity and mechanism.** The traps the plan documents are handled and I found no new
  instance beyond items 2 and 6: §4.3's equal-counts tautology is replaced by the readable non-weight
  input-id comparison (with the withdrawn intersection form explicitly NOT frozen); §5.2a/c use
  independently hand-built oracles rather than self-derived lengths; m51's superset anchor uses an
  eager out-of-graph reference; m50's declaration anchor uses a literally spelled expected label list
  (the r18 circularity correction is right — `graphed.labels(h)` DERIVES FROM the axis bin set);
  m49's JER-SF partition-invariance witness compares concatenated partition-local values/masks rather
  than a weighted float histogram, and correctly rules out the partition-blind `Session.materialize`
  as the oracle (measured signature `materialize(self, array)`, `python/graphed/session.py:291-301`),
  with `SequentialRunner`'s sorted task order (`core/execution.py:450-457`) supplying the determinism
  it needs; m48's origination anchor (same node id, different handles, different fill label sets) is a
  genuine mechanism witness, as is the m50 carrier witness (distinct External `content_hash`es).

---

## Verdict

**DIRTY.** 1 BLOCKER, 3 HIGH, 2 MID, 1 LOW.

The BLOCKER (finding 1) and finding 4 both freeze assertions a correct implementation must fail, and
finding 3 freezes a wrong integer — all three are r18 additions, and all three are cheap to correct
without touching an owner-locked decision. Finding 2 is a binding requirement whose only anchor
constrains nothing, and it also invalidates one of r18's own design arguments. Findings 5–7 are
wording/consistency repairs. Everything else in the test architecture — the R0.10a discipline, the
determinism anchors, the per-repo anchor partition and its `importorskip`/vendoring analysis, and the
non-vacuity floors on the dynamic gates — verified clean against the pinned roots.
