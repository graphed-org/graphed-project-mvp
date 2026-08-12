# Plan revision r22 — reviser notes (review round 13, r21 reviews)

Isolated reviser, fresh context. Source findings: `systematics-vary-plan-review-r21-{facts,design,tests}.md`
(19 findings after NIT exclusion; 18 unique after merging one cross-lens duplicate pair —
design "§7.2 (β) closure field lands at m48" ≡ tests "After r21 the §8.2(i) closure field lands at m48").
Severity spread: 0 BLOCKER, 0 HIGH, 8 MID, 10 LOW.

Verification roots used (nothing read from `/Users/lgray/vibe-coding/graphed-workdir`'s stale submodules):
`/private/tmp/claude-501/graphed-latest` @ ff7c607 (+ its own `.venv`),
`/private/tmp/claude-501/graphed-histogram-latest` @ 211cbbe (+ its `.venv`, boost_histogram 1.8.0),
`/private/tmp/claude-501/graphed-corpus-latest` @ 49650e4.
Toolchain for the pickle probe: cloudpickle 3.1.2 / CPython 3.12.10.

Outcome: **17 applied, 1 rejected (with measured counter-evidence + a clarifying edit), 0 deferred.**
No finding's resolution required reversing an owner-locked decision, so no "OPEN ITEMS (owner)" block
was opened.

---

## Applied

### 1. LOW / facts — m05 anchor carries corpus-repo line numbers on the consolidated path
**Verdict: APPLIED.**
Measured:
```
graphed-latest tests/frozen/corpus/m05/test_systematics.py
  :25 def test_kinematic_variation_changes_selection
  :33 def test_weight_variation_preserves_selection
graphed-corpus-latest tests/frozen/m05/test_systematics.py
  :26 / :34   (one blank line apart, as cba §corpus §3 records)
```
The claim's CONTENT is true on both copies; only the cited span is wrong for the consolidated path
(it opens one line inside the first test's body and closes one past the second).
**Edit:** Anchors appendix row now cites both paths explicitly with their own numbers
(`graphed …:25-37`; `graphed-corpus …:26-38`) and records the measured `def` lines and both bodies.

### 2. LOW / facts — `histograms.py:39-42` opens on a blank line and truncates `fingerprint`'s return
**Verdict: APPLIED.**
Measured (`graphed-latest tests/_corpus/graphed_corpus/histograms.py`): `STABLE_DECIMALS = 6` at `:20`;
`def bin_values` at `:35` (body `:36-37`); `def fingerprint` at `:40`, body `:41-43`, with
`return hashlib.sha256(payload).hexdigest()[:16]` at `:43` — the line that establishes the "rounds
again" claim, outside the cited `:39-42`.
**Edits:** both citations corrected to `:20,35-37,40-43` — the m48 matrix-anchor bullet in §10 and
the Anchors appendix row — each noting what the old span missed.

### 3. MID / design + MID / tests (MERGED) — the §8.2(i) closure field lands at m48, so §7.3 and m50's frozen docs anchor name the wrong milestone
**Verdict: APPLIED.**
Plan-internal chain confirmed by reading: §7.2 r21 binds (β) as the hook's RETURN channel whose value
"is attached to the shipped closure as the additive §8.2(i) field"; m48's (α) anchor freezes that a
returned dummy "is carried onto the SHIPPED closure and is readable there (`plan.process`)". Measured
(`graphed-latest python/graphed/aggregate.py:44-55`) `_PartitionReduce` has exactly
ir/source_name/backend_factory/reader/columns/externals/reduce, so a readable returned payload
requires the additive field at m48. Measured that ADDING the field is the churn, independently of its
value — same module name, class name and field names, with vs without one defaulted
`variation_labels` field:
```
without: 8d058bf867dc6bcd
with:    22a566276fd6077d      (cloudpickle 3.1.2, CPython 3.12.10)
```
**Edits:** §7.3's churn sentence re-scoped to m48 with the measurement inline and "m49 only POPULATES
the field"; §7.3's write-path sentence "the m49 scope above" → "the m48 churn scope above"; m50's
FROZEN docs anchor corrected to m48 with the reason; §7.2 gains a closing sentence "The field
therefore EXISTS from m48, which is where its one-time journal churn lands — see §7.3"; a new Anchors
appendix row carries the digest pair.

### 4. MID / design — `graphed.reindex_to`'s label rule is false across a link-kind-(3) projection, and m48 anchors both readings
**Verdict: APPLIED.**
Plan-internal, three clauses read together: §2.3d states the union unconditionally; §6.1d(B) defines
the operation as "composing link kinds (1)-(3)"; §6.1d link kind (3) yields "an unvaried value in the
ancestor's row space"; §6.1d's r21 ordering clause requires the projection to contribute NO labels
(it is what makes m48's `h.fill(graphed.nominal(sel).MET.pt, sel.MET.pt)` a BARE `hist`); m48's
lineage-seam anchor bindingly requires kinds (1)-(3) in one undivided clause.
**Edits:** the disposition is scoped in BOTH places (§2.3d and §6.1d(B)) to "the §2.4 union of the
value's labels and the intervening MASK-DERIVATION links' labels, MINUS every label eliminated by a
universe/nominal PROJECTION link on the path"; m48's lineage-seam anchor is split per link kind with
each kind's result labels asserted — (1) a `Varied` carrying the mask's labels, (2) identity,
(3) an unvaried `Array` equal to a manually projected reference, carrying no labels.

### 5. MID / design — the (β) closure field's declared TYPE is unbound and self-inconsistent; m48 freezes a "dummy" under `mypy --strict`
**Verdict: APPLIED.**
Confirmed: §8.2(i) declared the field non-optional while §7.2 r21 declared the hook's return "…or
`None`" and m48 freezes a "dummy". Measured `graphed-latest pyproject.toml:83` → `strict = true`, and
the DoD requires `mypy --strict` on src AND tests, so the m48 test's hook return is type-checked.
**Edits:** §8.2(i) declares
`variation_labels: tuple[tuple[tuple[int, int | None], tuple[str, ...]], ...] | None = None` with the
reason; §7.2 binds the type once by reference to §8.2(i) and fixes the m48 dummy as the empty tuple
`()` (well-typed, non-default, no invented type); m48's (α) anchor says so.

### 6. MID / design — §6.4a's per-LEVEL `select=` assumes ONE nesting structure
**Verdict: APPLIED.**
Confirmed plan-internally: §6.4a bound the level-≥1 predicate as "each per-label member of the mask
must carry THE RECORD'S OWN OFFSETS at that depth", which is single-valued only for a record whose
fields are all jagged with the same offsets. §6.4b makes `graphed.weight(ctx)` a storable depth-0
field and m51's round-trip anchor lists it beside the depth-1 object-migration case; a two-collection
record (Jet + Muon) has two distinct depth-1 offset arrays while `{0: evt, 1: jet_mask}` is
well-formed under the r21 grammar. §6.4d's "widest common structure" is about where varied columns are
STORED, and does not close it. Cross-checked that the write path imposes no uniformity:
`to_parquet(array, …)` takes an arbitrary array (`graphed-latest python/graphed/awkward/io.py:206-231`).
**Edits:** §6.4a binds the level-k ≥ 1 entry as FIELD-SCOPED (`{0: event_mask, ("Jet", 1): jet_mask}`)
and restates the structural check against THAT NAMED FIELD's offsets, with the packed per-label mask
stored against that field; §6.4d gains the sentence that fields shallower than a supplied level (or at
that depth under another path) are unaffected; m51's round-trip anchor states its coverage items MAY
be separate fixtures and adopts the field-scoped spelling; the m51 level-≥1 positive control spelling
updated to match.

### 7. LOW / design — no record-time DEPTH check for levels ≥ 1
**Verdict: APPLIED.**
Confirmed: r21's (2c) closes only level 0. A flat mask supplied at level 1 has no depth-1 offsets, so
the structural check has no operand and the implementation dies per partition inside `_WritePart`
rather than with a graphed error naming the level — at execution, on a record-time form property
(depth is decidable at the call: `graphed-latest python/graphed/array.py:283-290`, `_form_meta` reads
`self._session.form(self)`).
**Edits:** (2c) generalized in §6.4a to every supplied level (over the NAMED FIELD for k ≥ 1); m51's
(2c) bullet gains the too-shallow level-1 mask alongside the jagged level-0 one.

### 8. LOW / design — an AXIS-MODE output that no variation reaches has two defensible slot key forms
**Verdict: APPLIED.**
Confirmed plan-internally: §6.1a r19 ("an output NO variation reaches keeps today's BARE
`output_name` key") is unqualified on mode while §6.1c ("an axis-mode output contributes exactly ONE
slot, keyed `(output, None)`") is unqualified on varied-ness; the program is expressible, since §6.2's
opt-in is per-histogram and §6.2(ii) makes the frontend declare the axis always.
**Edits:** §6.1a's rule scoped to SIBLING-mode outputs, with the reasoning; §6.1c states the keying
holds whatever the label count — the MODE decides.

### 9. LOW / design — r21's "RENDERED CANONICAL LENGTH" is defined only for integer-valued inputs, and the negative-boundary message names a legal magnitude
**Verdict: APPLIED.**
Re-derived by hand against §1.1's own worked pair. r19's normalized count is
(mantissa digits) + (adjusted exponent); for `"1.5e31"` that is 2 + 30 = 32 = the rendered length.
For a FRACTIONAL input the adjusted exponent is negative by construction, so the count is smaller than
the mantissa (a 31-digit-mantissa fractional value: 31 − 35 = −4) while the rendered form is
`len(mantissa) + 2 + len(exp)` = 35 characters — the two bounds disagree in that direction and no
clause said which refusal applies. Separately, m48 froze `"-1.5e31"` as REJECTED with the SAME
MAGNITUDE message as `"1.5e32"`, while the adjacent half of the same anchor certifies that magnitude
as LEGAL (`"1.5e31"` ACCEPTED) — the plan's own standard elsewhere (§6.1d's loose-value message split,
§6.4b's row-space-not-offsets message) is that a diagnostic must not blame the wrong property.
**Edits:** §1.1 defines the compared quantity under BOTH renderings and splits the two refusals by
CAUSE (magnitude message only when the INTEGER digit count alone exceeds the cap; canonical-tag-LENGTH
message otherwise, covering `"-1.5e31"` and the long-mantissa fractional case); m48's grammar anchor
moves the negative twin's message CLASS accordingly. **Both verdicts are unchanged** — the negative
twin is still REJECTED, `"1.5e31"` still ACCEPTED, and the two rejections stay distinguishable, which
is what the anchor exists to freeze.

### 10. LOW / design — §1.2's §6.2 carve-out does not cover §6.2 r15's per-fill variation PAYLOAD
**Verdict: APPLIED.**
Confirmed plan-internally: §6.2 r15 binds the per-fill payload into `content_hash((spec,
variation_payload))` and says in terms that "§1.2's §6.2 carve-out does not close it", so §1.2 read
literally forbade the mechanism §6.2 binds. Nothing reds inside m48–m51 (m48's §1.2 anchor is
sibling-mode-scoped by r13), but an m50 integrity reviewer working from §1.2 had a defensible
objection.
**Edit:** §1.2's carve-out widened to name both channels, with the m48-scoping note.

### 11. LOW / design — §6.1c's per-slot spec is singular but an axis-mode slot gathers several fill nodes
**Verdict: APPLIED.**
Confirmed plan-internally; the consumer is real (`graphed-histogram-latest
src/graphed_histogram/boost.py:100-117` iterates `self.layout` per slot, `_GroupZero` at `:127-130`).
**Edit:** §6.1c adds that a sibling slot maps to one node (unambiguous) while an axis-mode slot's spec
is that of ANY gathered node — §6.2(i)'s cross-fill agreement rule forces them equal and an
implementation MAY assert it.

### 12. LOW / design — §6.1b is an m48 target whose only frozen anchor is m49's, with no note
**Verdict: APPLIED.**
Confirmed: m48's target line annotates every other cross-milestone split (§3.4 → m49, §2.5's
diagnostic → m49, §6.1c's axis slot → m50, `to_parquet` → m51) and not this one, while §10 is "the
acceptance skeleton the test-author starts from". No coverage gap results.
**Edit:** the annotation added to m48's target line, in the style already used three times there.

### 13. MID / tests — m48's four-way fold-order anchor uses a varied `sample=` with no storage pin
**Verdict: APPLIED.**
Re-measured myself in `graphed-histogram-latest`'s venv (boost_histogram 1.8.0):
```
Double        -> TypeError: Keyword(s) sample not expected
Weight        -> TypeError: Keyword(s) sample not expected
Mean          -> OK
WeightedMean  -> OK
```
and the evaluator passes `sample` straight through (`src/graphed_histogram/boost.py:60-71`,
`sample = _flat(rest.pop(0)) if self.has_sample else None; h.fill(*axes, weight=weight, sample=sample)`)
while `Histogram.fill` type-checks only `args` and `weights` (`:152-178`). So a default-storage
fixture RECORDS cleanly and dies at EVALUATION, post-freeze, against a correct implementation —
exactly what r21 fixed one milestone later for m50.
**Edit:** m48's bullet gains the same storage pin, plus the alternative escape (if the anchor is
record-time only, it must say so, so the test-author does not build a plan run around it).

### 14. MID / tests — m49's §5.3 anchor puts a CONSERVATIVE label in the union-growth fixture
**Verdict: APPLIED.**
Measured (`graphed-latest python/graphed/projection.py:109-147`): one `conservative` flag
(`:130`), set by any non-field op applied to the source (`:140`), across ALL arrays passed
(`for array in arrays: array.session.walk(...)`, `:142-143`), and
`if conservative or not needed: return None` (`:145-146`). §2.3d states the same for the varied
union. So a conservative label inside the same varied program collapses the union to `None` and the
growth half is vacuous or red.
**Edit:** m49's §5.3 bullet scopes the conservative label to a separate program (or output set) in the
same test module, with the per-label stats-verb restatement offered as the interaction-immune
alternative; §5.3's prose carries the same binding with the measured citation.

### 15. MID / tests — §6.4f's write-path optimizer-merge check is binding new source with no m51 frozen anchor
**Verdict: APPLIED.**
Confirmed by reading m51's whole anchor list (superset rows, bit-exact round-trip, `graphed.selection`
bridge, entry checks (1)/(2a)/(2b)/(2c)/level-≥1, representation, manifest determinism, manifest,
structure refusal, `to_parquet` table entry, ROOT half, docs, single-read witness): no anchor for
§6.4f's settled "it does" merge-refusal. Measured that the check is affordable where §6.4f puts it:
`to_parquet` computes `columns = _evaluation_columns(...)` at `python/graphed/awkward/io.py:230` then
`compiled = compile_ir(session, array)` at `:231`, both inside the call.
**Edits:** a new m51 anchor bullet (with the `w * 1.0` trigger, §7.2's message + workaround, and an
UNVARIED positive control); a new Anchors appendix row for the compile-at-the-call measurement.

### 16. MID / tests — §2.3e's propagation gate has no bound way to match each function's required operand KIND
**Verdict: APPLIED.**
Re-measured myself against `graphed-latest@ff7c607` with a contexted jagged-numeric `Array`
(`from_awkward(s, "events", ak.Array([[1.0, 2.0], [3.0]]))`):
```
num OK   unzip OK   drop_none OK   singletons OK   unflatten(a, num(a)) OK   firsts OK   where OK
with_field(a, num(a), "x")  RAISES GraphedTypeError:
    ill-typed op 'ak.with_field' ... no tuples or records in array
```
so one test-owned array cannot serve the enumerated classes, and r16 bars the fixture from supplying
the primary — the test-author would have to invent a convention and the wrong first guess reds the
gate for a reason unrelated to handle propagation.
**Edits:** §2.3e(2) binds that each `src` fixture slot DECLARES its operand kind (flat numeric /
jagged numeric / record / boolean mask / option) and the frozen test owns one contexted `Array` per
kind, all read through the SAME context; the measurement is carried in a new Anchors appendix row.
r16's property (the context is test-owned) and the self-repairing property (the type requirement lives
in `src` beside the classification) are both preserved.

### 17. LOW / tests — §6.4e's "MUST NOT import `awkward._connect.*`" is binding, unanchored, and unmarked
**Verdict: APPLIED.**
Confirmed: m51's manifest anchor asserts only the OUTCOME (`ak.from_parquet` round-trips the augmented
file), which an implementer who simply imports the private helper also satisfies. The plan's own
convention is to say so when a rule is knowingly unanchored (§7.2's compile-twice rule, §1.1's
`"1e1000000000"`, §2.2's vary-link-walking half).
**Edit:** §6.4e marks the rule knowingly UNANCHORED with its reason and offers the one-line
`tests/extra` static assertion, in the shape §7.2 already uses. (The alternative — a new frozen
witness — was not taken: the rule's violation is invisible to behaviour, which is precisely the
criterion this plan uses for the knowingly-unanchored treatment.)

---

## Rejected

### 18. LOW / tests — "m48's §4.1 anchor names a `systematic=` param the recorded External node does not carry"
**Verdict: REJECTED on measured counter-evidence** (with a clarifying edit that keeps the reviewer's
underlying hazard closed).

The review checked `gak.apply_correction` and is right about THAT path
(`graphed-latest python/graphed/awkward/functions.py:505-509` records
`{"name": name, "args": json.dumps(args, sort_keys=False)}` — the systematic rides inside the args
JSON). But it is not the path the anchor's own cited fixture uses. Measured r22 against
`graphed-latest@ff7c607`, using the m9 fixture's spelling
(`tests/frozen/preserve/m9/agc.py:113-115`,
`record_external(s, CORRECTIONLIB_PLUGIN, corr_bytes, [njet], params={"name": "event_sf",
"systematic": syst})` via `python/graphed/preserve/externals/_base.py:215-248`):

```
nominal params={... 'name': 'event_sf', 'systematic': 'nominal'}
up      params={... 'name': 'event_sf', 'systematic': 'up'}
down    params={... 'name': 'event_sf', 'systematic': 'down'}
all three descriptor.content_hash =
  sha256:cae4dd4b0c20d72dc81b28e8dd877841ff4d452dbc57a18007001318965ae94e
```

i.e. **all labels' External nodes share ONE `PayloadDescriptor.content_hash` and differ ONLY in the
`systematic` param** — the anchor's observable, verbatim, on the path §4.1 cites. The anchor's wording
is therefore NOT changed.

The residual hazard the review points at is real though: a test-author reaching for the gak
correctionlib verb instead would find the observable unsatisfiable. **Clarifying edit applied:** m48's
§4.1 bullet now names the recording spelling with the measured digest, and states explicitly that
`gak.apply_correction` is NOT that path — the same mid-freeze-discovery service the neighbouring
`gak.full_like` / `stable()`-rounding / pt-cut-jets notes provide. A new Anchors appendix row carries
both measurements.

---

## Deferred

None. No finding's resolution required reversing an owner-locked decision, so no "OPEN ITEMS (owner)"
block was opened in the plan header.

---

## Bookkeeping

- Status line: `draft for review (r21)` → `draft for review (r22)`.
- Revision history: new `r22 (2026-07-30)` entry summarizing applied fixes by section, the single
  rejection with its counter-evidence, and the absence of deferrals.
- Files touched: `systematics-vary-plan.md` and this notes file only.
