# systematics-vary-plan — revision r23 notes (review round 14, r22 reviews)

Audit trail for the r22 → r23 revision of `systematics-vary-plan.md`. Input: three independent
lens reviews of r22 (`systematics-vary-plan-review-r22-{facts,design,tests}.md`), 21 findings after
NIT exclusion, **19 unique** after merging two cross-lens duplicate pairs.

Verification roots used (fresh clones at the revisions the plan pins):
`/private/tmp/claude-501/graphed-latest` (`ff7c607`), `.../graphed-histogram-latest` (`211cbbe`),
`.../graphed-exec-check` (`201ea42`), `.../uproot5-graphed` (`393ecef`, branch `graphed-mvp`).
Every finding was re-verified in this session before acting; probes are named below.

**Outcome: 19 APPLIED, 0 REJECTED, 0 DEFERRED.** No finding's resolution required reversing an
owner-locked decision (naming, functional surface, e-form encoding, context attachment, record-time
expansion, scope, the Phase-2 pull-in), so no `OPEN ITEMS (owner)` block was needed.

Merged duplicates:
- facts LOW "`mypy --strict on src AND tests` cited to a line that does not establish it" +
  tests MID "The DoD's mypy-strict is unconfigured in every target repo" → one item (M-1 below).
- design MID "r22's m48/m49 milestone correction is incompletely propagated" + tests LOW
  "§8.2(i)'s closure field appears on no target line" → one item (M-2 below).

---

## HIGH

### H-1 — Context handle IDENTITY is never defined (design)

**Verdict: APPLIED.**

