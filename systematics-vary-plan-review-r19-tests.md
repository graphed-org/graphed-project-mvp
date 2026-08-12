# systematics-vary-plan review — round 11, revision r19 — LENS: TEST ARCHITECTURE

- **Lens:** test architecture (non-vacuity/discrimination, witness-of-mechanism R0.10, R0.10a
  wall-clock/size, determinism-gate compatibility, freeze-order hazards, traceability, buildability).
- **Plan revision reviewed:** r19 (`systematics-vary-plan.md`, 4545 lines, read in full — Part I,
  §§1–12, Anchors appendix, revision history).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts below were measured by me, this session):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe`
  - `/private/tmp/claude-501/graphed-corpus-latest`
  - `/private/tmp/claude-501/graphed-exec-check`, `/private/tmp/claude-501/uproot5-graphed` (not
    needed for the findings below)
  - boost_histogram 1.8.0 in `graphed-histogram-latest`'s environment.
- **Owner-locked decisions** were treated as fixed; nothing below asks for a different choice.
  No `OPEN ITEMS (owner)` block exists in the header (grepped).

## What I re-measured before writing

| Claim under test | Result |
|---|---|
| `NumpyArray.T` records; `shape`/`dtype`/`ndim` do not (r19 BLOCKER premise) | **Confirmed.** `T` is `@property def T: return self.transpose()` at `python/graphed/numpy/array.py:159-161`, `transpose` → `record_op` at `:154-157`; `shape`/`dtype`/`ndim` are `_form_meta`-backed at `:77-87`. Discovered properties on `NumpyArray` = `['T','dtype','ndim','node_id','session','shape']`; on `Array` = `['node_id','session']`. |
| §3.3 topology reduces to `{source:1, stage:N+1, reduction:N}` (r19 HIGH, `2N+2`) | **Confirmed**, raw `GraphStore` *and* frontend `compile_ir`: N=3 → 8 nodes `{source:1,stage:4,reduction:3}`; N=16 → 34 `{1,17,16}`; N=128 → 258 `{1,129,128}`. |
| `GraphStore.nodes()` exposes no token; stage members carry `kind`/`name`/`params` (r19 LOW, "or token" dropped) | **Confirmed.** Node keys `{id,output,inputs,kind,name,params}` (+`n_members`/`members` on a stage); member keys `{kind,name,params,inputs}`. |
| m23 indexes the group-plan value by BARE output name (r19 BLOCKER-2 premise) | **Confirmed**, `graphed-histogram tests/frozen/m23/test_group_plan.py:74-75,86,89,99`. |
| `Plan`/`ExecResult`/`TaskEvent` field sets (r19 HIGH, literal key sets) | **Confirmed** verbatim at `python/graphed/core/execution.py:206-217,219-224,335-351`. |
| `Session.record_op` validates only `op_form`, never lengths (r19 HIGH, §2.1(b) row space) | **Confirmed**, `python/graphed/session.py:142-168`. |
| bh 1.8.0 refuses unequal-length axis fills (r19 MID, same-granularity fixtures) | **Confirmed:** `bh.Histogram(Regular(3,0,10),Regular(3,0,10)).fill(arange(3.),arange(5.))` → `ValueError: spans must have compatible lengths`. |
| Corpus b-tag SF operand is the pt-CUT jets (r19 LOW) | **Confirmed**, `graphed-corpus src/graphed_corpus/analyses/systematics.py:60-76` (`good = jets[jets.pt > 25]`; `sel_jets = good[sel]`; `_btag_weight` products per-jet SF over `axis=1` at `:25-36`). |
| gak public surface = 65, `join` present; annotation-wide filter over `graphed.__all__` = 8 verbs | **Confirmed** (`['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`). |

Every r19 delta I could check measured out correct. The findings below are gaps r19 *created* or
left open, not corrections to r19's measurements.

---

## Findings (severity-ordered)

### 1. HIGH — §7.2's new `aggregate_plan` seam is an m48 `graphed` Implementation Target with no `graphed`-side m48 frozen anchor, and r19 removed the only plan-shaped anchor from that half

**Section:** §7.2 (plan `:2224-2245`), §10/m48 target line (`:2650-2655`), §10/m48 `graphed` half
(`:2672-2676`), §10/m48 §7.2 schema-absence anchor (`:2951-2963`).

**Detail.** r19 binds a NEW seam on `graphed`'s `aggregate_plan` ("gains ONE pinned seam … (α) lets
the caller see the compiled output list before the worker closure is finalized … (β) accepts
per-plan variation metadata to be carried as an additive field on the shipped closure") and adds it
to m48's target line ("including §7.2's r19 `aggregate_plan` SEAM"). That is new source in
`graphed/python/graphed/aggregate.py`. The DoD gate is per repo: ≥90 % line+branch diff coverage on
new/changed lines **with covering hits from that repo's frozen suite**. I read every anchor assigned
to `graphed`'s `tests/frozen/frontend/m48` in §10 (§1.1 grammar, §2.x semantics, §2.6 lineage, §1.2
label-out-of-identity + its scope positive control, §3.2 determinism, §7.2 schema absence, §2.3d
dispositions, §2.1 stacking, §2.2 `apply`, §2.3b, §2.5 diagnostic, the parity/gak gates, the
frontend halves of §2.6/§6.1d): **none of them calls `aggregate_plan` at all.**

