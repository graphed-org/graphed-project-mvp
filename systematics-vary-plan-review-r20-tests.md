# systematics-vary-plan — review round 12, TEST ARCHITECTURE lens (plan revision r20)

- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, traceability (requirement ↔ anchor), and testability-as-stated (can the test-author
  actually build the fixture from what the plan gives?).
- **Document reviewed:** `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-plan.md`,
  revision **r20**, read in full (4841 lines: Part I, every PART II section, §10 milestones, §11,
  §12, the Anchors appendix, and the revision history back through r15).
- **Date:** 2026-07-30.
- **Verification roots used (all facts below were measured by me in this session):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`, numpy 2.5.2)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (its own `.venv`,
    boost_histogram 1.8.0)
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4`
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, the Phase-2 pull-in) were treated as
  fixed; nothing below asks to reverse one.

---

## What I re-measured (clean — no finding)

These are the claims my lens depends on most heavily. All of them hold exactly as written; I record
them so the next round does not re-spend the budget.

| Plan claim | Measured result |
|---|---|
| m48 §7.2 schema anchor's literal key sets | `Plan` → `{combine,empty,next_tasks,open_once,process,stop,tasks}`; `ExecResult` → `{n_combines,n_partitions,stopped,value}`; `TaskEvent` → `{bytes_read,error,key,n_entries,partition,phase,t,worker}` — all three exactly as spelled in §10/m48 |
| §6.3 params key set | `{"spec","n_axes","weighted","sampled"}` + `n_weights` only when `len(weights) > 1` (`graphed-histogram src/graphed_histogram/boost.py:198-212`) |
| §2.3d annotation-wide discovery = 8 verbs, `compile_ir` missed | `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`; `compile_ir` IS in `graphed.__all__` but is not discovered |
| §2.2/§2.3a property discovery + r20's 1-D fixture pin | discovered properties on `NumpyArray` = `['T','dtype','ndim','node_id','session','shape']`; on a 1-D `gnp.ones(s,(4,))`: `dtype`/`ndim`/`shape` → `node_count()` delta **0**, `T` → delta **1**; on `gnp.ones(s,(4,3))`, `.T` → `GraphedTypeError: … displacing the partitioned axis 0`. r20's pin is necessary and correct. |
| §3.3 / m49 §8.2(i) topology shape and r20's scoping | base builder: N=3 → `reduced_nodes 8`, kinds `{source:1, stage:4, reduction:3}`; N=16 → `34`, `{1,17,16}` — i.e. `2N+2` / `N+1` stages. Dead branch changes nothing (DCE). Shared-node extension: N=3 → `9`, `{1,5,3}`; N=16 → `35`, `{1,18,16}` — `2N+3` / `N+2`. r20's scoping of the cardinality literal to the base fixture is exactly right. |
| m48 §7.2 merge-guard UNVARIED positive control | `compile_ir(s, b, b*1.0)` → `GraphStore.deserialize(ir).outputs() == [0]` (one value for two marked outputs) |
| m48 §1.2 anchor's r19 "drop *or token*" + stage recursion | `GraphStore.nodes()` node keys = `{id, output, inputs, kind, name, params}`; a reduced `stage` adds `n_members`/`members`, each member carrying `{inputs,kind,name,params}`; no token anywhere. `nodes()` is dense, so `nodes()[fill_id]` (the §4.3 spelling) is valid alongside the m29 house pattern. |
| m48 matrix note: gak has no `round(decimals)`, use `rint(x*1e6)/1e6` | bit-identical to `np.round(x, 6)` over 200 000 uniform values in [0,800] (numpy 2.5.2, zero differing bit patterns). The note is safe as a frozen-anchor instruction. |
| m48 matrix portability of the corpus analysis | every awkward function the corpus fixture uses (`with_field`, `num`, `sum`, `prod`, `firsts`, `drop_none`, `full_like`, `local_index`) exists in gak's 65 public functions |
| m5's frozen `aggregate_plan` call shape that §7.2's (α) anchor reuses | `tests/frozen/frontend/m5/test_aggregate_plan.py:77` is `plan = aggregate_plan(` with `reduce=_sum_each, combine=_add_pairs, empty=lambda: [0, 0], steps_per_file=4` — the plain-callable contract r20's *additive* seam preserves |

