# systematics-vary plan — review round 4, DESIGN SOUNDNESS lens

- **Lens**: design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  violations, milestone-boundary consistency. New-surface priority: §2.6, §6.1d, §6.4/m51, §1.1 r9.
- **Plan revision reviewed**: r12 (`systematics-vary-plan.md`, 2205 lines, read in full).
- **Date**: 2026-07-30.
- **Verification roots used** (fresh clones at the revisions the plan pins; the stale submodules in
  `graphed-workdir` were NOT used for any code fact):
  - `/private/tmp/claude-501/graphed-latest` — consolidated `graphed`, verified `ff7c607a8ba637ebc1b5db37316adf6e10028dcc`
  - `/private/tmp/claude-501/graphed-histogram-latest` — verified `211cbbe22497b64ce624d4880005af7faddf74f7`
  - `/private/tmp/claude-501/graphed-exec-check`, `graphed-corpus-latest`, `uproot5-graphed` (not needed for any finding below)
- **Owner-locked decisions were treated as fixed.** No finding below asks for a different choice on
  naming, the functional surface, e-form canonicalization, context attachment, record-time expansion +
  interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, or the Phase-2 pull-in. Every finding is an
  internal inconsistency, an unhandled interaction, or an under-specified target.

**No BLOCKERs.** 3 HIGH, 5 MID, 4 LOW, 1 NIT.

---

## HIGH

### H1 — §8.2(ii): the bound transport can carry a label, but nothing binds how the worker learns WHICH node raised

**Section**: §8.2(i)/(ii), m49 anchors.

**Detail.** §8.2 binds a `variation_labels: tuple[tuple[int, frozenset[str]], ...]` field on
`_PartitionReduce` keyed on post-reduction ids (r12: on `(reduced_node_id, member_index)` via a new
read-only core accessor), and binds (ii) as *"the `evaluate_ir` call site in `_PartitionReduce.__call__`
is wrapped so a worker failure becomes a `StageError`"*. A wrapper **around the call** cannot produce a
node id, so it cannot index the map it is given. The map is necessary but not sufficient, and the
missing half — per-node failure attribution inside evaluation — is not scoped anywhere in m49.

**Evidence** (read this session, `graphed-latest@ff7c607`):
- `python/graphed/aggregate.py:57-65` — `_PartitionReduce.__call__` is `read_partition` →
  `evaluate_ir(...)` → `self.reduce(values)`. One call, no per-node context.
- `python/graphed/execute.py:98-126` — `evaluate_ir` is a bare `for nd in store.nodes():` loop with
  `backend.eval_stage(...)` dispatches and **no try/except and no node-id annotation anywhere**; a
  backend exception propagates naked. For `kind == "stage"` the members are evaluated in an inner loop
  (`:110-117`) that likewise annotates nothing — and §8.2 itself notes fusion collapses a whole universe
  into ONE `Stage`, so the *common* case needs `member_index`, which only that inner loop knows.
- So `except Exception as e:` at the call site yields a `StageError` with no node, hence no
  `(reduced_node_id, member_index)` key, hence no label. The m49 anchor *"a failure raised inside the
  `jes_up` universe … re-raises driver-side carrying `variation == 'jes_up'`"* — and the r12-added
  multi-label rendering anchor — cannot be satisfied by the bound mechanism.

**Why it matters at this severity.** r10 withdrew r9's transport because "the channel it named does not
exist"; r12 withdrew r11's key space for the same reason. This is the same defect a third layer down:
the key space now exists (given the accessor), but the *keying event* does not. An implementer will
either guess (re-evaluate node-by-node on failure? ship a second instrumented `evaluate_ir`?) or ship
the honest fallback silently.

**Suggested fix.** Make the attribution explicit as a third m49 part: **(iii) per-node attribution in
`evaluate_ir`** — an optional `on_node`/`attribute=` hook (or a `node_index`/`member_index`-carrying
exception wrapper) added at `execute.py:98-126` and `:110-117`, so the raiser is identified as
`(node_index, member_index | None)`; `_PartitionReduce` then maps that through `variation_labels`.
State explicitly that this is a change to `graphed`'s evaluation path (not core, not the IR), and word
the m49 anchors over the resulting `StageError`, not over the wrap site. If (iii) is descoped, the
§8.2 output-position fallback must become the primary binding, not the "if the accessor is descoped"
footnote — because without (iii) the accessor alone buys nothing.

