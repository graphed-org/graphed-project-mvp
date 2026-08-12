# `systematics-vary-plan.md` — review round 13, lens: **DESIGN SOUNDNESS**

- **Plan revision reviewed:** r21 (`systematics-vary-plan.md`, 5069 lines, read in full: header, Part I,
  every PART II section, §10 milestones, §11, §12, Anchors appendix, revision history).
- **Date:** 2026-07-30.
- **Lens:** PART II as an implementable specification — internal contradictions, unhandled
  interactions, under-specified Implementation Targets, package-boundary/factorization violations,
  milestone-boundary consistency. Deepest attention to the newer surfaces per the review brief:
  §2.6 functional context, §6.1d, §6.4/m51, §1.1 r9 e-canonicalization, and every r21 clause.
- **Owner-locked decisions** (naming, functional surface, e-form canonical, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2
  pull-in) were treated as fixed; nothing below asks for a different choice.

## Verification roots used

| Root | Revision | Used for |
|---|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607` | `python/graphed/aggregate.py`, `array.py`, `awkward/io.py`, `session.py` |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe` | `src/graphed_histogram/boost.py`, `_spec.py`, its `.venv` (bh 1.8.0) |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea42` | (not needed for any finding below) |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4` | (cross-checked against the vendored copy; no finding) |

Commands run in-session are quoted inline with each finding.

## Summary

The plan is in strong shape for its lens. The heavy r15–r21 work on the fill/lineage seams
(§6.1d(A)/(B), §2.3e origination, §6.4a's handle-equality predicate) has closed the class of hole
that used to dominate these reviews — I re-derived the §2.6 sketch end-to-end (pu/pdf weights → JES
shift form → derived context → selection-scoped b-tag) against §2.1's stacking rule, §2.4's
label-aligned union, §2.6c's per-label re-indexing and §6.1d's fold order, and it comes out
consistent, one-at-a-time, and matching the corpus reference semantics at every label. §6.4's two
entry predicates plus r20's fifth positive control and r21's (2c) depth check now decide all five
m51 controls the plan lists, and I could not construct a sixth program that falls between them at
level 0.

Nine findings, none blocking: **0 BLOCKER, 0 HIGH, 4 MID, 5 LOW.** Three of the four MIDs are
consequences of r21's own two structural changes (the (β) return channel and the `reindex_to`
disposition) that were not propagated to the sections those changes now govern; the fourth is a
genuine gap in §6.4's per-level `select=` model on the record shape m51's own round-trip anchor
requires.

One false lead is recorded for the record: I suspected §6.1b r21's `Mean`/`WeightedMean` clause was
under-specified because `Mean()` cannot carry the weight labels the m50 mixed program needs.
**Measured false** — bh 1.8.0 `Mean()` accepts `weight=` alongside `sample=`
(`Mean ['sample','weight'] -> OK`), and `spec_of`→`zero_of` round-trips a named `StrCategory`
alongside a `Regular` on `Mean()` storage and adds (`names [None, 'variation']`, `add ok True`).
r21's clause is correct as written.

---

## MID-1 — §7.2's (β) field lands at **m48**, but §7.3 and m50's frozen docs anchor attribute the one-time journal churn to m49

**Section:** §7.2 / §7.3 / §10 m48 / §10 m50 docs anchor.

**Detail.** r21 bound §7.2's seam half (β) as the hook's *return channel*: "the hook is called with
the `CompiledGraph` before the worker closure is constructed, and its RETURN VALUE (the per-plan
variation metadata, or `None`) is attached to the shipped closure as the additive §8.2(i) field."
m48's `graphed`-side anchor then freezes the observable: "**Plus the RETURN-CHANNEL assertion,
r21** … a value returned from the hook — a dummy at m48 — is carried onto the SHIPPED closure and is
readable there (`plan.process`)".

That means the additive field on `_PartitionReduce` **exists at m48**, not m49. But §7.3 still says:

> **One-time churn on landing m49, SCOPED (r17)**: §8.2(i) adds a field to `_PartitionReduce`, so
> every journal whose `DurablePlan.process` `OpSpec` embeds `_PartitionReduce` by value is
> invalidated once, *unvaried* programs included (the field is unconditional).

and m50's **frozen** docs anchor freezes that scoping into the user documentation: "all three
invalidation classes, each with the scope §7.3 binds … the label-RENAME class and **m49's one-time
closure churn** apply only to journals whose `DurablePlan.process` `OpSpec` embeds the worker
closure BY VALUE".

