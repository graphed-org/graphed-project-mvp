# Plan revision r20 — audit trail (review round 11, from r19 reviews)

Source reviews: `systematics-vary-plan-review-r19-{facts,design,tests}.md` (19 findings after NIT
exclusion; 17 unique after merging two cross-lens duplicate pairs — DESIGN §7.2-seam-unanchored ≡
tests "r19's new `aggregate_plan` seam", and DESIGN §6.1a-mypy ≡ tests "wholly-unvaried positive
control's rationale"). Verification roots used: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`/private/tmp/claude-501/graphed-histogram-latest` (211cbbe). Every code fact below was re-measured
or re-read in THIS session; nothing is carried over from the reviews on trust.

**Outcome: 17/17 applied. Nothing rejected, nothing deferred.** No finding's resolution required
reversing an owner-locked decision, so no OPEN ITEMS block was added.

---

## HIGH

### 1. DESIGN §6.1d — fill-side lineage unification/re-indexing has no public surface at m48 — APPLIED

Verified: `Histogram.fill` is `graphed-histogram src/graphed_histogram/boost.py:153-212` (read this
session at `211cbbe`), a different distribution from `graphed`. §9.1's m48 surface (read in the
plan) is `labels`/`universe`/`nominal`/`weight`/`context_of`/fill-node accessor/`unpack`; nothing
relates two handles or yields a derivation mask, and `graphed.selection(ctx)` is marked m51 in both
§9.1 and m51's target line. m48 nonetheless assigns `§6.1d link-kind-(1) ancestor-VALUE re-indexing`
and the projected-VALUE half of the universe/nominal clause to `graphed-histogram`'s flat
`tests/frozen/m48`.

Edit: new bound paragraph in §6.1d binding **two read-only m48 seams in `graphed`** —
`graphed.unify_contexts(*handles)`-shaped (most-derived handle / `None` / §2.3e divergence error)
and `graphed.reindex_to(value, ctx)`-shaped (link kinds (1)-(3), label-aligned, identity when the
handle already matches, raising on the wrong direction). Listed in §9.1; added to m48's §9.1 target
line; §2.3d disposes both (`reindex_to` *broadcasting*, `unify_contexts` outside the
`Array`-consuming surface like `evaluate_ir`); new m48 anchor bullet in `graphed`'s half so the new
`graphed` source carries frozen-suite diff coverage. `graphed.selection` was NOT moved — with
`reindex_to` doing the mask work inside `graphed`, m48 needs no mask accessor across the boundary.

### 2. DESIGN §6.4a(2a) case (ii) stale against r19's handle-equality predicate — APPLIED

Verified in the plan: r19's rule is `graphed.context_of(select_mask) is graphed.context_of(record)`;
case (ii) is written over "the supplied mask DERIVED NO CONTEXT" and m51's anchor repeats that
wording; §2.3e's ORIGINATION rule gives every read performed through a context THAT context's
handle. So `select=(events.MET.pt > 50)` on a record read from `events` is accepted by the predicate
and refused by (ii) — a contradiction that freezes a refusal for a legal program.

Edit: (ii) re-expressed as "the supplied mask carries NO context handle (a hand-built loose mask,
§2.3e Drop rule)", with an explicit sentence that a contexted mask carrying the record's OWN handle
is ACCEPTED whether or not any context was derived from it; m51's entry-check anchor re-worded
identically and gains that case as its fifth positive control.

### 3. DESIGN + TESTS (merged) §7.2 — the r19 `aggregate_plan` seam is an m48 `graphed` target with no `graphed` m48 anchor — APPLIED

Verified: `python/graphed/aggregate.py:68-108` — `aggregate_plan` compiles internally at `:95` and
builds the frozen `_PartitionReduce` from pre-built closures; `graphed_histogram.plan()` builds
`layout` at `boost.py:282` before the `aggregate_plan` call at `:286` (both read this session), so
the seam's premise is right. `grep -rn aggregate_plan tests/frozen/` in `graphed-latest` returns
m5, m39 and m40 hits only — no m48 anchor; and grep over the plan for `SEAM|on_compiled|factories
over the compiled` returns §7.2, m48's target line and the revision history, never an anchor.

Edit: §7.2 gains a bound "each half is anchored in the repo whose source it is" paragraph; new m48
frozen-anchor bullet in `graphed`'s `tests/frozen/frontend/m48` over an UNVARIED build in m5's call
shape (hook fires exactly once, receives the `CompiledGraph` before the worker closure exists,
resulting `Plan` runs to the same value as the hookless build); (β) explicitly anchored at m49 and
named on m49's target line, with the §8.2(i) plan-byte determinism bullet marked as its coverage.
(The second, smaller instance the reviewer raised — `broadcast_like`'s awkward branch — is left
alone: §2.3d already disposes `broadcast_like` and m48's gate is metadata-only, so no anchor is
red; naming a backend for it would add a constraint no finding shows to be load-bearing.)

## MID

### 4. DESIGN §2.3e/§2.1 — `context_of` on a `Varied` bound two ways — APPLIED