---

### H2 — §6.4a predicate (2) is unsatisfiable for the level ≥ 1 masks that §6.4d and the m51 object-migration anchor require

**Section**: §6.4a (entry checks), §6.4d, m51 anchors.

**Detail.** r11 made `select=` **per level** (`{0: event_mask, 1: jet_mask, …}`) precisely so §6.4d's
object-level cutflow is expressible; r12 then bound entry predicate (2):

> **(2) ROW-SPACE AGREEMENT** — every supplied `select=` level must be a mask over the SAME row space
> as the record. Bound structurally via §2.6b lineage: each mask must be the selection deriving
> directly from the context the record was read from (`graphed.selection(ctx)` of the record's own
> context handle, §2.3e) … plus a runtime row-count equality between the record and each level-0 mask.

Both halves of the binding clause are false for level ≥ 1:
1. A level-1 mask is a **per-object** mask (`events.Jet.pt > 25`), jagged over the record's inner
   dimension. It is *not* "a mask over the SAME row space as the record" in the sense the sentence uses
   for level 0, and the plan's own runtime check is scoped to "each **level-0** mask" — the two halves
   of one sentence disagree about scope.
2. A level-1 mask is **not** `graphed.selection(ctx)` of anything. §9.1 defines `graphed.selection(ctx)`
   as *"the `Varied` mask that derived a context from its parent"*, and contexts are event-level
   (§2.6c: `events[mask]` derives a context). There is no context whose derivation mask is a per-jet
   mask, so "each mask must be the selection deriving directly from the context the record was read
   from" cannot be satisfied by any legal level-1 argument.

Consequence: read literally, predicate (2) refuses **every** `select={0: …, 1: …}` call — i.e. exactly
the m51 anchor *"covering a shift with object-level migration (per-label inner masks, §6.4d, written
through the per-LEVEL `select={0: event_mask, 1: jet_mask}` channel — §6.4a r11 is what makes this
anchor satisfiable at all)"*. The plan's own BLOCKER fix from r11 is re-closed by the r12 entry check.

**Suggested fix.** Scope predicate (2) by level, explicitly:
- **level 0**: bound as written — lineage identity against the record's context handle plus the runtime
  row-count equality.
- **levels ≥ 1**: the decidable check is *structural*, not lineage-based — the mask's per-label offsets
  must equal the record's offsets at that depth (the same data the level-0-agnostic predicate (1)
  already computes per partition, so it costs nothing extra and lands in the same `_WritePart` raise).
Then say which m51 positive control each level's check decides, as §6.4a already does for (1)/(2).

---

### H3 — §2.6c binds `graphed.labels(ctx)` to the mask's labels, contradicting §6.1d's fill label set; no section defines a context's label set in general

**Section**: §2.2, §2.6c, §6.1d, §9.1, m48 anchor list.

**Detail.** §2.2 makes `graphed.labels(x)` accept "a `Varied` OR an event context (uniform
introspection, §9.1)" but defines its answer only for a `Varied`. The **only** binding statement for a
context is in §2.6c's varied-context bullet:

> its collections are `Varied` per §2.6b; **`graphed.labels(ctx)` reports the mask's labels**;
> re-indexing happens per label …

§6.1d meanwhile binds a fill's label set as *"the §2.4 union of value-borne labels, **ambient-weight
labels**, and explicit `weight=[...]` factor labels"*. On the plan's **own mainline sketch** (§2.6, lines
613–635) these disagree by 105 labels: `events` carries `pu` (2) + `pdf` (102) ambient weight labels
before `sel = events[gak.num(jets) >= 4]` is derived by a JES-varied mask, so
`graphed.labels(sel)` = `{nominal, jes_up, jes_down}` under §2.6c, while every fill from `sel` yields
those plus the 104 weight labels. The introspection verb the plan bills as "uniform" answers a strict
subset of what the sink produces — the confidently-wrong-bookkeeping class §2.5 exists to delete, and
the class §6.2(i-bis) was added in r12 to fix for histograms.

