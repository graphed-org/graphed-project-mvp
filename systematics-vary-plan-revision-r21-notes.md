# Plan revision r21 — audit trail (review round 12, over r20)

Reviser: isolated agent, fresh context. Inputs: `systematics-vary-plan-review-r20-{facts,design,tests}.md`
(13 findings after NIT exclusion — 2 HIGH, 6 MID, 5 LOW; no cross-lens duplicates to merge).
Verification roots used for every code fact: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`/private/tmp/claude-501/graphed-histogram-latest` (211cbbe), and the pinned venvs in each.

**Outcome: 13 applied, 0 rejected, 0 deferred.** No finding's resolution required reversing an
owner-locked decision, so the header carries no new OPEN ITEMS block.

Two findings' *suggested fixes* were altered on the strength of my own measurement (both noted below):
F12's third m48 program (the reviewer's fixture does not discriminate — replaced with one that does,
plus an explicit knowingly-unanchored marking) and F7's route (bound as a public composition plus a
no-private-import rule, per the reviewer's own suggestion, with the merge point named from source).

---

## HIGH

### F3 — design §7.2/§6.1c/m48: `node id → position` "from the compiled output list" is not computable
**Verdict: APPLIED (confirmed).**

Measured myself (probe `/tmp/probe_r21_seam.py`, `graphed-latest@ff7c607` venv, a toy Backend):

```
record ids: src 0, dead 1, b 2, e 3, c 2      # c interns with b
compile_ir(s, b, e, c) -> GraphStore.deserialize(ir).outputs() == [1, 2]
reduced kinds: [(0,'source'), (1,'stage'), (2,'stage')]
evaluate_ir -> 2 values: [[2.0,4.0,6.0], [3.0,6.0,9.0]]   # b's then e's
s._store.outputs() == []
```

- compiled `outputs()` are POST-REDUCTION ids (1,2), joinable to record ids only through the m49
  §8.2(i) accessor, which does not exist.
- `compile_ir` never marks the record store: `python/graphed/execute.py:70-80` passes `ids` as
  `reduce(outputs=ids)` / `serialize(outputs=ids)`; the `mark_output` dedup the plan cites runs when
  `GraphStore::from_reduced` builds the REDUCED store (`src/store.rs:185-200`, `mark_output(map[o])`
  at `:197`).
- The value order IS first-occurrence order over the distinct record ids, so the frontend's own
  ordered marked-id list is the exact operand — and `plan()` already holds it: `fill_nodes` at
  `graphed-histogram src/graphed_histogram/boost.py:281`, one line before `layout` at `:282` and five
  before `aggregate_plan` at `:286` (read in source).
- Divergence between the two orders is possible only under an OPTIMIZER merge, which m48's shortfall
  guard refuses — so the derivation is exact for every program m48 admits.

**Edits:** §7.2's opening re-bound to "index of first occurrence in the frontend's OWN ordered list of
marked record ids", with the probe and the corrected `mark_output` site; the seam paragraph now names
TWO consumers (merge refusal, m49 `variation_labels`) and explicitly withdraws §6.1c's layout as the
third; §6.1c's indices sentence re-bound to `plan()`'s own `fill_nodes`; m48's target line updated;
"*`CompiledGraph`, not ids*" re-worded (the merge refusal needs a COUNT, not `node id -> position`,
which `outputs()` could never have given). New Anchors-appendix row for the probe.

### F4 — design §7.2: seam half (β) unsatisfiable as an input parameter
**Verdict: APPLIED (confirmed).**

Read `python/graphed/aggregate.py:68-108`: `compiled = compile_ir(session, *outputs)` (:95) is
immediately followed by `_PartitionReduce(...)` (:96-104) built from the call's parameters; the
returned `Plan` is constructed at :108. §8.2(i) keys `variation_labels` on post-reduction ids obtained
"for the reduction that produced a given compiled artifact" — i.e. on the artifact this call produces
— while §7.2 forbids compiling twice and §8.2(i) declares the field an immutable sorted tuple
(`_GroupReduce`/`_PartitionReduce` are frozen dataclasses, `boost.py:100-118`, `aggregate.py:44-55`).
So a see-only `on_compiled(compiled)` hook has no path into the shipped closure, and m48's anchor
("fires exactly once, receives the `CompiledGraph`") is green against that dead-end spelling.

**Edits:** §7.2 binds "(β) IS THE HOOK'S RETURN CHANNEL" — the hook is called with the `CompiledGraph`
before the closure is constructed and its RETURN VALUE is attached to the closure as the additive
§8.2(i) field; m48's (α) anchor gains a return-payload assertion (dummy value, readable on
`plan.process`).

---

## MID

### F5 — design §6.1d: label-set inference vs link-kind-(3) projection is unordered
**Verdict: APPLIED (confirmed by reading).** §6.1d(d)'s union rule and the three link kinds are stated
paragraphs apart with nothing sequencing them; for kind (3) the order changes the result shape. On
m48's own fixture `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` the unified context is the CHILD
`graphed.nominal(sel)` (§2.2 r14), whose ambient weight and selection are that label's unvaried
members — so the ancestor value is the sole label source and the two orders give `{label: hist}` vs a
bare `hist` (§6.1a), mutually red under a read-only freeze.