Verified in the plan: §2.3e says *eager-metadata* "answering on the nominal member for a `Varied`";
§2.1 r18 says "all members' handles MUST lie on ONE ancestry chain, the container carries the
most-derived one" and §2.1's construction checks are form/Session/source, never row space. The two
disagree exactly when the most-derived handle is a non-nominal member's — a container §2.1 accepts.

Edit: §2.3e binds the CONTAINER's handle as the answer, states that *eager-metadata* here means only
"answered without recording", and m48's §2.3d table anchor gains the discriminator (ancestor-handled
nominal + more-derived non-nominal member → the more-derived handle).

### 5. DESIGN §7.2 vs §8.2(i) — seam (α) under-specified: output ids cannot serve `variation_labels` — APPLIED (merged edit with #7)

Verified in the plan: §8.2(i)'s m49 accessor answers "for the reduction that produced a given
compiled artifact"; §7.2 forbids a second compile.

Edit: (α) is bound to expose the **`CompiledGraph`** itself, with the m49 dependency named beside
the §6.1c and §7.2 ones.

### 6. DESIGN §2.1(b) — the row-space contract closes only the ANCESTOR direction — APPLIED

Verified: `python/graphed/session.py:142-168` — `record_op` calls `backend.op_form` and records; no
length or row-space validation anywhere in it (read this session). A DESCENDANT-handled factor is
on the same ancestry chain, so §2.1's divergence check passes and nothing else catches it.

Edit: §2.1(b)'s violation half restated as total ("neither the target's own nor an ANCESTOR of it —
a DESCENDANT as much as a divergent one — is a construction-time error naming both contexts and the
DIRECTION"); m48's stacking anchor gains the descendant negative control beside its r19 positive one.

### 7. DESIGN §2.2 vs §9.1 — `graphed.labels(ctx)`'s third union term has no answer for a vary-derived context — APPLIED

Verified in the plan: §2.2(c) = "the labels of the mask that derived it"; §6.1d binds THREE link
kinds; §9.1 r16 binds `graphed.selection` to skip `vary` identity links; §2.6's sketch rebinds `sel`
through a `vary` call.

Edit: (c) replaced by "the labels of `graphed.selection(ctx)` in §9.1's sense" with the universe/
nominal case spelled out (contributes no labels) and an explicit note that the definitional
reference does not move `graphed.selection`'s m51 milestone.

### 8. DESIGN §10/m48 — the §7.2 varied merge-refusal lands in `graphed`, where its own SITE binding makes it need `importorskip` — APPLIED

Verified: `graphed-histogram src/graphed_histogram/boost.py:256-292` — `plan()` is the only place
`(output_name, Histogram)` pairs exist (`items = …`, `layout = …` at `:282`), so triggering the
guard needs `Histogram.fill` + `gh.plan(...)`.

Edit: m48's split sentence gains a second exception (the VARIED half of the §7.2 merge-guard clause
→ `graphed-histogram`; the unvaried `compile_ir(s, b, b * 1.0)` scope control stays in `graphed`),
and §10's "any clause whose assertion requires a `Histogram.fill` lives in `graphed-histogram`" rule
is promoted out of straddling-anchor (3) to a general m48 splitting rule.

### 9. TESTS §6.1b — the `S`/`W`-by-lowering definition is binding and unanchored — APPLIED (with a correction)

Verified in the plan: the only anchor naming a `Varied` `sample=` is m48's fold-order bullet
(position + ACCEPTED); m49's arity anchor states no sample fixture; m50's scaling anchor is
"scoped to WEIGHT labels only". Correction to the reviewer's suggested fix: adding a sample-only
label to **m49's** sibling arity anchor is NOT discriminating — `1 + |S| + |W|` counts every label
once whatever its class, so the total is identical under both classifications. The split is
observable only in axis mode (`1 + |S|`).

Edit: §6.1b states where the split is witnessable and binds the anchor to m50; m50's equality anchor
gains a label borne ONLY by a `Varied` `sample=`, asserting it lowers as a SIBLING and that the
axis-mode result still equals its sibling-fill decomposition.

### 10. TESTS §1.1 — the r19 digit-count normalization has no boundary anchor — APPLIED

Verified arithmetic: `1.5e31` = `15` followed by 30 zeros = 32 plain digits (at the cap, legal);
the naive "mantissa digits + exponent" gives 2 + 31 = 33 and rejects it. `1e40` is rejected by both
computations, so m48's existing clause cannot discriminate. Chose `"1.5e32"` (33 plain digits) as
the rejected neighbour rather than the reviewer's `"1.55e31"`, which is also 32 digits
(`155` + 29 zeros) and therefore legal.

Edit: m48's grammar anchor gains the pair (`"1.5e31"` accepted with its canonical tag, `"1.5e32"`
rejected with the magnitude message) and §1.1 points at it; the "count before rendering" rule is
flagged knowingly unanchored (its witness would be a hang/OOM, not a clean red).

### 11. TESTS §7.2 — "reduce/empty supplied as factories" is not implementable without changing an m5-frozen signature — APPLIED