It also leaves the general case unbound: for a *root* context carrying only weight registrations (no
derivation mask at all), no section says what `graphed.labels(ctx)` returns.

**Anchor exposure.** m48 freezes "`graphed.labels` on a context derived by a **Varied** mask (per-label
row sets, §2.6c)". A test-author reading §2.6c will freeze the mask-labels-only answer; the two readings
only coincide if the anchor program registers no weights before deriving — i.e. only if the anchor
deliberately avoids the mainline shape.

**Suggested fix.** Bind the context label set once, in §2.2 or §2.6c: `graphed.labels(ctx)` = the §2.4
union of (a) the ambient weight registry's labels, (b) the labels of any `Varied` collections on the
context, and (c) the derivation mask's labels, in the §2.4 bound order with `"nominal"` first — which is
by construction the superset the §6.1d fill can produce. Reword §2.6c's sentence to *"the derived
context's labels include the mask's labels"* and re-word the m48 anchor to assert the union on a program
that has a weight registered before the derivation.

---

## MID

### M1 — the m48 `.plan()` refusal over-freezes m50's mixed axis-mode program, where `_SumFills` is the CORRECT reduce

**Section**: §6.1c, §6.2, m48 anchor "§6.1c `.plan()` refusal", m50 mixed-program anchor.

**Detail.** r12 rescoped the m48 anchor to *"a `Histogram` carrying **more than one staged fill node
with varied labels** (i.e. sibling mode) raises"*, justified by "m50's axis mode with weight labels only
collapses to ONE fill node (§6.2, arity `1 + |S|`), where the merge hazard does not exist". That
carve-out is incomplete: §6.2 explicitly permits **shift siblings targeting the same pre-declared
variation axis** ("one histogram carrying both classes, filled from separate passes with a scalar
label, is the field's actual layout"), and m50 anchors exactly that ("a mixed shift+weight program
lands in ONE axis-mode histogram equal to its sibling-fill decomposition"). Such a histogram has
`1 + |S| > 1` fill nodes **with varied labels** — matching the frozen refusal predicate — yet summing
them is precisely correct: each sibling writes its own bin of the shared `"variation"` axis, so
`_SumFills` merges nothing.

**Evidence** (`graphed-histogram-latest@211cbbe`, `src/graphed_histogram/boost.py:88-98`):
`_SumFills.__call__` is `total = zero_of(spec); for f in fills: total = total + f` — histogram addition.
For axis-mode siblings with disjoint variation-axis bins that is the identity-preserving combine, not a
universe merge. §6.1c's stated justification ("would silently merge universes into a plausible-looking,
physically wrong result") is false for this configuration.

The frozen m48 test is read-only from freeze, so m50 inherits a permanent refusal on a path that is
correct. Nothing in m50 says "mixed axis-mode routes through the group `plan()` only", so an implementer
has no instruction either way.

**Suggested fix.** Word the m48 anchor over **sibling mode explicitly**, not over the fill-node count:
raise when the staged fill nodes carry varied labels **and the histogram is not in axis mode** (the
axis-mode opt-in is a recorder-side flag the frontend already owns per §6.2(i)). Alternatively state in
§6.2 that axis-mode histograms are group-API-only in v1 and park single-histogram `.plan()` for them in
§11 — but say one of the two.

---

### M2 — §2.3d claims exhaustiveness over `graphed`'s public Array-consuming surface and is measurably not exhaustive

**Section**: §2.3(d).

**Detail.** §2.3d is worded as a completeness claim — *"the enumeration is **EXHAUSTIVE** over
`graphed`'s public Array-consuming surface (r12; the r11 list named three and left the rest undisposed,
which is not harmless …)"* — and cites `python/graphed/__init__.py:8-25`, `__all__` `:27-58`. It disposes
`join`, `repartition`, `apply`, `read_columns`, `compile_ir`, `evaluate_ir`, `aggregate_plan`,
`graphed.awkward.to_parquet`, `Histogram.fill`.