Freeze-order sweep (my lens item (e)): I re-checked every m48-frozen shape that a later milestone
must contradict — §6.1a's sibling-mode scoping and its bare-key scoping for unvaried outputs,
§6.1b's `1+|S|+|W|` sibling scoping, §1.2's sibling-lowering scoping against §6.2's carve-out,
`to_parquet`'s removal from m48's §2.3d table and floor, the containment-not-equality form of every
per-class and refusing-class floor, and `graphed.labels`-on-a-bare-histogram at m48 vs
§6.2(i-bis) at m50 (compatible: the m48 fixture's bare histogram carries no `variation` axis).
**No new freeze-order trap of the r7/r18 kind.** R0.10a is clean: §3.3's ratio gate remains the one
named wall-clock carve-out and r20 introduced no timing or size threshold. Determinism-gate
compatibility is clean: §3.2's m48 anchor, m49's plan-byte anchor (by-value `DurablePlan` +
module-level closure operands), §5.5's partition-invariance quantities, and m51's manifest
determinism anchor are all still stated over invariants that survive the R22.3 form.

---

## Findings

### 1. MID — m50's new `sample=`-only-label anchor is unbuildable with the default storage, and nothing says so

**Section:** §10/m50 (equality anchor, r20 clause); §6.1b r19/r20; §6.2's `S`/`W` clause.

**Detail.** r20 added, as the *only* place §6.1b's `S`/`W`-by-lowering split is witnessable, an m50
clause: *"The mixed program carries a label borne ONLY by a `Varied` `sample=` … that label must
lower as a SIBLING … and the axis-mode result still equals its sibling-fill decomposition."* That
anchor **runs** (bin-for-bin equality), so the fixture histogram must actually evaluate a fill with
`sample=`. Measured (boost_histogram 1.8.0, `graphed-histogram-latest/.venv`):

```
bh.Histogram(bh.axis.Regular(3,0,1)).fill(np.array([0.1,0.5]), sample=np.array([1.0,2.0]))
  -> TypeError: Keyword(s) sample not expected
```

`graphed_histogram.FillEvaluator.__call__` passes `sample` straight through to `h.fill`
(`src/graphed_histogram/boost.py:60-71`), so the failure lands at *evaluation*, not at record time —
i.e. after TEST_SANITY has been written and against a correct implementation, which is a Test
Dispute or a red frozen test rather than a clean discovery.

The fixture is buildable, but only on a `Mean`/`WeightedMean` storage, and I verified the whole
chain works there: `Mean` and `WeightedMean` accept `sample=`; `_spec.py`'s `_STORAGES` carries both
(`src/graphed_histogram/_spec.py:19-27`); and a `WeightedMean` histogram with a
`Regular` + `StrCategory("variation")` axis pair round-trips `spec_of` → `zero_of` (storage and both
axes preserved) and adds cleanly — which is what `_GroupZero`/`_add_groups` need.

This is exactly the class of note the plan spends real space on elsewhere ("mid-freeze discovery
spared" for `gak.full_like`, the corpus `stable()` rounding, `h.axes.name`, the pt-cut jets, and —
in r20 itself — the 1-D property fixture). It is missing here, and the discriminating power of the
anchor also depends on it: with a `Double`-storage histogram there is no observable difference
between a sample-only label lowered as `S` and one folded into `W`, because the sample never reaches
the result at all.

**Evidence.** measured this session, boost_histogram 1.8.0:
`Double + sample -> TypeError: Keyword(s) sample not expected`; `Mean` fill with sample OK
(`MeanView` populated); `WeightedMean` fill with weight+sample OK;
`spec_of/zero_of` round-trip of `bh.Histogram(Regular(3,0,1), StrCategory(['nominal','s_up']),
storage=WeightedMean())` → `WeightedMean`, `[Regular(3,0,1), StrCategory([...])]`, and `z + h`
succeeds. Source: `graphed-histogram@211cbbe src/graphed_histogram/boost.py:60-71`,
`_spec.py:19-27`.

**Suggested fix.** In the m50 anchor (and in §6.1b's r20 paragraph, which is what an implementer
reads), add one sentence: *the `sample=` fixture MUST use a `Mean` or `WeightedMean` storage —
measured, `boost_histogram` rejects `sample=` on `Double`/`Weight` storages
(`TypeError: Keyword(s) sample not expected`, bh 1.8.0), while `_spec.py`'s `_STORAGES` carries both
mean storages and the variation-axis spec round-trips and adds on them.* Note in the same place that
the sample values must differ per label, or the equality is satisfied by both classifications.

---

### 2. MID — the r20 `context_of`-on-a-`Varied` discriminator fixture freezes a mixed-row-space container as constructible, i.e. the exact hole §2.1(b) r20 just closed

**Section:** §10/m48 (`§2.3d table` bullet, r20 clause); §2.3e r20; §2.1 r18/r19/r20.

**Detail.** r20 added to m48: *"a container built from an ancestor-handled nominal member and a
MORE-DERIVED non-nominal member answers with the more-derived handle."* The natural — and, from the
wording, most likely — fixture is a loose overload-(a) call such as
`graphed.vary(events.Jet, "jes", up=sel.Jet)`, whose nominal member sits at `events`' row count and
whose `up` member sits at `sel`'s. §2.1 accepts it (form compatibility is a *type* check; Session
and source agree; the handles lie on one ancestry chain), and §2.3e r20 explicitly leans on that
acceptance as its justification.