Adding the field at m48 changes the pickled state of every `_PartitionReduce` instance, and the plan
itself establishes that those bytes reach `task_id` through `OpSpec.identity()`. So the churn is an
m48 event and the m50 docs anchor freezes a false milestone attribution — precisely the defect class
r17 fixed when it scoped the unscoped churn sentence ("Freezing the unscoped r16 sentence would put
a false claim in the user docs").

**Evidence (verified this session).** `graphed-latest@ff7c607`,
`python/graphed/aggregate.py:44-65` — `_PartitionReduce` is a `@dataclass(frozen=True)` whose
fields are exactly `ir, source_name, backend_factory, reader, columns, externals, reduce`; a new
field changes the instance state that `cloudpickle` serializes. `aggregate_plan` constructs it at
`:96-104`, one line after `compiled = compile_ir(session, *outputs)` at `:95` — i.e. exactly where
r21 places the hook. The plan's own `core/plan.py:72-76,164-176` chain (opaque `OpSpec.identity()` =
the cloudpickle blob → `task_id`) is what makes the state change a churn.

**Suggested fix.** In §7.3, change "One-time churn on landing **m49**" to "on landing **m48**",
naming §7.2's (β) seam (not §8.2(i)) as the edit that adds the field, and note that m49 only
*populates* it (which churns nothing further for unvaried programs, whose value stays the default).
Re-word m50's docs anchor to "the milestone that adds the closure field (m48)". Everything else in
§7.3's scoping argument (by-value journals only, `from_ref` unaffected, `graphed-executors` has
zero `task_id`/`DurablePlan` references) carries over verbatim.

---

## MID-2 — §2.3d/§6.1d's `reindex_to` label rule ("§2.4 union with the intervening masks'") is false across a link-kind-(3) projection, and m48 anchors both readings

**Section:** §2.3d (r21) / §6.1d(B) + link kind (3) / §10 m48 `graphed` lineage-seam anchor.

**Detail.** r21 rewrote `graphed.reindex_to`'s §2.3d disposition to close a real hole (r20's "a
`Varied` with the SAME labels" silently dropped a mask's labels). The replacement is stated
**unconditionally**, twice:

- §2.3d: "**`graphed.reindex_to` … BROADCASTS** — the result's labels are the **§2.4 UNION of the
  value's labels and the intervening masks' labels**, each member re-indexed by that label's own
  mask, so an UNVARIED value re-indexed across a `Varied`-mask link BECOMES a `Varied` carrying that
  mask's labels".
- §6.1d, at the (B) binding: "`reindex_to` **broadcasts** (the result's labels are the §2.4 union of
  the value's and the intervening masks', exactly like `graphed.broadcast_like`, r21 — §2.3d)".

But §6.1d(B) also defines the operation as "composing link kinds (1)-(3) in lineage order", and link
kind (3) does the opposite of a union:

> **(3) universe/nominal projection link** (§2.2) — PROJECT each ancestor `Varied` value to that
> label's member (falling back to its `"nominal"` member per §2.4), **yielding an unvaried value** in
> the ancestor's row space, then continue with the links below it.