**Measured** (`graphed-latest@ff7c607`, `python/graphed/__init__.py:8-25` + `__all__` `:27-58`, and
`python/graphed/shuffle.py`): three further public exported verbs take `Array` and are undisposed —
- `pack_key(array: Array, *, on: Sequence[str]) -> Array` (`shuffle.py:84-89`) — public by design
  ("also public so a caller can pre-key a source"); reads `array.session`;
- `shuffle_plan(output: Array, *, reduce, combine, empty, …)` (`shuffle.py:142-150`) — reads
  `output.session`;
- `join_plan(output: Array, *, …)` (`shuffle.py:208-220`) — reads `output.session`.

All three are in `__all__`. Under §2.2's reserved-name rule they would at least fail cleanly with
`AttributeError` rather than compiling a `field` op, but that is the fallback the section itself calls
insufficient for `compile_ir`/`aggregate_plan`, which it nevertheless disposes explicitly. A claim of
exhaustiveness that a five-minute grep falsifies is worse than a scoped list, because it tells the
implementer to stop looking.

**Suggested fix.** Add the three to the enumeration with their disposition — `pack_key` **broadcasts**
(it is a fusible `Op`, not a boundary, `shuffle.py:86-89`) or refuses; `shuffle_plan`/`join_plan`
**refuse** with the §5.4 boundary message (they are Exchange/Join plan builders, so §5.4 already
governs them). Or restate the sentence as "every verb below plus any Array-consuming export not listed
refuses", and name the discovery rule the way §2.3c does for gak.

---

### M3 — §4.3's bound extraction mechanism depends on a public `(output, label) → node id` accessor that no section names or pins

**Section**: §4.3, §7.2, §9.1, m48 anchor "§4.3 structural selection-invariance".

**Detail.** r12 bound §4.3's extraction: *"compute `reachable(fill_node[label])` per label via
`session.walk` … `fill_node[label]` comes from the §6.1c per-slot output indices / §7.2
`(output, label) → node id` map, **the only public per-label fill-node channel** (`Histogram._fill_nodes`
is private)."* §7.2 says only that *"the frontend **owns** `(output, label) → node id`"* — ownership, not
a public accessor — and §9.1's introspection surface enumerates `labels`/`universe`/`nominal`/`weight`/
`variations`/`selection`, the §3.4 impact API, and "a plan-level listing of `{output: [labels]}`" —
labels, **not** node ids. So the m48 anchor's bound mechanism reaches for a surface that PART II never
brings into existence, while every other new surface in this plan carries an explicit
"spelling pinned at m<x> freeze" clause (`graphed.broadcast_like`, `graphed.selection`,
`graphed.read_varied`, the §6.2 opt-in, the `is_data=True` constructor).

`session.walk` itself checks out for this use — verified `python/graphed/session.py:245-289`: it is a
generic post-order evaluator over sources/externals/ops, and reductions/exchanges/joins all live in
`Session._ops` (`:165,180,201`), so a handler-based reachability walk covers the whole recorded graph.
The gap is only the per-label fill-node handle.

**Suggested fix.** Add the accessor to §9.1's introspection surface with the standard clause — e.g.
`graphed.fill_nodes(result_or_histogram) -> {(output, label): node_id}` (spelling pinned at m48 freeze),
m48 target — and have §4.3 and the m48 anchor cite it by that name.

---

### M4 — §10's milestone bookkeeping did not follow r12's move of m49's headline matrix to `graphed-histogram`

**Section**: §10 preamble (frozen layouts), m49 header.

**Detail.** r12 moved m49(i), the 15-reference matrix and the §5.2b read witness, into
`graphed-histogram`, flat `tests/frozen/m49` (line 1616 f., with the fixture argument spelled out). Two
places were not updated:
- §10's directory pinning still reads *"`graphed-executors` = flat `tests/frozen/m49`;
  **`graphed-histogram` = flat `tests/frozen/m48` and `tests/frozen/m50`**"* (lines 1364–1366) — omitting
  the m49 directory it now must host, in the very paragraph whose stated purpose is that "duplicate
  basenames have bitten it before" and directories are pinned now.