But the same revision, in §2.1(b), makes the analogous mis-spelling an error precisely because it
"records CLEANLY — measured, `Session.record_op` validates only the backend's `op_form`, never
lengths or row spaces (`python/graphed/session.py:142-168`) — dying at execution with a message
§6.1d's refusal contract does not cover". Freezing this fixture at m48 pins that a row-space-broken
`Varied` is *constructible*, which forecloses ever extending §2.1's construction check the way
§2.1(b) was just extended — read-only, for the remaining three milestones.

The anchor does not need that commitment. A `graphed.vary`-**identity** link (§6.1d link kind (2))
gives two distinct handles on one ancestry chain at the **same** row space:

```python
events2 = graphed.vary(events, "pu", pu_nom, is_weight=True, up=..., down=...)
v = graphed.vary(events.Jet, "jes", up=events2.Jet)     # nominal handle `events`, up handle `events2`
graphed.context_of(v) is events2                        # the discriminator, unchanged
```

This discriminates the container-vs-nominal-member reading identically (a "nominal member's handle"
implementation answers `events`), and it is also closer to what §6.4a(2a)'s handle-equality predicate
actually consumes, since a `select=` mask's members are routinely reads through sibling registration
states of one row space.

**Evidence.** Plan text: §10/m48 §2.3d bullet, r20 clause ("ancestor-handled nominal member and a
MORE-DERIVED non-nominal member"); §2.3e r20 ("§2.1 explicitly ACCEPTS members whose handles differ
along one ancestry chain and refuses only divergent ones"); §2.1(b) r19/r20 (the row-space contract
and the DESCENDANT construction-time error), whose measured basis I re-verified:
`graphed-latest@ff7c607 python/graphed/session.py:142-168` — `record_op` performs no length or
row-space validation.

**Suggested fix.** Pin the fixture in the m48 bullet: build the two handles across a
`graphed.vary` IDENTITY link (same row space, §6.1d kind (2)), not across a mask-derivation link, and
say why (the anchor must not freeze a row-space-mismatched container as legal). §2.3e's rationale can
keep its "§2.1 accepts members on one ancestry chain" argument; only the fixture needs pinning.

---

### 3. MID — m49's §8.2(i) partitioning clause is ambiguous about the SOURCE record id, and one reading reds a correct accessor

**Section:** §10/m49, §8.2(i) accessor anchor (r18 clause, retained through r20).

**Detail.** The clause reads: *"the shared-prefix record ids all map to ONE reduced id, each
universe's chain maps to a reduced id DISTINCT from every other universe's, and the map's image over
the WHOLE topology has exactly 2N + 2 distinct reduced ids, of which exactly N + 1 are of kind
`stage`."*