A lineage path that ends on (or passes through) a universe/nominal-derived context therefore yields
an **unvaried** result, carrying *no* labels — not the union. This is not a corner case: it is
exactly m48's own anchored fill fixture, where the unified context is `graphed.nominal(sel)` and the
ancestor value `sel.MET.pt` (handle `sel`) is re-indexed into it. §6.1d's own r21 ordering clause
depends on that projection producing no labels ("a value reached across a universe/nominal
PROJECTION link contributes NO labels, having been projected to one label's unvaried member"), and
m48's fill anchor now freezes the resulting **BARE `hist`**.

Meanwhile §10/m48's `graphed`-side lineage-seam anchor bindingly requires `reindex_to` to be
exercised "across link kinds (1)-(3)". A test-author writing the (3) case from §2.3d's sentence
freezes "result is a `Varied` whose labels are the union"; one writing it from §6.1d(3) freezes "the
result is an unvaried `Array`". Both are read-only after freeze and they are mutually exclusive —
a mid-m48 Test Dispute of the exact shape §6.1a's r18 repair (result shape vs combine shape) was
written to prevent.

**Evidence.** Textual, within the plan: §2.3d's `reindex_to` paragraph; §6.1d(B); §6.1d link kind
(3); §6.1d's r21 ordering clause; §10/m48 "§6.1d's r20 LINEAGE SEAMS" bullet. No code fact is
needed — the three clauses are inconsistent with each other.

**Suggested fix.** Scope the disposition sentence in both places: *"the result's labels are the §2.4
union of the value's labels and the intervening MASK-derivation links' labels, **minus** any label
eliminated by a universe/nominal PROJECTION link on the path — across a path containing a link of
kind (3) the result is that label's unvaried member and carries no labels."* Then split m48's
lineage-seam anchor's link-kind coverage explicitly: (1) → a `Varied` carrying the mask's labels;
(2) → identity; (3) → an unvaried `Array` equal to a manually projected reference. That also makes
the anchor's `reindex_to` half and the fill-side `graphed.nominal(sel)` half agree by construction.

---

## MID-3 — the (β) closure field's declared TYPE is unbound, and m48 freezes a "dummy" read-back under `mypy --strict`

**Section:** §7.2 (β) / §8.2(i) / §10 m48 (α)-anchor / DoD.

**Detail.** Two clauses give the same field two incompatible types and a third freezes a value of
neither:

1. §8.2(i) declares it **non-optional**: `variation_labels: tuple[tuple[tuple[int, int | None],
   tuple[str, ...]], ...]` — "a sorted association list … It is still a sorted tuple".
2. §7.2's r21 (β) binding attaches the hook's return value, "(the per-plan variation metadata, **or
   `None`**)", to that field.
3. §10/m48's (α) anchor freezes "a value returned from the hook — **a dummy at m48** — is carried
   onto the SHIPPED closure and is readable there (`plan.process`)".

The DoD requires `mypy --strict` **on src AND tests** (§10 closing checklist, R0.4a), and
`graphed`'s own config sets it (`graphed-latest@ff7c607 pyproject.toml:83`, `strict = true`). The
m48 frozen test supplies the hook, so mypy checks its return against the hook's declared parameter
type, which is the field's type. A `str`/sentinel dummy is a type error at the hook's return; `None`
is a type error against §8.2(i)'s non-optional declaration. This is a freeze-order trap of exactly
the class r18 removed for `to_parquet`'s m48 table entry: an m48 test-author has to invent both the
type and a value of it, and m49's bindingly-declared narrower type then reds the frozen test,
leaving only a Test Dispute or an integrity violation.

**Evidence.** §8.2(i)'s literal declaration (no `| None`); §7.2's "or `None`"; §10/m48's "a dummy";
`graphed-latest@ff7c607 pyproject.toml:83` (`strict = true`, measured by `grep -n "strict"
pyproject.toml`).

**Suggested fix.** Bind the field's declared type **once**, in §8.2(i), as
`tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...] | None` with default `None` (the shape
§7.2 already assumes), and state in m48's (α) anchor that the dummy is a **well-typed non-default
value of that type** — the empty tuple `()` is the smallest one and is distinguishable from the
`None` default, so the anchor stays discriminating without inventing a type.

---

## MID-4 — §6.4a's per-LEVEL `select=` and the level-≥1 structural check assume ONE nesting structure; the record shape m51's own round-trip anchor needs is heterogeneous

**Section:** §6.4a (per-level channel, levels ≥ 1 check) / §6.4b / §6.4d / §10 m51 round-trip anchor.

**Detail.** §6.4a binds `select=` as "an ordered per-depth mapping `{0: event_mask, 1: jet_mask, …}`
of `Varied` masks, one per level that varies", and binds the level-≥1 predicate structurally:

> **Levels ≥ 1** — lineage is not the available handle, so the check is STRUCTURAL: each per-label
> member of the mask must carry **the record's own offsets at that depth**.

"The record's own offsets at that depth" is single-valued only for a record whose fields are all
jagged with the *same* offsets — e.g. `events.Jet`. It is not single-valued for either of the two
record shapes this section itself puts in scope:

- **A record with fields of different DEPTH.** §6.4b binds `graphed.weight(ctx)` as a storable
  varied field ("their varied factors, when among the stored fields, augment like any other varied
  field"), and §6.4b's r18 precondition makes it storable exactly when it lives in the record's own
  row space. A per-event weight factor is a **depth-0** field; the object-migration case that the
  *same* m51 anchor requires needs a **depth-1** field. m51's round-trip anchor lists both as
  coverage of "an augmented skim": "covering a shift with object-level migration (per-label inner
  masks, §6.4d, written through the per-LEVEL `select={0: event_mask, 1: jet_mask}` channel), **a
  weight-only label whose stored factor is in the RECORD's own row space** — `graphed.weight(c)` …".
  A record carrying both has no unique depth-1 offsets.