- m49's header still reads *"**m49 — shift path + impact + executor end-to-end** (repos: `graphed` +
  `graphed-executors`)"* (line 1612) while its headline anchor and its only mechanism witness live in
  `graphed-histogram`.

This is not cosmetic: the repo list is what the DoD's "full-matrix CI green at the pinned revision
(R0.5)" and the per-repo freeze tagging key on. A milestone whose headline gate lives in an unlisted
repo can be declared DONE with that repo's CI unexamined.

**Suggested fix.** Add `tests/frozen/m49` to `graphed-histogram`'s pinned directory list and add
`graphed-histogram` to m49's repo line (`graphed` + `graphed-histogram` + `graphed-executors`).

---

### M5 — the milestone target lists omit §9.1, though `graphed.weight` is §9.1-only, m48, and load-bearing for an m48 anchor

**Section**: §9.1, §10 m48/m50 target lines.

**Detail.** §9.1 introduces `graphed.weight(ctx)` and marks it **m48**, and §2.6a agrees ("`graphed.
variations` lands in m50, `graphed.selection` in m51, **the rest in m48**"). r12 then made it
load-bearing twice: §6.4b's "their varied factors, when among the stored fields" is stated to be
unsatisfiable without it, and m48's straddling-anchor assignment says the §2.1 stacking anchor "**MUST
use it** rather than a fill" so it can stay in `graphed`'s half of the split.

But m48's target line is *"§1, §2 (incl. the §2.6 event context), §3.2/§3.4 (API only), §4, §6.1 (incl.
§6.1d ambient fills), §7.2, §6.3"* — no §9.1 — and §9 appears only under **m50** ("Targets: §6.2, §9").
`graphed.weight` is defined nowhere in §§1–8, so under the DoD's "Implementation Targets done exactly as
specified" it is an m50 target being consumed by an m48 frozen anchor.

**Suggested fix.** Add "§9.1 (`graphed.labels`/`universe`/`nominal`/`weight` only)" to m48's target
list, and scope m50's to "§9.1 (`graphed.variations`) + §9.2"; m51 already carries `graphed.selection`
through §6.4a's bridge text, but naming it in m51's target line would close the same loop.

---

## LOW

### L1 — §3.1's absolute "no optimizer change" vs §8.2's m49 core accessor

§3.1 binds *"No Rust IR variant, no serialize tag, **no optimizer change** is added for variations."*
§8.2 then scopes an m49 core accessor returning `record_node_id -> (reduced_node_id, member_index |
None)` and asserts *"§3.1 still holds … no new `NodeKey`, no serialize tag, **no optimizer arm**, no
semantics."* The two are not the same claim: the accessor's data is the DCE `remap` vector which today
*"lives entirely inside `dead_code_elimination` and is never returned"* (`src/optimizer/mod.rs:88-116`,
as the plan itself measures), so surfacing it means retaining and returning it — a change to optimizer
code, if not to optimizer semantics. An integrity reviewer reading §3.1 literally can flag the m49 work
as an owner-locked violation.

**Fix**: reword §3.1 to "no optimizer **semantics** change; the only optimizer-adjacent addition is
§8.2's read-only remap accessor (m49)", and cross-reference it from §8.2.

### L2 — §6.1d leaves the numpy `broadcast_like` semantics as an either/or

§6.1d binds `graphed.broadcast_like(value, factor) -> Array` as a neutral backend-dispatched seam, then:
*"the numpy idiom documents **a no-op (rectilinear, already aligned) or a refusal**."* Two different
observable behaviours for the same Implementation Target, chosen by the implementer. Every other seam in
this plan is bound or explicitly exempted (`§6.4f numpy: EXEMPT — varied writes refuse`). A no-op and a
refusal are not interchangeable: the first makes an all-numpy varied fill work, the second makes it
fail.

**Fix**: pick one (a no-op is the consistent reading — `graphed.numpy` is rectilinear and its shapes are
numpy's own, `python/graphed/numpy/__init__.py:8`) and state it, with the fallback that a genuine shape
mismatch surfaces as numpy's own error at execution.

### L3 — §1.1: the input grammar admits magnitudes the canonical integer rendering then rejects on length

The input-sugar grammar is `-?\d+(\.\d+)?([eE][+-]?\d+)?` with no magnitude bound, and integer values
"render as plain digits". So `"1e40"` is accepted as input, canonicalizes to a 41-digit tag, and is then
rejected by the 32-character cap — with a *tag-length* message, for a spelling the grammar advertises as
legal. The asymmetry is odd too: `"1e-40"` → `1em40` (5 chars, accepted) while `"1e40"` is refused. No
real σ-scan / μR-μF / PDF family reaches this, so the practical cost is only a confusing error.

**Fix**: one clause in §1.1 — an integer-valued input whose plain-digit rendering exceeds the cap is
rejected **at canonicalization** with a message naming the magnitude, not a generic length error (or
state that large-magnitude integers are simply out of the tag domain).

### L4 — §7.3's one-time-churn paragraph covers `_PartitionReduce` (m49) but not `_WritePart` (m51)

§7.3 documents the m49 all-programs checkpoint churn honestly: §8.2(i) adds a field to
`_PartitionReduce`, which is the plan's opaque `process` spec, and `task_id` folds
`self.process.identity()` (`plan.py:72-90,164-176`). The identical mechanism applies to m51: §6.4f binds
widening `_WritePart.__call__`'s single-output unpack, and `_WritePart` is the **write** plan's `process`
spec — verified `python/graphed/awkward/io.py:239,260,274` (`_WritePart(...)` → `gw.write_plan(partitions,
writer)`) and `python/graphed/write.py:32-43` (`Plan(process=write_part, …)`). Every existing write-plan
journal is invalidated once when m51 lands, including for unvaried writes.

**Fix**: one sentence in §7.3 (and in m51's docs anchor if it has one), same shape as the m49 paragraph.

---

## NIT

### N1 — §6.2's heading says "weight labels only" while its body permits scalar-labeled shift siblings

The heading reads *"§6.2 (Scaling shape: the variation axis, m50 — **weight labels only**.)"*; the body
binds that shift siblings **MAY** target the same pre-declared axis, and m50 anchors a mixed program.
The heading is a leftover from r1's scoping. Reword to "weight labels in the evaluator loop; shift
labels as scalar-labeled siblings on the same axis".

---

## Verdict

**DIRTY — but structurally sound.** The architecture (record-time expansion + interning, contexts as
immutable lineage, sibling-fill default with an opt-in axis mode, superset+augmentation write) is
coherent, and the parts that got the most review rounds (§1.1 canonicalization, §2.4 label-aligned
union, §5.x, §6.1c layout, §7.2 node-id keying) survived hard probing this round with no defects found:
§1.1's e-form edge cases (exact decimal arithmetic, minimal re-rendering of canonical tags, negative
zero, cross-notation rejection under both parsers) are internally consistent apart from L3; §2.4's
label-aligned union composes correctly with §2.6c's per-label re-indexing on the mainline sketch (checked
label by label for a fill from a Varied-mask-derived context carrying both weight and shift labels);
§4.3's `session.walk` reachability mechanism is implementable as bound (walk covers reductions, exchanges
and joins — all route through `Session._ops`); §6.1c's `_GroupReduce` mis-slicing diagnosis and the
indices-based repair are correct against the measured code; and no requirement violates the
package-boundary rules (the broadcast seam, the context mechanism and `to_parquet`'s idiom placement are
each on the right side of the line, and `graphed-core` gains only a read-only accessor).

The three HIGHs are all in the newest surfaces, as expected: one is a third-iteration recurrence of the
same "the channel does not exist" defect (§8.2, now at the attribution layer rather than the key layer),
one re-closes r11's own BLOCKER fix from the opposite direction (§6.4a's entry check vs per-level masks),
and one is an introspection verb that answers a strict subset of what the sink produces (§2.6c/§6.1d).
None requires reversing an owner-locked decision; all three are fixable with bounded edits inside the
existing structure. Recommend one more revision (r13) and a re-review of §§6.4a, 8.2, 2.6c and the m48
`.plan()` anchor before any freeze.