Verified: `grep -n "same object|object identity|memoi|canonical context" systematics-vary-plan.md`
returns only `:195` (prose about r5's mutable registry) and a WITHDRAWN r17 rule about MASK identity
in the revision history — no context-identity rule anywhere. The three consumers are real and were
read: universe/nominal return "a CHILD" context (§2.2), divergent handles are an error at the op
(§2.3e), `unify_contexts` raises on divergent handles (§6.1d(A)), and §6.4a(2a) is a literal
`is` comparison. Under a fresh-object-per-call implementation two reads of one universe are
SIBLINGS, so the divergence rule fires on `h.fill(graphed.nominal(sel).MET.pt,
graphed.nominal(sel).Jet.pt)` and on `sel1 = events[mask]; sel2 = events[mask]`.

**Edit:** §2.6b gains a binding paragraph — PURE DERIVATIONS ARE CANONICAL: `graphed.nominal(c)`,
`graphed.universe(c, L)` and `c[mask]` for the same mask (identical per-label node ids) return the
SAME context object, memoised on the parent; `graphed.vary` always returns a fresh one (so §2.3e's
divergence rule keeps its meaning and §2.1's "always returns a NEW object" is untouched). m48's
op-level divergence anchor gains the positive control that two separate `graphed.nominal(sel)` reads
(and two `events[mask]` derivations from one mask) UNIFY rather than raising.

---

## MID

### M-1 — "mypy --strict on src AND tests" mis-cited; the (α) anchor's read-back route unpinned (facts + tests)

**Verdict: APPLIED.**

Measured this session: `graphed pyproject.toml:80-84` → `[tool.mypy]`, `python_version = "3.12"`,
`strict = true` (`:83`), **`files = ["python"]` (`:84`)** — the test tree is excluded;
`graphed-histogram pyproject.toml:70-73` → `strict = true`, `files = ["src"]`;
`graphed-executors pyproject.toml:108-111` → `strict = true`, `files = ["src"]`;
`uproot5-graphed` has **no `[tool.mypy]` section** (`grep -n "tool.mypy" pyproject.toml` → no hit).
`graphed-root-prompt.md:147-153` (R0.4a) does bind src+tests and names src-only repos as a pending
cross-cutting cleanup. `Plan.process` is declared `Callable[[Partition, WorkerResources], R]`
(`python/graphed/core/execution.py:210`); `_PartitionReduce` is a module-private frozen dataclass
(`python/graphed/aggregate.py:44-55`).

**Edit:** §7.2's r22 parenthetical now cites R0.4a as the binding source and records the measured
src-only state instead of presenting `pyproject.toml:83` as evidence for the "AND tests" half. m48's
(α) anchor gains the READ-BACK ROUTE: the dummy is read off the concrete
`graphed.aggregate._PartitionReduce` via a narrowing `isinstance`/cast, not off `plan.process`'s
declared `Callable` type — pinned rather than guessed, the §9.1 discipline. The `()` choice is
unchanged (it is well-typed against the field's DECLARED type, which is src and is checked today).

### M-2 — r22's m48/m49 milestone correction incompletely propagated (design + tests)

**Verdict: APPLIED.**

Verified in r22's text: §7.2 binds "The field therefore EXISTS from m48" and §7.3 / m50's docs anchor
were re-scoped, but (a) m48's target line runs §1, §2, §3.2, §4, §6.1, §6.3, §7.2, §9.1-partial with
no §8 at all while m49's takes `§8` wholesale; (b) m48's §7.2 schema-absence anchor still read
"m49's §8.2(i) closure field changes those by design"; (c) §7.2 still read "(β) carries its anchor at
m49", stale since r21 made m48's (α) anchor freeze the return channel.

**Edit:** m48's target line gains "plus §8.2(i)'s `variation_labels` FIELD DECLARATION ONLY
(`tuple[…, …] | None = None`, unpopulated) — accessor/keying/population stay m49"; m49's target line
excepts it; the schema-absence anchor now says "ADDED at m48 … POPULATED at m49"; §7.2 now reads
"(β)'s return CHANNEL is anchored at m48 WITH (α), its per-plan PAYLOAD at m49".

### M-3 — m48's §4.1 correctionlib `content_hash` literal does not reproduce (facts)

**Verdict: APPLIED.**

Re-measured in `graphed-latest`'s own `.venv` at `ff7c607`: `exec`'d
`tests/frozen/preserve/m9/agc.py`'s `correctionlib_json()` (only the `from graphed_corpus import
make_events` line stripped) and ran three
`record_external(s, CORRECTIONLIB_PLUGIN, corr, [njet], params={"name": "event_sf",
"systematic": syst})` calls → node ids 3/4/5, all carrying
`descriptor.content_hash = sha256:e72c0da3cb6614cfaf50cea8c93ab740e8229986024a8bad4361e9ae82f4b5cd`
and differing only in `params["systematic"]`. The hash is a pure function of the payload
(`correctionlib_content_hash` = sha256 over `b"correctionlib-contents-v1"` + canonical JSON,
`python/graphed/preserve/externals/correctionlib_external.py:14-18`), so `sha256:cae4dd4b…` is not
produced by the named fixture at this revision.

**Edit:** §10/m48's §4.1 anchor and the appendix row now name the payload
(`agc.correctionlib_json()` at its default `scale = 1.0`, `agc.py:38`) and carry the measured
`e72c0da3…`; the r22 literal is explicitly WITHDRAWN. The substantive observable (ONE shared payload
hash, `systematic` the only differing param) is unchanged — it re-verified.

### M-4 — §6.4a(2a)'s handle equality is narrower than the r16 rule it claims to subsume (design)

**Verdict: APPLIED.**

Verified against the plan's own rules: §2.3e's ORIGINATION rule (`:937-939` in r22) gives every read
performed through a context THAT context's handle, so a mask read through
`E2 = graphed.vary(E1, …)` carries `E2` while a record read through `E1` carries `E1` — different
handles, identical row spaces (§6.1d link kind (2) is IDENTITY). Bare handle equality therefore
refuses `to_parquet(E1.Jet, select=graphed.selection(E2[mask]))`, which r16 admitted; r19's "the r16
admission … becomes automatic" is false. Checked all five existing m51 controls against the repaired
predicate: each refused pair is separated by a MASK-DERIVATION or PROJECTION link, never by `vary`
alone, so all five decide identically.

**Edit:** the predicate is restated as "IS the record's handle, OR reachable from it across
`graphed.vary` IDENTITY LINKS ONLY, in either direction" (one upward walk over lineage the plan
already retains); the "becomes automatic" sentence is withdrawn; m51 gains a SIXTH control — the
`E1`/`E2` program above, ACCEPTED and round-tripping — which is the only fixture that discriminates
the two readings (the existing `vary`-derived bullet puts the `vary` link BELOW the mask derivation,
where both readings accept).

### M-5 — `unweighted=True`'s effect on the fill's LABEL SET is unbound (design)

**Verdict: APPLIED.**

Verified: §6.1d binds the label set as the union of value-borne, ambient-weight and explicit factor
labels, then binds `unweighted=True` to suppress the ambient weight AND any explicit `weight=[…]`,
and says nothing about labels. m48's anchor ("a contexted fill with registrations yields counts equal
to an unweighted eager reference") is satisfied by BOTH readings — under "labels kept" every label's
histogram equals the reference — so the result shape was the test-author's coin-flip, frozen
read-only. This is the ambiguity r21 closed one clause earlier for the projection link.

**Edit:** §6.1d binds that a suppressed weight contributes NO labels (the label set is computed over
the factors the fill actually applies), so such a fill is UNVARIED and returns a bare `hist` (§6.1a);
m48's anchor is re-worded over that shape and states it as the discriminator against the
labels-kept implementation.

### M-6 — §6.4a's "one entry per level that varies" contradicts r22's FIELD-SCOPED level keys (design)

**Verdict: APPLIED.**

Verified in r22's text: the row-rule sentence still read "an ordered per-depth mapping … one entry
per level that varies" and "one packed per-label validity mask per supplied LEVEL", while the very
next clause makes level-k ≥ 1 entries field-scoped and justifies it with a Jet+Muon record that
REQUIRES two depth-1 entries; §6.4d's own r22 sentence is already field-scoped, so the two
paragraphs disagreed.

**Edit:** "one entry per (FIELD PATH, LEVEL) that varies, level 0 keyed by the bare depth `0`" and
"one packed per-label validity mask per supplied ENTRY — stored against that entry's FIELD, level 0
against the row axis". No anchor changes needed (m51's fixtures use a single depth-1 entry either
way).

### M-7 — §1.1's family example and m48's grammar anchor use a call shape §2.1 REJECTS (design)

**Verdict: APPLIED.**

Verified: §2.1's overload (c) is the event-context target with no `is_weight`, and in it
"`variations=` is REJECTED … with an error naming `collections=`". `vary(ctx, "murf",
variations={"0.5": a})` with `ctx` an event context is therefore refused by a different rule before
the family check can run — and m48's grammar anchor froze exactly that spelling as a family-check
rejection.

**Edit:** both places re-spelled in the WEIGHT form (b) — `vary(ctx, "murf", w_nom, is_weight=True,
variations={"0.5": a})` — the overload the μR/μF family actually uses. §1.1 additionally states
where a context's per-`name` tag map lives (the ambient-weight `Varied` for weight families, the
replaced collections for shift families), so the family check has a named operand from m48, one
milestone before `graphed.variations(ctx)` exports it.

### M-8 — m51's ROOT half lands in a repo with no coverage, no type gate, a reduced CI matrix (tests)

**Verdict: APPLIED.**

Measured at `uproot5-graphed` `393ecef` (branch `graphed-mvp`): `pyproject.toml:136`
`testpaths = ["tests"]` (so a new `tests/frozen/m51` IS collected); `.github/workflows/graphed.yml`
`:7-10` triggers on `push` to `graphed-mvp` + `workflow_dispatch` only (no `pull_request`), `:26-32`
ubuntu-latest with CPython 3.11/3.12 only, `:55` `python -m pytest -vv tests -m "not xrootd"`;
`grep -c cov .github/workflows/graphed.yml` → **0**; no `[tool.mypy]` section anywhere in
`pyproject.toml`. Contrast `graphed-histogram .github/workflows/ci.yml:44`
(`pytest tests/frozen --cov=graphed_histogram --cov-branch`), read this session. §6.4f calls the ROOT
half "the larger half of m51".

**Edit:** §10's uproot paragraph gains the same per-repo gate analysis the other three repos get,
with the measurement, plus three binding m51 items: (a) a `--cov` invocation over the new ROOT-side
source with the ≥90% diff-coverage gate; (b) a `[tool.mypy]` config covering that source AND
`tests/frozen/m51`; (c) an explicit statement of the CI matrix m51's DONE is keyed on for this repo
(widen, or record the reduced matrix as accepted scope) and of the trigger. A new appendix row
carries the measurement.

---

## LOW

### L-1 — §7.3's cloudpickle digest pair is not re-runnable (facts)

**Verdict: APPLIED.** Toolchain confirmed in `graphed-latest/.venv`: cloudpickle 3.1.2, CPython
3.12.10. Probe: two importable module-level frozen dataclasses with the same field values, one
carrying an extra `variation_labels: tuple | None = None`, → sha256[:16] `fc1812a8d1150009` vs
`5de138ba2f0dfdc4` — different, as the plan claims, but neither of the cited
`8d058bf867dc6bcd`/`22a566276fd6077d`, which no stated payload determines (cloudpickle's bytes for an
importable class embed module, qualname and field names — the exact reason §7.3 withdrew
`80e8024dc8f3b77d` and r13 withdrew the §6.4e pair). **Edit:** the literals are withdrawn from §7.3
and the appendix row; the qualitative statement (adding one defaulted field changes the digest,
so the churn lands where the field is ADDED — m48) is what binds.

### L-2 — appendix `read_columns` row: two of four line attributions wrong (facts)

**Verdict: APPLIED.** Measured `grep -n` over `graphed-latest/python/graphed/projection.py`:
`def read_columns` `:109`, `conservative = False` `:123` (`:130` is `nonlocal conservative` inside
`on_op`), `conservative = True` `:140`, `for array in arrays:` `:143` with `array.session.walk(...)`
`:144`, `if conservative or not needed:` `:145` / `return None` `:146`. The body citations (§5.3,
§2.3d) are accurate and untouched. **Edit:** the appendix row corrected to `:123` and `:143-144`.

### L-3 — appendix row still attributes the one-time closure churn to m49 (facts)

**Verdict: APPLIED.** The row's rationale read "why §7.3's m49 churn is SCOPED, r17" while §7.3,
m50's docs anchor and the sibling appendix row all say m48 after r22. **Edit:** the row now reads
"why §7.3's **m48** churn is SCOPED — r17; the MILESTONE corrected in r22 and swept into this row in
r23".

### L-4 — cluster of meaning-preserving span drifts (facts)

**Verdict: APPLIED.** Measured in the verification roots:
`graphed-histogram src/graphed_histogram/boost.py` — module-level `def plan(` `:256`, its
`aggregate_plan` call closing `:295` (cited `:254-292`/`:255-292`/`:256-292`); `Histogram.plan`'s
`return aggregate_plan(` block `:244-253` with `_SumFills(self._spec)` `:246` and
`_ZeroHist(self._spec)` `:248` (cited `:245-255`); `_GroupReduce` class `:101-117`, `__call__`
`:108-117` with its `-> dict[str, bh.Histogram]` on `:108` (cited `:101-118`).
`graphed python/graphed/numpy/io.py` — the numpy-idiom `def to_parquet` `:182` (signature
`:182-191`), the 1-D cap inside `_WritePart.__call__` at `:164-165` (cited `:158-173`).
`graphed pyproject.toml` — `pythonpath = [` `:115`, `"tests/_corpus"` `:117`, list closes `:127`
(cited `:114-127`). `graphed-executors .github/workflows/ci.yml` — `:44` and `:67` run the whole
frozen tree, `:101` runs only `tests/frozen/m42 … m45` and `:153` only m46/m47 (cited as three
whole-tree runs). **Edit:** all six corrected in PART II / §10 / the appendix (revision-history
entries are left as the historical record of what earlier revisions said).

### L-5 — `reindex_to`'s label rule is order-insensitive while §6.1d composes in lineage ORDER (design)

**Verdict: APPLIED.** Verified: §6.1d binds "Links compose in lineage order, parent-to-child" and a
projection link annihilates the accumulated labels while mask-derivation links BELOW it re-introduce
them; r22's set expression ("the §2.4 union … MINUS every label a projection link eliminates")
coincides for a single link but diverges once links compose (a shared label name across two masks;
a projection below the last mask), and m48's lineage-seam anchor is split PER SINGLE LINK KIND, so no
frozen test would catch it. **Edit:** both statements (§2.3d and §6.1d(B)) restated as sequential
composition — a mask-derivation link UNIONS per §2.4, a `vary` link is the IDENTITY, a
universe/nominal projection link RESETS the label set to empty.

### L-6 — m48's "m48 has weight labels only, so |S| = 0" is false of m48's own anchors (design)

**Verdict: APPLIED.** Verified against §6.1b r19's definition (`S` = labels borne by any AXIS value or
by a `Varied` `sample=`): m48's four-way fold-order anchor carries varied values in TWO axes plus a
varied `sample=`; §2.3b's anchor has `plain_array[varied_mask]` returning a `Varied` filled
downstream; §6.1d's link-kind-(1) fixture is `h.fill(events.MET.pt, sel.MET.pt)` with
`sel = events[varied_mask]`. **Edit:** the placement (arity anchor → m49) is unchanged; the
justification is replaced by the true one (m48's `W` rides the corpus weight matrix, a COUNTED
`1 + |S| + |W|` assertion needs the shift path; m48's varied-axis/varied-`sample=` programs are
anchored for fold order and result shape, not arity) and the false claim is explicitly withdrawn.

### L-7 — §2.2 defines its verbs over two input shapes while §6.1a/§6.2(i-bis) bind four (design)

**Verdict: APPLIED.** Verified: §2.2 says "each accepting a `Varied` OR an event context"; §6.1a
requires the same verbs to narrow a bare `bh.Histogram` and a `{label: hist}` mapping; §6.2(i-bis)
adds the axis-mode histogram with its own label rule and duck-typed (`.axes`) detection that must not
import `boost_histogram` into `graphed`. **Edit:** §2.2 enumerates all four shapes at the definition
site with cross-references to where each answer is bound.

### L-8 — §2.3e's slot-KIND vocabulary is a closed list owned by the frozen test (tests)

**Verdict: APPLIED.** Verified the tension: §10/m48 states the design rule "a frozen test cannot grow
arguments for a function added later" as the reason fixtures live in `src`, while r22's slot-kind
clause puts a five-kind vocabulary and one contexted `Array` per kind INSIDE the frozen test. Nothing
in m48–m51 trips it (the reviewer enumerated the 65 public gak functions; every primary in the three
enumerated classes falls inside the five kinds — consistent with the plan's own measured 65-function
count). **Edit:** the trap is RECORDED in §2.3e(2), the shape r18 used for `refusing == {gak.join}`:
the kind vocabulary is frozen at m48 and a sixth kind requires a Test Dispute.

### L-9 — r22's "an unvaried axis-mode output is still keyed (output, None)" is unanchored (tests)

**Verdict: APPLIED.** Verified: m50's mixed-mode anchor carries an axis-mode VARIED output, a
sibling-mode varied output and a third output "no variation reaches" whose asserted key is BARE
(i.e. sibling-mode), so an implementation keying an unvaried axis-mode output bare passes every
m48–m51 anchor while contradicting the rule — and the rule IS witnessable (these anchors assert the
plan value's key set). **Edit:** m50's mixed-mode anchor gains a FOURTH output — axis-mode opt-in,
no variations — asserting the `(output, None)` key and a bare histogram with a 1-bin variation axis.

### L-10 — m49's §3.4 impact-set anchor names a fixture with exactly one construction (tests)

**Verdict: APPLIED.** Verified the interning argument against `graphed src/store.rs:73-88` and the
plan's own re-measured probe (`a = src * 2.0; b = src * 2.0` → `a.node_id == b.node_id == 1`,
`session.node_count() == 2`): two labels share a node iff its input ids agree, which transitively
requires structurally identical members, so the only frontend construction is
`vary(x, "jes", up=e, down=e)` (§1.2's dedup case) and the naive fixture does not exist. It remains
adequate — a watermark implementation hands the second label an EMPTY set. **Edit:** the anchor now
states the fixture and the discriminator, the mid-freeze-discovery service m48 already gives
`gak.full_like`, `stable()` rounding, `h.axes.name` and the pt-cut jets.

---

## Bookkeeping

- Status line → **draft for review (r23)**.
- Revision history gains the r23 entry (HIGH / MID / LOW summary by section, merges named, no
  rejections, no deferrals).
- Appendix: three rows corrected (churn milestone, cloudpickle digests, correctionlib digest +
  payload, `read_columns` line attributions) and one row ADDED (the uproot5-graphed-mvp gate
  measurement).
- Only `systematics-vary-plan.md` and this notes file were modified.