- **A record with two different jagged collections.** The canonical skim (`Jet` + `Muon`, JES
  shifting only `Jet`) has two distinct depth-1 offset arrays. `select={0: evt, 1: jet_mask}` is
  well-formed under §6.4a's grammar and undecidable under its own check.

§6.4d's "widest common structure" phrase does not resolve it — it is about *where* varied columns
are stored, not about which field a level-k mask is validated and stored against. §6.4c's XOR-delta
requirement is per-column and unaffected, so this is a spec gap rather than a correctness hazard:
the writer either picks a field arbitrarily (silently validating a jet mask against muon offsets) or
crashes with an offsets message about the wrong field — the diagnosis-quality failure §6.4b's own
r18 clause was added to avoid.

**Evidence.** §6.4a "one per level that varies" and the levels-≥1 clause; §6.4b's r18 row-space
precondition; §10/m51's round-trip anchor bullet. Structural, not code-dependent. (Cross-checked
that the write path can express both: `graphed-latest@ff7c607 python/graphed/awkward/io.py:206-232`
— `to_parquet` takes an arbitrary `array` and calls `compile_ir(session, array)` at `:232`, with no
uniformity requirement.)

**Suggested fix.** Make the level channel **field-scoped**: `select={0: event_mask, ("Jet", 1):
jet_mask}` — or, minimally, bind that a level-k ≥ 1 mask names the field path it applies to, and
restate the structural check as *"the mask's per-label offsets equal **that named field's** offsets
at depth k, and the packed per-label mask is stored against that field"*. Add one sentence to §6.4d
saying that fields shallower than a supplied level are unaffected by it. m51's round-trip anchor
should then either use one heterogeneous record with the field-scoped spelling, or say explicitly
that the four coverage items may be separate fixtures.

---

## LOW-1 — no record-time DEPTH check for levels ≥ 1, the exact asymmetry r21's (2c) closed at level 0

**Section:** §6.4a (2c) / levels ≥ 1.