**Edit:** §6.1d(d) binds the label set to be computed AFTER the lineage step; m48's universe/nominal
anchor now asserts the BARE `hist` result and notes it as the discriminator against a
"labels kept, contents identical" implementation.

### F6 — design §2.3d: `reindex_to` "same labels" contradicts §6.1d(B)
**Verdict: APPLIED (confirmed by reading).** §2.3d said "same labels"; §6.1d(B) says "label-aligned
per §2.4" (a UNION), and m48's link-kind-(1) anchor re-indexes the PLAIN Array `events.MET.pt` into
`sel`'s per-label row spaces — impossible without acquiring the mask's labels. The plan's own
precedent (`broadcast_like`) is classified *broadcasting* with §2.4-UNION labels.

**Edit:** §2.3d's `reindex_to` entry re-worded to the §2.4 union (an unvaried value across a `Varied`
mask link BECOMES `Varied`), and §6.1d's own dispositions sentence aligned.

### F7 — design §6.4e: "reproduce awkward's own KV entries" names no route; only producer is private
**Verdict: APPLIED (confirmed).** Measured in `graphed-latest`'s venv (awkward 2.12.0):
`grep -rn awkward_array_metadata awkward/` → 3 hits, all in
`awkward/_connect/pyarrow/table_conv.py:16,23,47`; the key is written by
`convert_awkward_arrow_table_to_native` (`:19-40`), which `ak.to_parquet` imports
(`awkward/operations/ak_to_parquet.py:14`) and calls at `:417`. `ak.to_arrow_table` never adds it
(read `ak_to_arrow_table.py:18-140`). The public merge point exists: `ak_to_parquet.py:424-431` uses
`table.replace_schema_metadata(merged_metadata)` for `attrs`. (pyarrow is absent from that venv, so I
did not re-run the byte/KV probes; the finding depends only on where the key is produced.)

**Edit:** §6.4e binds the ROUTE — the varied write MUST NOT import `awkward._connect.*`, and uses the
public composition (write as awkward's own writer would, then re-read and re-write with
`replace_schema_metadata` + `pq.write_table`), the second write named as the accepted cost of the
varied path. New Anchors-appendix row.

### F10 — tests m50: the `sample=`-only-label anchor is unbuildable on the default storage
**Verdict: APPLIED (confirmed).** Measured, `graphed-histogram-latest` venv, boost_histogram 1.8.0:
`Double()` and `Weight()` both raise `TypeError: Keyword(s) sample not expected`; `Mean()` fills
(MeanView populated) and `WeightedMean()` fills with weight+sample. `FillEvaluator` passes `sample`
straight to `h.fill` (`src/graphed_histogram/boost.py:60-71`, read). `_spec.py:19-27` carries `Mean`
and `WeightedMean` in `_STORAGES`.

**Edit:** the storage requirement and the "per-label sample values must DIFFER" non-vacuity condition
added in BOTH places (§6.1b's r20 paragraph and m50's equality anchor). New Anchors-appendix row.

### F11 — tests m48: the `context_of`-on-a-`Varied` fixture freezes a mixed-row-space container
**Verdict: APPLIED (confirmed).** The bullet's wording admits the mask-derived spelling
(`vary(events.Jet, "jes", up=sel.Jet)`), whose members sit in different row spaces; §2.1's checks are
form + Session + source only (re-verified: `Session.record_op` validates only the backend's `op_form`,
`python/graphed/session.py:142-168`), which is exactly why §2.1(b) r20 made the analogous
weight-factor mis-spelling a construction-time error. The identity-link fixture discriminates
identically (a nominal-member implementation answers `events`).

**Edit:** m48's bullet pins the fixture to a `graphed.vary` IDENTITY link
(`events2 = vary(events, "pu", …, is_weight=True)`; `v = vary(events.Jet, "jes", up=events2.Jet)`;
`context_of(v) is events2`) and states why.