Two facts make this structural rather than incidental:

- `graphed`'s m48 half cannot build a *varied* plan even if it wanted to — §2.3d bindingly makes
  `graphed.aggregate_plan` **refuse** a `Varied` output (`:677-681`), and "the varied route to a
  plan is the §6.1c group API", which lives in `graphed-histogram`. So the seam's only real consumer
  (`graphed_histogram.plan()`, `boost.py:282-292` — measured: `layout` built at `:282`, the
  `aggregate_plan` call at `:286`) is in the *other* repo, whose frozen suite does not count toward
  `graphed`'s diff coverage.
- r19 itself converted the one `graphed`-side anchor that previously implied a run — §7.2's
  schema-absence anchor, r18 wording "on a varied program … never against a sibling unvaried run" —
  into a purely **static** assertion over `dataclasses.fields(...)` (`:2951-2963`). Measured, all
  three are dataclasses with class-level field lists, so the r19 wording is correct on its own
  terms; the side effect is that `graphed`'s m48 half now contains no plan construction whatsoever.

Half of the seam is worse: **(β) has no consumer until m49** (§8.2(i)'s `variation_labels`). Landing
(β) at m48 puts unreachable code in `graphed` for a whole milestone.

The plan has used exactly this argument three times to move work (r14 moved §3.4 out of m48
"New m48 source with zero m48 frozen coverage either fails the DoD's ≥90 % diff-coverage-from-the-
frozen-suite gate or is covered only by `tests/extra`, which that gate excludes"; r16 moved m50's
`{output: [labels]}` listing; r17 moved it again). The same argument applies verbatim here and was
not applied.

**Evidence.** `python/graphed/aggregate.py:68-108` (`aggregate_plan(*outputs, reduce, combine,
empty, externals, backend, steps_per_file, partitions) -> Plan[V]`; compiles internally at `:95`;
constructs the frozen `_PartitionReduce` at `:96-104`). `graphed`'s existing frozen coverage of it
is `tests/frozen/frontend/m5/test_aggregate_plan.py` (m5, not m48). Plan `:2237-2241`, `:2650-2655`,
`:2672-2676`, `:2951-2963`.

**Suggested fix.** Add one `graphed`-side m48 anchor over the seam, worded over its observable
(spelling pinned at m48 freeze): on an UNVARIED multi-output `aggregate_plan` build, the caller
observes the compiled output list/ids **before** the worker closure exists, and the resulting `Plan`
behaves identically to the m5 call shape (positive control: `tests/frozen/frontend/m5`'s own program
still runs unchanged), plus a witness that `aggregate_plan` compiles **exactly once** for that build
(§7.2's own "MUST NOT compile a second time"). Alternatively split the seam: land (α) at m48 with
that anchor, and (β) at m49 with the §8.2(i) anchor that consumes it.

---

### 2. MID — §6.1b/§6.2's r19 `S`/`W` lowering definition is binding and unanchored: no m48–m51 anchor carries a label borne ONLY by a `Varied` `sample=`

**Section:** §6.1b (`:1436-1450`), §6.2 (`:1681-1686`), m49 arity anchor (`:3299-3302`), m50 anchors
(`:3394-3404`, `:3473-3491`).

**Detail.** r19 redefines `S`/`W` by **lowering behaviour**: `S` = labels borne by any axis value
**or by a `Varied` `sample=`**; `W` = labels borne ONLY by weight factors. The stated reason is
real — "a label borne solely by `sample=` cannot ride the weight loop, which re-fills with different
weights against a FIXED sample column, so it must lower as a sibling". So a sample-only label is a
sibling fill node in *both* modes (`1 + |S| + |W|` at m49, `1 + |S|` at m50).

I grepped every occurrence of `sample` in the anchor lists. The only anchor that mentions a
`Varied` `sample=` is m48's fold-order bullet (`:3033-3040`), which asserts the **fold position**
("axis values in argument order, then ambient, then explicit factors in list order, then `sample=`")
and that it is "ACCEPTED/expanded rather than raising `AttributeError`". Nothing asserts its
**lowering class**:

- m49's arity anchor (`:3299-3302`) is worded "`1 + |S| + |W|` fill nodes" with no fixture
  constraint; a fixture without a sample-borne label cannot distinguish `S` from `W` membership for
  such a label, and both classifications yield the same total.
- m50's equality anchor is a mixed shift+weight program (no `sample=`); m50's scaling anchor is
  explicitly "scoped to WEIGHT labels only" (`:3477`); (i-bis) and the declaration anchors are
  single-histogram shapes.

So an implementation that classifies a sample-only label into `W` passes every frozen anchor at m49
and then, in m50's axis mode, folds it into the evaluator weight loop — producing a
**wrong histogram** (the same sample column reused across universes) with no frozen test able to
see it. This is the "binding but unanchored" class the plan closed for §5.3 (r12), §2.3d/§2.2 (r13)
and §9.1's listing (r16).

**Evidence.** Plan `:1441-1450`, `:1683-1686`, `:3299-3302`, `:3477`; grep of `sample` over the plan
(lines listed above). Measured, `Histogram.fill` appends `sample` to the same `inputs` list with no
type check, `graphed-histogram src/graphed_histogram/boost.py:160-178`.

**Suggested fix.** Extend m49's `1 + |S| + |W|` arity anchor's fixture with a label borne ONLY by a
`Varied` `sample=` and assert it contributes a sibling node (i.e. counts in `S`), and extend m50's
equality anchor (or add a small one) with the same label in axis mode, asserting it lowers as a
scalar-labelled sibling equal to its sibling-fill decomposition.

---

### 3. MID — §1.1's r19 digit-count normalization has no boundary anchor; m48's grammar anchor is passed by the very off-by-one implementation r19 wrote the rule to forbid

**Section:** §1.1 (`:264-276`), m48 grammar anchor (`:3165-3173`).

**Detail.** r19 added the normalization explicitly: the magnitude test runs on "(the input's mantissa
digits after removing the decimal point and stripping leading zeros) + (the exponent adjusted for
where that decimal point sat), NOT a naive 'mantissa digits + exponent', which is off by one at the
boundary for a dotted mantissa (`"1.5e31"` renders as `15` followed by 30 zeros = 32 plain digits,
exactly at the cap and LEGAL, while the naive sum gives 2 + 31 = 33 and rejects it)". The same
paragraph then asserts: **"the cap boundary is precisely where m48 freezes the magnitude message as
a case distinct from the generic tag-length one."**

m48's grammar anchor does not carry that boundary. Its magnitude clause reads in full:
`"1e40"` (integer-valued, 41 plain digits) is rejected with a message naming the magnitude,
"alongside the existing `"1e-8"` → `eps_1em8` positive" (`:3171-3173`). Arithmetic: the naive
implementation computes 1 + 40 = 41 for `"1e40"` → rejects → **anchor green**; and computes
2 + 31 = 33 for `"1.5e31"` → rejects a LEGAL tag → **no anchor sees it**. The anchor therefore
cannot discriminate the exact implementation error r19 introduced the rule for, and §1.1's own
sentence about what m48 freezes is not true of m48's anchor list.

(Secondary, same paragraph: r18/r19's "count BEFORE any rendering" rule, justified by
`"1e1000000000"` needing a one-billion-digit materialisation under render-then-measure, is likewise
unwitnessed. I do not recommend freezing that input directly — the failure mode is a hang/OOM, which
is a poor frozen-test shape — but it should be noted as knowingly unanchored rather than left
implicit.)

**Evidence.** Plan `:264-276` (the normalization + the "m48 freezes the boundary" sentence),
`:3167-3173` (the anchor, which names only `"1e40"` and `"1e-8"`).

**Suggested fix.** Add the boundary **positive** control to m48's grammar anchor: a dotted-mantissa
input whose canonical plain-digit rendering is exactly 32 characters (`"1.5e31"` → tag
`15` + 30 zeros) is ACCEPTED and yields that canonical tag, alongside a 33-digit neighbour
(`"1.55e31"`) rejected with the magnitude message. Those two cases together are what pin the
normalization; either alone is passed by the naive computation.

---

### 4. MID — §7.2's seam illustration "`reduce`/`empty` supplied as factories" is not implementable without changing a signature already frozen at m5

**Section:** §7.2 (`:2237-2241`).

**Detail.** The seam is left to the implementer's spelling ("exact spelling pinned at m48 freeze")
with two illustrations: "e.g. `reduce`/`empty` supplied as factories over the compiled output ids,
or an `on_compiled`-shaped hook". The first reading changes the meaning of the existing `reduce=`
and `empty=` parameters, which are asserted with plain callables in an already-frozen test:

```
aggregate_plan(out1, out2, reduce=_sum_each, combine=_add_pairs, empty=lambda: [0, 0], steps_per_file=4)
aggregate_plan(a + b, reduce=_sum_each, combine=_add_pairs, empty=lambda: [0])
```
(`graphed tests/frozen/frontend/m5/test_aggregate_plan.py:77,88,102` — read this session). A
"factory over the compiled output ids" cannot be duck-typed apart from a plain reducer callable
(`_sum_each` also takes one positional argument), so an implementer taking the first illustration
either breaks frozen m5 (an integrity violation under §B.6) or files a Test Dispute. The plan is
scrupulous about additivity everywhere else it touches a shipped surface (§8.1's `variation: str =
""`, §8.2(i)'s "additive dataclass field", §9.2's "additively; existing m9 frozen tests are
untouched") and this clause is the exception.

**Evidence.** Plan `:2237-2241`; `graphed tests/frozen/frontend/m5/test_aggregate_plan.py:74-102`;
`python/graphed/aggregate.py:68-108`.

**Suggested fix.** Bind the seam **additive**: the existing `reduce`/`combine`/`empty` parameter
contracts are unchanged (frozen at m5) and the seam is a NEW optional parameter or hook; drop the
factory illustration or restate it as a distinct new keyword.

---

### 5. LOW — m49's §8.2(i) `2N + 2` / `N + 1` cardinality clause is exact on only one of the three topologies the anchor names

**Section:** m49 §8.2(i) anchor (`:3312-3351`).

**Detail.** The anchor names a base topology "built through the frontend `compile_ir` path, and
EXTENDED with one deliberately unmarked branch", then "a topology EXTENDED a second way … one
derived node consumed by TWO NON-nominal universes", then r18/r19's partitioning clause: "the map's
image over the WHOLE topology has exactly **2N + 2** distinct reduced ids, of which exactly
**N + 1** are of kind `stage`". "the WHOLE topology" is naturally read as "all record ids" (not "a
different topology"), and the clause is prefaced "a PARTITIONING clause the §3.3 topology makes
exact" — but the anchor has by then introduced two fixtures, and a test-author who builds ONE
fixture carrying both extensions (the economical choice) freezes a literal that a correct accessor
fails.

Measured this session (raw `GraphStore`, D=20/K=5, marking every universe's reduction):

| fixture | reduced_nodes | stages |
|---|---|---|
| base | 2N+2 (N=3 → 8; N=16 → 34) | N+1 (4; 17) |
| base + unmarked dead branch | 2N+2 (8; 34) | N+1 (4; 17) |
| base + node shared by two non-nominal universes | **2N+3** (9; 35) | **N+2** (5; 18) |
| both extensions | **2N+3** (9; 35) | **N+2** (5; 18) |

So the unmarked-branch extension is harmless (DCE removes it) and the shared-node extension shifts
both literals by one.

**Evidence.** Probe above against `graphed-latest@ff7c607` (raw `GraphStore` and, for the base,
`compile_ir` — both give `{source:1, stage:N+1, reduction:N}`). Plan `:3325-3351`.

**Suggested fix.** State in the anchor that the cardinality clause is asserted on the FIRST fixture
(base ± the unmarked branch) only, and note the shared-node fixture's measured `2N+3` / `N+2` so a
test-author does not merge the two.

---

### 6. LOW — m48's §6.1a positive control asserts a `mypy --strict` property that §6.1a's own varied shape makes false

**Section:** m48 §6.1a anchor (`:2929-2935`).

**Detail.** The r19 wholly-unvaried positive control is right and welcome. Its justification
sentence, however, claims: "`run(gh.plan({"hi": h1, "lo": h2})).value["hi"]` still works **and
`plan()`'s declared `Plan[dict[str, bh.Histogram]]` (`boost.py:262`) still types under
`mypy --strict`**". The second half cannot hold: §6.1a/§6.1c bind a varied plan's value to
`{(output, label) → hist}` / `{(output, None) → hist}`, so `_GroupReduce.__call__`'s return
annotation must widen from `dict[str, bh.Histogram]` (measured at
`graphed-histogram src/graphed_histogram/boost.py:106-118`) to a union-keyed dict, and
`plan()`'s inferred/declared `Plan[dict[str, bh.Histogram]]` at `:262` widens with it. The runtime
half (`value["hi"]` still works, m23 stays green) is exactly right; only the "declared type
unchanged" half is wrong, and it reads as an instruction to an implementer not to touch the
annotation.

**Evidence.** `graphed-histogram src/graphed_histogram/boost.py:101-122` (`_GroupReduce.layout` /
`__call__ -> dict[str, bh.Histogram]`, `_add_groups` at `:120-122`), `:262`
(`-> Plan[dict[str, bh.Histogram]]`), `:282` (`layout`), `:286` (the `aggregate_plan` call) — all
read this session. Plan `:2929-2935`.

**Suggested fix.** Re-word to what is actually frozen and true: the runtime keys of a wholly-unvaried
plan's value are bare output names, m23's indexing is unchanged, and the declared return type widens
to the union-keyed dict (which still admits `value["hi"]`).

---

## Lens areas that came back CLEAN

Stating these explicitly so the absence of findings is not read as absence of checking.

- **(a) Non-vacuity / discrimination of r19's new anchors.** The two BLOCKER repairs are both
  discriminating: the property gate classifies by a *measured* `Session.node_count()` delta on the
  plain nominal `Array` (self-repairing, and `varied.T` returning a `Varied` with matching
  `graphed.labels` fails a nominal-only answer); the wholly-unvaried positive control fails any
  implementation that re-keys unvaried outputs. The §2.1(b) row-space positive control fails a
  non-re-indexing implementation on row count alone. §8.2(i)'s partitioning clause defeats the
  degenerate constant map r18 identified (the per-universe-distinctness half). No new tautology of
  the §4.3-equal-counts or §5.2a-self-derived kind was introduced.
- **(b) Witness-of-mechanism (R0.10).** r19 did not weaken any mechanism witness. The one anchor
  that is purely static after r19 (§7.2 schema absence) is honestly labelled as such and the plan
  correctly demotes the varied-vs-unvaried comparison to "may ride along as a sanity assertion" —
  measured, that comparison is equal by construction for three dataclasses with class-level fields.
- **(c) R0.10a.** No new wall-clock or size threshold entered a frozen test in r19. §3.3's 16.0
  bound remains the single named carve-out; §6.2's scaling anchor stays structural (combine-payload
  entry counts); §6.4c compression and the m50 N≈100 comparison stay R0.11 implementer-report items.
- **(d) Determinism-gate compatibility.** r19 touched nothing here. m49's plan-byte anchor stays
  bound to the BY-VALUE `DurablePlan` with module-level closure operands (r18), which is the only
  construction that can observe a `frozenset` `variation_labels`; §8.2(i) stays a sorted tuple;
  §6.4e's manifest stays sorted with its own m51 two-seed anchor.
- **(e) Freeze-order hazards.** I re-checked the r19 deltas against later milestones: m48's §6.1a
  slot-key freeze is scoped "in SIBLING mode" and cannot be red by m50's `(output, None)` keys (the
  three key forms are disjoint and per output, and the r19 deletion of the MODE field makes §9.1's
  one-argument `unpack(value)` consistent with §6.1a again); m48's §2.3d per-class floors are
  containment, so m51's *accepting* `to_parquet` cannot red them; m48's gak floor now correctly
  reads "`gak.join` IS IN the refusing class and `len(refusing) >=` the freeze-time count" instead of
  r16's stale equality; m48's §1.2 anchor is scoped to sibling mode against §6.2's m50 carve-out and
  its "or token" drop is correct (measured: `GraphStore.nodes()` exposes no token, and stage
  `members` carry `kind`/`name`/`params`, so the recursion clause is implementable). I found no new
  instance of the r7-style superseded-rejection trap.
- **(f) r19's fixture repairs are buildable.** The mixed-granularity → same-granularity correction
  (`sel.Jet.pt` → `sel.MET.pt` in both m48 fixtures) is necessary and sufficient: I reproduced
  bh 1.8.0's `ValueError: spans must have compatible lengths` for unequal axis lengths, and under
  §6.1d link kinds (1)/(3) both restated fixtures land at one row count per label. The §2.6 sketch's
  b-tag operand correction matches the corpus exactly (`good = jets[jets.pt > 25]`; `sel_jets =
  good[sel]`; per-jet SF producted over `axis=1`), so the m48/m49 reference matrices are reachable.
- **(g) Repo placement / frozen-layout rules.** No r19 delta moved an anchor into a repo that cannot
  host it; the unique-basename and no-`importorskip`-on-headline-gates rules are untouched.
  (Finding 1 is a *coverage* gap in a correctly-placed half, not a placement error.)

## Verdict

**DIRTY — but narrowly.** One HIGH (finding 1: the r19 `aggregate_plan` seam lands in `graphed` at
m48 with no `graphed`-side frozen anchor, in a half that structurally cannot build a varied plan,
after r19 removed the only plan-shaped anchor from it), three MIDs (a binding lowering rule with no
discriminating anchor; a boundary the plan claims m48 freezes and m48 does not; a seam illustration
that collides with frozen m5), and two LOWs. No BLOCKER: every r19 milestone remains implementable
and no anchor as worded would freeze a wrong or vacuous test. All six are local fixes — one new
anchor, two fixture extensions, three wording repairs — and none requires reversing an owner-locked
decision or reopening a design choice.