Verified: `graphed tests/frozen/frontend/m5/test_aggregate_plan.py:77,88,102` pass plain callables
(`reduce=_sum_each`, `empty=lambda: [0, 0]`), and `_sum_each` takes one positional argument, so a
"factory over the compiled output ids" is not duck-typeable apart from a reducer.

Edit: §7.2 binds the seam ADDITIVE — the `reduce`/`combine`/`empty` contracts are unchanged, the
seam is a NEW optional `on_compiled(compiled)`-shaped hook — and the factory illustration is dropped.

## LOW

### 12. DESIGN §1.1 vs §2.2 — the family check needs a name → tags map `Varied` does not carry — APPLIED

Verified in the plan: §1.1 defines a family over one `name`'s tags including inherited labels; §2.2
binds `Varied` as `{label: Array}`; `graphed.variations` is a CONTEXT verb landing at m50.

Edit: one clause in §2.2 — `Varied` additionally retains, per `name`, the tags registered under it
(internal state; the label mapping stays the public shape), with the prefix-ambiguity reason stated.

### 13. DESIGN §10/m49 — the target line omits §9.1's per-label projection-stats verb — APPLIED

Verified in the plan: §9.1 marks the verb m49; m49's §5.3 anchor reads through it; the target line
named only §3.3/§3.4/§5/§7/§8 + §2.5's diagnostic.

Edit: appended to m49's target line (together with seam half (β)), citing the r13/r18 precedents.

### 14. DESIGN §2.3d — the m49-landing `Array`-consuming verbs get no disposition class — APPLIED

Verified in the plan: m48's gate enumerates `graphed.__all__` filtered to functions any of whose
parameter annotations mentions `Array` and asserts every member carries a disposition; §5.3's stats
verb is defined over `read_columns`' operands (a `Sequence[Array]`).

Edit: one sentence in §2.3d — the m49 verbs (§3.4's impact helper, §5.3's stats verb) enter the
table *expanding*; the self-repair rule (classification in `src`) is the mechanism and every floor
is a containment floor, so nothing reds.

### 15. DESIGN §2.2/§10 — the property classifier's measurement step raises on a ≥2-D fixture — APPLIED

Measured this session (`graphed-latest@ff7c607`, its own `.venv`): on a 1-D source
`dtype`/`ndim`/`shape` give `Session.node_count()` delta 0 and `T` delta 1; `gnp.ones(s, (4, 3)).T`
raises `GraphedTypeError: ill-typed op 'transpose' … transpose without axes reverses them,
displacing the partitioned axis 0`.

Edit: m48's §2.3d anchor bullet repeats the 1-D constraint with the measured message.

### 16. DESIGN + TESTS (merged) §10/m48 §6.1a — the positive control's `mypy` claim is false — APPLIED

Verified: `graphed-histogram src/graphed_histogram/boost.py:262` is `) -> Plan[dict[str,
bh.Histogram]]:` and `_GroupReduce.__call__` is annotated `-> dict[str, bh.Histogram]` at `:101-118`
(read this session), while §6.1a binds a varied plan's value to `(output, label)` / `(output, None)`
keys — so the annotation must widen.

Edit: the control re-worded — the runtime bare keys and m23 indexing are unchanged; the declared
type WIDENS to `Plan[dict[str | tuple[str, str | None], bh.Histogram]]` as part of m48's §6.1c
target.

### 17. TESTS m49 §8.2(i) — the `2N + 2` / `N + 1` clause is exact on only one of the named topologies — APPLIED

Measured this session against `graphed-latest@ff7c607` with `graphed.core.GraphStore` on the §3.3
builder shape (D=20, K=5, every universe's terminating reduction marked as an output):

| topology | N=3 | N=16 |
|---|---|---|
| base | reduced 8, `{source 1, stage 4, reduction 3}` | 34, `{1, 17, 16}` |
| base + unmarked dead branch | 8, `{1, 4, 3}` (DCE removes it) | 34, `{1, 17, 16}` |
| base + node shared by two non-nominal universes | 9, `{1, 5, 3}` | 35, `{1, 18, 16}` |
| both extensions | 9, `{1, 5, 3}` | 35, `{1, 18, 16}` |

i.e. `2N + 2` / `N + 1` stages on the base (± dead branch) and `2N + 3` / `N + 2` with the shared
node — confirming the reviewer's numbers independently.

Edit: the anchor scopes the cardinality clause to the BASE fixture (± the unmarked branch) and
records the shared-node fixture's measured `2N + 3` / `N + 2` so a test-author does not merge the
two topologies.

---

## Rejections / deferrals

None. Two review suggestions were narrowed rather than taken verbatim, both recorded above:
finding 9 (the m49 arity fixture is class-blind, so the anchor went to m50 only) and finding 10
(`"1.55e31"` is itself 32 digits and legal; `"1.5e32"` is the correct 33-digit neighbour). One
secondary sub-claim inside finding 3 (`broadcast_like`'s awkward-vs-numpy backend disposition) was
not acted on: §2.3d already disposes the verb and m48's gate is metadata-only, so no anchor is red
either way and naming a backend would add an unforced constraint.