**Detail.** r21 added (2c) on a sound argument: depth is a FORM property known at record time, and a
wrong-depth level-0 mask passes both (2a) and (2b) and is then applied as the level-0 OR, silently
filtering objects instead of rows. The mirror case at level ≥ 1 is unhandled: a **flat** mask
supplied at level 1 (`select={0: evt, 1: evt}` — an easy mis-spelling) has no depth-1 offsets at
all, so the bound structural check ("each per-label member of the mask must carry the record's own
offsets at that depth") has no operand. The most likely implementation dies with an
`AttributeError`/`IndexError` inside `_WritePart` per partition, not with a `graphed` error naming
the level — and it dies at execution when the fault is a record-time form property, which is the
argument (2c) itself makes.

**Evidence.** §6.4a (2c) and the levels-≥1 clause; the record-time availability of the form is real —
`graphed-latest@ff7c607 python/graphed/array.py:283-290` (`_form_meta` reads
`self._session.form(self)`), so depth is decidable at the `to_parquet` call.

**Suggested fix.** Generalise (2c): *"a mask supplied at level k MUST have depth k over the record's
structure (over the named field, per MID-4); a depth mismatch at ANY supplied level is refused at
the `to_parquet` call, naming the level."* One sentence, and it makes the level-≥1 structural check
total. Add the too-shallow level-1 mask to m51's (2c) negative control.

---

## LOW-2 — an AXIS-MODE output that no variation reaches has two defensible slot key forms

**Section:** §6.1a (r19 scoping) vs §6.1c (axis-mode slot).

**Detail.** §6.1a r19 binds, without qualification on mode: "an output **NO variation reaches** keeps
today's BARE `output_name` key." §6.1c binds, without qualification on varied-ness: "an axis-mode
output contributes **exactly ONE slot, keyed `(output, None)`**, gathering ALL that output's
fill-node indices, and its per-slot value is the bare histogram."

An axis-mode histogram whose fills carry no variations is expressible — §6.2's opt-in is a property
of the histogram fixed at its first fill, and §6.2(i) declares the axis "from the §6.1d inferred
label set", which is `{"nominal"}` in that program. The two clauses then give that output different
plan-value keys. The user-facing result happens to be identical under both readings (a bare
histogram either way, `graphed.labels` duck-typing on `.axes`), so nothing miscomputes — but m48/m50
freeze the plan value's slot-keyed shape directly (§10/m48's §6.1a anchor: "the executed plan's
value is the flat `{(output, label) → bh.Histogram}` mapping"), so a test-author's pick is frozen
read-only for the wrong reason.

**Evidence.** §6.1a r19 and §6.1c's axis-mode slot paragraph, read together; §6.2(i)/(ii)'s
frontend-declares-always rule makes the 1-bin case reachable.

**Suggested fix.** One clause in §6.1c: *"an axis-mode output is keyed `(output, None)` **whatever
its label count** — the mode, not the variation count, decides; §6.1a's bare-key scoping is scoped
to SIBLING-mode outputs"*, and mirror the scoping word into §6.1a's r19 sentence.

---

## LOW-3 — §1.1's cap: r21's "compared quantity is the RENDERED CANONICAL LENGTH" is defined only for integer-valued inputs, and the frozen negative-boundary message names a magnitude that is legal

**Section:** §1.1 (r18/r19/r21 magnitude + cap clauses) / §10 m48 grammar anchor.

**Detail.** Two residues of r21's otherwise-correct `+1`-for-`m` fix:

**(a) Fractional canonical forms have a different length formula.** r21 binds "the quantity compared
against the cap is the RENDERED CANONICAL LENGTH — that digit count PLUS 1 when the value is
NEGATIVE", where "that digit count" is r19's normalized count `(mantissa digits) + (adjusted
exponent)`. For a fractional value the adjusted exponent is negative by construction and the count
is *smaller* than the mantissa, while the rendered form is `m?<mantissa>em<exp>` whose length is
`len(mantissa) + 2 + len(exp)` (+1 if negative). Worked example: `"1.234…e-5"` with a 31-digit
mantissa has normalized count `31 − 35 = −4`, passes the magnitude test comfortably, and renders as
35 characters — refused by the *generic* 32-character rule. So the two bounds still disagree in the
fractional direction, and which of the two refusal messages applies is unstated. (No m48 anchor
covers a long fractional tag, and no real σ-scan reaches it, hence LOW.)

**(b) The frozen negative-boundary message is inaccurate.** m48's grammar anchor now freezes:
`"-1.5e31"` is "REJECTED with the SAME **magnitude** message" as `"1.5e32"`. But `-1.5e31`'s
magnitude is exactly `1.5e31`'s, which the adjacent anchor freezes as **ACCEPTED**. The user is told
the magnitude is too large for a magnitude the same anchor certifies as legal; the real cause is the
one-character sign marker. The plan's own standard elsewhere is that a diagnostic must not blame the
wrong property (§6.1d's loose-value message split, §6.4b's row-space-not-offsets message).

**Evidence.** §1.1's r18/r19/r21 clauses read together; §10/m48's grammar-anchor bullet
("`"-1.5e31"` is REJECTED with the SAME magnitude message, r21"). Arithmetic verified by hand
against §1.1's own worked pair (`"1.5e31"` → `15` + 30 zeros = 32 digits; `"1.5e32"` → 33).

**Suggested fix.** State the compared quantity as the **rendered canonical length under BOTH
renderings** — `sign + digits` for an integer-valued input, `sign + mantissa + "em" + exponent` for a
fractional one — and split the two refusals by *cause* rather than by form: a **magnitude** message
when the integer digit count alone exceeds the cap, and a **canonical-tag-length** message in every
other over-cap case (which then correctly covers `-1.5e31` and the long-mantissa fractional case).
m48's anchor changes only in which message class `-1.5e31` freezes; the accepted/rejected verdicts
and the discriminating `"1.5e31"` positive are untouched.

---

## LOW-4 — §1.2's §6.2 carve-out does not cover §6.2 r15's per-fill variation PAYLOAD

**Section:** §1.2 (carve-out) / §6.2 (r15 carrier).

**Detail.** §1.2 keeps labels out of `NodeKey` params/tokens/content hashes, with one carve-out:
"in variation-axis fill mode the labels become *output content* — **StrCategory bin identities in the
histogram spec** — and there they DO enter the spec/params/content hash, by design."

§6.2's r15 carrier puts a *second*, differently-shaped label payload into node identity: "the
per-fill variation payload (the scalar label for a shift sibling; the ordered weight-label tuple for
the loop) is a **field of the fill's `FillEvaluator` AND enters the External payload's content
hash** — `content_hash((spec, variation_payload))` in axis mode". That payload is deliberately *not*
in the spec (§6.2 says so: "§1.2's §6.2 carve-out does not close it — it puts the BIN IDENTITIES in
the spec, which is exactly the part identical across siblings"), so §1.2's carve-out, read literally,
forbids the very mechanism §6.2 binds. Nothing reds inside m48–m51 (m48's §1.2 anchor is
sibling-mode-scoped by r13), but an m50 integrity reviewer working from §1.2 has a defensible
objection to the m50 implementation.

**Evidence.** §1.2's carve-out sentence; §6.2's r15 carrier paragraph, which explicitly notes the
carve-out does not reach it.

**Suggested fix.** Widen §1.2's carve-out to name both channels: "…the histogram spec **and, per
§6.2's r15 carrier, the per-fill variation payload in the External payload's content hash**".
Cross-reference from §6.2 as §6.1c already cross-references §6.2.

---

## LOW-5 — §6.1c's per-slot spec is singular, but an axis-mode slot gathers several fill nodes

**Section:** §6.1c (per-slot spec; axis-mode slot).

**Detail.** §6.1c binds "the slot spec is the spec baked into **that fill node's** params" — written
for the sibling shape, where a slot maps to one fill node. The axis-mode slot introduced in the same
section gathers "ALL that output's fill-node indices" (`1 + |S|` nodes). Which node's spec is the
slot's is unstated. In practice they agree — §6.2(i)'s cross-fill agreement rule forces one inferred
label set, hence one variation axis, hence one spec per axis-mode histogram — but the reader has to
derive that, and `_GroupZero` consumes the spec per slot (verified: `graphed-histogram@211cbbe
src/graphed_histogram/boost.py:100-117,127-130`, `layout` element 3 fed to `zero_of`).

**Suggested fix.** One clause: "for an axis-mode slot the spec is that of any of the gathered fill
nodes — §6.2(i)'s cross-fill agreement rule makes them identical, and an implementation MAY assert
it."

---

## LOW-6 — §6.1b is an m48 target whose only frozen anchor is m49's, with no note

**Section:** §10 m48 target line / §10 m49 anchor list / §6.1b.

**Detail.** m48's target line reads "§6.1 (incl. §6.1d ambient fills) **except** §6.1c's AXIS-MODE
slot, which is m50's" — so §6.1b (the `1 + |S| + |W|` structural fill-node arity) is an m48 target.
Its frozen anchor is m49's ("§2.4/§6.1b structural no-cross-product count — in SIBLING mode"). Every
other cross-milestone split in §10 is annotated explicitly (§3.4 → m49, §2.5's diagnostic → m49,
§6.1c's axis slot → m50, `to_parquet` → m51); this one is not, and §10 is described as "the
acceptance skeleton the test-author starts from". A reviewer checking "targets exactly as specified"
gets two answers, the same defect r19 fixed for §2.5's diagnostic on this very line.

No coverage gap results — §6.1b describes a property of the sibling lowering that m48's matrix and
§6.1a anchors exercise, and §6.1b's own r20 clause concedes the `S`/`W` split is unwitnessable
before m50 — so this is a bookkeeping inconsistency, not a DoD risk.

**Suggested fix.** Add "(§6.1b's arity anchor is m49's; m48 has weight labels only, so `|S| = 0`)"
to m48's target line, matching the annotation style already used three times on that line.

---

## Verdict

**Clean-with-findings.** No BLOCKER and no HIGH. The specification is coherent and implementable as
a whole; the four MIDs are localized propagation failures from r21's two structural changes plus one
genuine model gap in §6.4's per-level channel, and every one has a one-to-three-sentence fix that
touches no owner-locked decision. I would expect a further round to be short.

Recommendation: fix MID-1 through MID-4 and LOW-1 (which is MID-4's other half) in r22; LOW-2
through LOW-6 are one-sentence edits that can ride the same revision. Given that MID-2 and MID-3
both bear directly on anchors §10 already spells out, the r22 revision should re-check that m48's
`graphed`-side anchor list still names one frozen assertion per binding clause it touches.