The §3.3 builder is "source → a shared prefix of D ops → per universe {…}". r19's own correction
established that the accessor is bound over **every surviving record id, which includes the source**
— that is precisely why the cardinality literal moved from `N+1` to `2N+2`. But the *first* half of
the same sentence was not correspondingly clarified: the source record id maps to the reduced
**source** node, not to the prefix **stage**, so if a test-author reads "the shared-prefix record
ids" as "source + the D prefix ops" — which is how the builder sentence reads — the assertion
`len({map[r].reduced for r in prefix_records}) == 1` is **false against a correct accessor** (it is
2). This is the same defect class r19 fixed one clause later in the same bullet, and it lands as a
frozen literal.

**Evidence.** Measured this session against `graphed-latest@ff7c607` on the §3.3 builder (D=20, K=5,
every universe's reduction marked): reduced kinds are `{source: 1, stage: N+1, reduction: N}` for
N=3 (`{1,4,3}`, 8 reduced nodes) and N=16 (`{1,17,16}`, 34 reduced nodes) — i.e. the reduced store
carries a source node distinct from the prefix stage, and the prefix ops fuse into exactly one of the
N+1 stages.

**Suggested fix.** Reword to name the two halves explicitly: *"the D shared-prefix OP record ids all
map to ONE reduced id (the prefix stage); the SOURCE record id maps to the reduced source node, which
is neither a stage nor an output; each universe's fork+chain ops map to a stage id distinct from every
other universe's …"*.

---

### 4. MID — §2.2's r20 rebinding of the third `graphed.labels(ctx)` union term is unwitnessed: both anchored programs are green under the pre-r20 reading

**Section:** §2.2 (r20 clause); §10/m48 (`graphed.labels` on a context bullet).

**Detail.** r20 replaced §2.2's third union term ("the labels of the mask that derived it") with
"the labels of `graphed.selection(ctx)` in §9.1's sense — the selection reached by **skipping over
any number of `vary` IDENTITY links** and answering as of the first non-identity link". The stated
motivation is that "the object whose labels a user or an m48 anchor asks for is routinely
`vary`-derived", and the paragraph itself warns that in the mainline term (a) rescues the answer,
"but that is a property of the program, not a rule".

m48's anchor for this verb carries two programs, and **neither queries a `vary`-derived context**:

- program 1 ("registers a weight BEFORE the derivation"): `ctx = vary(events, "pu", …)` then
  `sel = ctx[varied_mask]` — the query target `sel` is **mask**-derived;
- program 2 (r14's discriminator, "a shift-varied collection with an UNVARIED derivation mask"):
  `ctx = vary(events, "jes", Jet={…})` then `sel = ctx[unvaried_mask]` — again **mask**-derived.

An implementation that keeps the pre-r20 reading (term (c) = the mask that derived *this* context,
`None`/nothing for a `vary`-derived one) passes both. The whole clause therefore lands with zero
frozen-suite coverage in the milestone that binds it — the same shape r12 closed for §5.3, r13 for
§2.3d/§2.2's reserved names, and r14 used to move §3.4 out of m48.

There is a second-order problem worth settling in the same edit: on a **varied-mask**-derived
context, §2.6c makes *every* read through the context `Varied`, so union term (b) ("the labels of any
`Varied` collections on the context") may already subsume term (c). Whether term (c) is observable at
all depends on an unstated implementation choice — whether a context's "varied collections" means the
explicitly `vary`-replaced ones or every collection reachable through it. If it is genuinely
unobservable, say so the way §1.1's "count BEFORE any rendering" rule is knowingly left unanchored;
if it is observable, anchor it.

**Evidence.** Plan text, §2.2 r20 clause (lines 509-521 of the plan) and §10/m48's
`graphed.labels`-on-a-context bullet (lines ~3323-3333), read in full. No other m48 anchor mentions
`graphed.labels` on a `vary`-derived context (grep of §10/m48 for `graphed.labels`).

**Suggested fix.** Add a third program to the m48 bullet whose query target is `vary`-derived across a
mask-derived parent, and whose answer differs between the two readings — e.g.
`sel = events[jes_varied_mask]`, then `sel2 = graphed.vary(sel, "jer", Jet={…})`, asserting
`graphed.labels(sel2)` reports the **jes** labels (from the walked-over `vary` link) alongside the
jer ones — **and** state in §2.2 whether term (b) covers implicitly-varied reads, so the fixture's
discriminating power does not depend on an implementer's choice.

---

### 5. LOW — §7.2's "`plan()` MUST NOT compile a second time" is binding and unanchored, and (α)'s anchor carries one clause with no observable

**Section:** §7.2 (r19/r20 seam); §10/m48 (§7.2 seam (α) anchor).

**Detail.** Two small things in the same new anchor:

(a) §7.2 binds *"`plan()` MUST NOT compile a second time: the §3.3 anti-quadratic budget is written
for ONE reduction of the variation-expanded graph, and a frontend-side `compile_ir` before
`aggregate_plan`'s own would double it."* Nothing in m48–m51 witnesses it. The (α) anchor asserts the
hook "fires EXACTLY ONCE" **inside `graphed`'s** `aggregate_plan` call, which says nothing about
whether `graphed-histogram`'s `plan()` compiled separately beforehand. This is a binding sentence
whose violation is silent (correct results, doubled reduction cost) and is not covered by the R0.11
report route either, since §3.3's budget is a frozen gate on a *different* fixture.

(b) The (α) anchor's phrase "its `outputs()` readable **BEFORE the worker closure exists**" is not
assertable by a frozen test: the hook receives only the `CompiledGraph` and has no handle on the
closure, so a test-author has no operand for the ordering half. The rest of the anchor ("fires
exactly once", "receives the `CompiledGraph`", "the resulting `Plan` runs to the same value as the
same program built WITHOUT the hook") is fully assertable.

**Evidence.** Plan text §7.2 (lines ~2367-2371 and the r20 additivity paragraph) and §10/m48's
`§7.2's r19 aggregate_plan SEAM (α)` bullet (lines 3002-3013). Measured context: `aggregate_plan`
compiles internally (`graphed-latest@ff7c607 python/graphed/aggregate.py:95`) and
`graphed_histogram.plan()` builds `layout` at `src/graphed_histogram/boost.py:282` before its
`aggregate_plan` call at `:286` — so a second compile in `plan()` is a live implementation option.

**Suggested fix.** (a) Either give the "no second compile" rule a witness in `graphed-histogram`'s
m48 half — the cheapest discriminating form is a counting hook: the same `on_compiled`-shaped seam
fires **exactly once** across a whole `gh.plan({...})` call, which a `plan()` that compiles first
would fail only if that first compile also goes through the seam, so the honest alternative is to
state the rule as an R0.11 implementer-report item (measured compile count) — or (b) mark it
knowingly unanchored, the treatment §1.1's `"1e1000000000"` rule already receives. Drop "before the
worker closure exists" from the anchor bullet, or restate it as what a test can see (the hook's
argument is a `CompiledGraph` whose `outputs()` is readable, and the returned `Plan` behaves as m5
freezes).

---

## Verdict

**Dirty — but only lightly, and nothing blocking.** No BLOCKER and no HIGH. The r20 changes I was
asked to scrutinise are, on this lens, mostly *improvements* to test architecture: the two new
`graphed`-side m48 anchors (§7.2 seam (α), §6.1d lineage seams) close genuine per-repo
diff-coverage holes; the §8.2(i) cardinality scoping, the §1.1 cap-boundary pair, and the 1-D
property fixture pin each fix a literal that a correct implementation would otherwise have failed —
I re-measured all three and they are right.

Four MID findings and one LOW remain, and all five are of the same, now-familiar shape this plan has
been converging on: a rule bound in one revision whose *witness* did not travel with it (#4, #5a), an
anchor sentence whose most natural fixture is unbuildable or over-committing (#1, #2), and one
residual ambiguity in a frozen literal that r19 fixed for its sibling clause but not for this one
(#3). None requires reopening an owner-locked decision; each has a one-or-two-sentence fix in the
anchor text.