### F12 — tests §2.2: the r20 rebinding of union term (c) is unwitnessed
**Verdict: APPLIED, with a corrected fixture (confirmed, and the reviewer's fixture measured
non-discriminating).** Both m48 programs query a MASK-derived context, where the r13–r19 and r20
readings agree — so the r20 clause had zero frozen coverage. The reviewer's proposed program
(`sel2 = vary(sel, "jer", Jet={…})` over a jes-varied mask) does NOT discriminate under the plan's own
rules: §2.6c makes every read through a `Varied`-mask-derived context `Varied`, and §2.1 stacking then
puts the mask's labels into `sel2.Jet`, i.e. into union term (b); the weight-form variant puts them
into term (a) for the same reason (the plan concedes this: "in the mainline term (a) happens to rescue
the answer"). I could construct no m48–m51-scoped program in which the two readings differ.

**Edits:** (1) §2.2 SCOPES term (b) to the collections a shift-form `vary` REPLACED (not the
implicitly-varied reads §2.6c produces) — without that scoping (b) subsumes (c) everywhere and (c) is
dead text; (2) m48 gains a program that isolates term (c) ITSELF — a context derived by a mask varied
through the LOOSE §2.1a primitive, with no registration and no shift-form `vary`, so (a) and (b) are
both empty; (3) the r20 `vary`-link-walking half is marked KNOWINGLY UNANCHORED with the measured
reason, on §1.1's `"1e1000000000"` precedent, in §2.2 and in the m48 bullet.

---

## LOW

### F1 — facts §10/m48: "`graphed`'s only existing coverage of `aggregate_plan` is m5's"
**Verdict: APPLIED (confirmed).** `grep -rln aggregate_plan tests/frozen` in `graphed-latest@ff7c607`
→ m39's README + `test_shuffle_plan_builder.py`, m40's `test_join_plan_builder.py` (docstring only),
m5's `test_aggregate_plan.py`. m39 imports it (`:18`) and calls it in
`test_single_source_aggregate_plan_is_unchanged` (`:58-64`). **Edit:** the clause now names m5's
positive path plus m39's two-source-rejection control; the bullet's conclusion is unchanged.

### F2 — facts §7.3 + m49: `80e8024dc8f3b77d` is not reproducible
**Verdict: APPLIED (confirmed).** Re-measured (cloudpickle 3.1.2, CPython 3.12.10,
`graphed-latest/.venv`, seeds 1/7/12345) with my own module-level frozen dataclass
(`/private/tmp/claude-501/rev21mod/vmod.py`): importable+sorted-tuple → `7c822d415da97a9c` ×3 (NOT
`80e8024dc8f3b77d`); importable+frozenset → three distinct; §8.2(i)'s NAMED payload reproduces the
plan's triple exactly (`b7984b3caadf74f7` / `2778da7a97834ac5` / `97429e5989f2a831`). The literal
names no module/class/field names, which cloudpickle bytes depend on — failing the plan's own r14
reproducibility standard.

**Edit:** the literal is WITHDRAWN in §7.3 and in m49's anchor, replaced by the reproducible
qualitative statement, with the withdrawal reason recorded.

*Not folded into the plan (measured, offered as context only):* at a FIXED `PYTHONHASHSEED=1`,
`frozenset(("btag_down","btag_up","jes_down","jes_up","nominal"))` digests `dcbaefaddebcaf1b` while the
equal set-literal digests `b7984b3caadf74f7` — frozenset pickle bytes depend on construction order as
well as on hash seed. It strengthens §8.2(i)'s case but no finding required it, so the plan was left
lean.

### F8 — design §6.4a: no depth constraint on a level-0 `select=` mask
**Verdict: APPLIED (confirmed by reading).** (2a) is a handle comparison and (2b) a row-COUNT
comparison; the structural check is scoped to levels ≥ 1. A per-object mask read through the record's
own context passes both (ORIGINATION gives it the handle — the same property that makes r20's fifth
positive control legal — and a jagged boolean over the record's own structure has the record's outer
length), after which the level-0 OR filters objects, not rows.

**Edit:** new predicate **(2c) LEVEL-0 DEPTH, record-time** (depth is a form property), added to the
predicate list, to the "where each runs" summary in both places, and to m51's entry-check anchor as a
negative control with the flat mask as its positive.

### F9 — design §1.1: magnitude pre-check counts DIGITS while the cap bounds CHARACTERS
**Verdict: APPLIED (confirmed by arithmetic).** `-1.5e31` → normalized digit count 32 (passes the
magnitude test) → renders `m` + 32 digits = 33 characters → refused by the generic 32-character cap
with the wrong message class, while `1.5e31` (the r20 boundary pair m48 freezes) is accepted.

**Edit:** §1.1 binds the compared quantity to the RENDERED CANONICAL LENGTH (digit count + 1 when
negative); m48's grammar anchor adds `"-1.5e31"` rejected with the SAME magnitude message.

### F13 — tests §7.2/m48: "MUST NOT compile a second time" unanchored; one anchor clause unassertable
**Verdict: APPLIED (confirmed).** m48's (α) anchor observes the hook firing INSIDE `aggregate_plan`
and cannot see a `plan()`-side compile that preceded it; §3.3's budget is a frozen gate on a different
fixture. The phrase "its `outputs()` readable BEFORE the worker closure exists" has no operand — the
hook receives only the `CompiledGraph`.

**Edit:** the no-second-compile rule is marked knowingly unanchored, riding an R0.11
implementer-report compile count; the m48 bullet drops the unassertable phrase and says so explicitly
(the r21 return-channel assertion is what makes the ordering observable at all).

---

## Bookkeeping

- Status line → **draft for review (r21)**.
- Revision-history entry added at the head of the history, summarising by severity and section.
- Anchors appendix: three new rows (compile/mark_output/outputs probe; awkward private KV producer;
  boost_histogram `sample=`-by-storage), plus corrected `src/store.rs` spans (`:185-200`, `:197`).
- Files touched: `systematics-vary-plan.md` and this notes file only.
