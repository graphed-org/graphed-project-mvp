# Plan revision r25 — reviser audit trail (review round 16, r24 reviews)

Input: 17 findings (facts / design / tests lenses, NITs excluded) on
`systematics-vary-plan.md` r24. After merging cross-lens duplicates: **13 unique**.
All 13 **CONFIRMED** against the pinned verification roots and **APPLIED**. Nothing rejected,
nothing deferred (no finding touched an owner-locked decision, so no "OPEN ITEMS (owner)" block
was needed).

Verification roots used: `/private/tmp/claude-501/graphed-latest` (ff7c607),
`/private/tmp/claude-501/graphed-histogram-latest` (211cbbe),
`/private/tmp/claude-501/graphed-corpus-latest` (49650e4). Every measurement below was re-run in
this session; nothing was carried over on the reviewers' word.

## Merged duplicate groups

- **§6.1c `.plan()` "equivalently" parenthetical** — facts MID + design HIGH + tests MID → one edit.
- **§3.4 impact-verb operand phrase** — facts LOW + design LOW + tests LOW → one edit (plus §9.1).

---

## 1. HIGH (design) / MID (facts, tests) — §6.1c's `.plan()` refusal: false equivalence

**Verdict: APPLIED.**

Measured, `graphed-histogram@211cbbe src/graphed_histogram/boost.py`:
- `:148` — `self._spec: str = spec_of(self)` in `__init__`.
- `:180-212` — every `fill()` records `params={"spec": self._spec, "n_axes": …, "weighted": …,
  "sampled": …}` (plus `n_weights` only when `len(weights) > 1`) and `chash =
  content_hash(self._spec)` — the attribute itself, not a per-fill recomputation.
- `:88-98` — `_SumFills` sums ALL staged fills; `:244-253` — `Histogram.plan` passes
  `_SumFills(self._spec)`/`_ZeroHist(self._spec)`.

So in sibling mode every staged fill's spec **equals** `self._spec` whether the fill is varied or
not; the r24 parenthetical predicate is False exactly on the arm m48 exercises, while the
disjunction's first arm is True. The plan agrees with itself elsewhere (§6.2 r24 "a SIBLING-mode
fill — varied or not — hashes exactly as today"; §1.2; §6.3's pinned params key set).

**Edits:** §6.1c — replaced the "(equivalently: …)" parenthetical with an explicit statement that
the two arms are INDEPENDENT tests (varied arm = frontend-tracked, m48; axis-mode arm = the spec
comparison, m50), carrying the measured basis and the failure it prevents. §10/m48's
`.plan()`-refusal anchor — "word the anchor over the DISJUNCTION … and NOT over the spec comparison
alone", noting a spec-only wording has no m48-constructible fixture. r24's revision-history entry —
one inline clause marking the "equivalently" half as corrected in r25.

## 2. HIGH (design) — §8.2(i)'s record→reduced accessor has no bound carrier

**Verdict: APPLIED.**

Measured, `graphed-latest@ff7c607`:
- `python/graphed/execute.py:36-52` — `CompiledGraph` fields are `ir: bytes` /
  `source_names: tuple[str, ...]`, single method `evaluate`.
- `:54-80` — `compile_ir` reduces internally (`session._store.reduce(...)[0].serialize()` /
  `_reducer.finalize(...)`), returning only bytes + names.
- `src/lib.rs:365-381` `reduce` → `(PyGraphStore, HashMap<String, usize>)`; `:387-399`
  `reduce_incremental`; `:403-415` `reduction_report` — no id mapping anywhere.
- `src/optimizer/mod.rs:88-116` — `remap` is local to DCE; only `(kept, out_idx)` escapes (`:114-115`).

So "a read-only accessor over the reduction that produced a given compiled artifact" had no operand,
and the three conceivable carriers were each unbound or foreclosed by the plan's own rules (second
reduction = §7.2's forbidden double compile; IR tag = §3.1's "no serialize tag"; second hook
parameter = contradicts m48's frozen one-argument (α) anchor at plan `:3520-3556`).

**Edit:** §8.2(i) — bound the carrier as an **additive `CompiledGraph` field** (absent/`None` at
m48, populated by `compile_ir` from the core accessor at m49), citing §2.5's existing additive-field
precedent and its schema-anchor scoping note, and stating that m48's ONE-argument hook signature
stays sufficient and must not be widened. §7.2 — one sentence tying the "`CompiledGraph`, not ids"
rationale to that carrier.

## 3. MID (design) — §6.4a's level-≥1 predicates have no operand for r24's bare depth-`k` key

**Verdict: APPLIED.** Plan-internal, verified by reading: (2c) at `:2403-2413` reads "over the NAMED
FIELD for a level-k ≥ 1 entry"; the levels-≥1 structural check at `:2414-2421` reads "that NAMED
FIELD's own offsets … stored against that field"; r24's storage sentence at `:2249-2250` and §6.4d
at `:2548-2556` were already swept for the bare key, these two were not. m51's entry-check anchors
are worded over these predicates and the canonical skim is m51's positive control.

**Edit:** both predicates now run against the RECORD'S OWN structure/offsets at depth k for a bare
depth-`k` entry (single-valued by r24's own legality condition), mask stored against that axis.

## 4. MID (design) — `graphed.numpy`'s module verbs excluded from the "EXHAUSTIVE" surface

**Verdict: APPLIED.** Measured in `graphed-latest`'s venv: the plan's own annotation-wide filter
(`inspect.isfunction`, any parameter annotation mentioning `Array`) over `graphed.numpy.__all__`
(22 names) discovers exactly six — `apply_gufunc`, `empty_like`, `full_like`, `ones_like`,
`project`, `zeros_like` (`python/graphed/numpy/creation.py:77-91`, `projection.py:40`,
`gufunc.py:74-90`; each reaches `array.session` / `arrays[0].session`). §2.3d discovered only over
`graphed.__all__`, so a numpy-idiom `Varied` (bound first-class in r24 §2.2) handed to the numpy
twin of §4.1's binding `gak.full_like` reached no bound behaviour.

**Edit:** §2.3d — dispositions bound by analogy with the idiom twins (`*_like` + `apply_gufunc`
*broadcast*; `project` *expands*, incl. `read_columns`' conservative-`None` union rule), and the m48
gate runs the identical dynamic enumeration over `graphed.numpy.__all__` (same repo, same anchor,
same containment floor).

## 5. MID (design) — §6.1d's unification/divergence enumeration omits `sample=`

**Verdict: APPLIED.** Measured, `graphed-histogram@211cbbe boost.py:160-178`: `fill` type-checks
`args` (`isinstance(a, Array)`) and `weights` ("weights must be graphed Arrays") and then
`if sample is not None: inputs.append(sample)` — no check at all. The plan makes `sample=`
first-class elsewhere (§6.1d r15 fold order, §6.1b r19 `S` membership, m48's four-way fold anchor),
but the binding sentence enumerated only three operands.

**Edit:** `sample=` added to the binding unification/divergence enumeration, with the measured basis
and a note that an ancestor-context `sample=` re-indexes like any other ancestor VALUE while the
broadcast seam stays deliberately scoped to weight factors.

## 6. MID (tests) — m48's §2.1 stacking anchor does not require a NESTED factor

**Verdict: APPLIED.** Corpus semantics re-measured at `graphed-corpus@49650e4
src/graphed_corpus/analyses/systematics.py`: `jets = _apply_jes(events.Jet, …)` `:60`,
`good = jets[jets.pt > 25]` `:61`, `sel_jets = good[sel]` `:74`, `weight = _btag_weight(sel_jets,
variation=variation)` `:76`, where `_btag_weight` returns the CENTRAL per-event SF unless the
variation is `btag_up`/`btag_down` (`:25-36`). Under §2.6's context idiom the registered factor's
members are therefore themselves `Varied` — the nested shape §2.1 r24 governs — while the r11 anchor
text is satisfiable by a flat factor, for which one-level and two-level readings agree.

**Edit:** §10/m48's stacking bullet now requires the nested factor (corpus spelling given), asserts
`graphed.weight(sel2)[jes_up] == old_ambient[jes_up] × factor[jes_up]["jes_up"]` and names the
one-level answer as the discriminated-against wrong result; no fill needed, so the anchor stays in
`graphed`'s half.

## 7. MID (tests) — m51 anchors neither half of r24's bare depth-`k` rule

**Verdict: APPLIED.** Read in full: the round-trip bullet (`:4482-4506`) pins the level-≥1 coverage
item to the multi-field record + field-scoped channel and mentions the bare key only descriptively,
while r22 made the coverage items separable; the entry-check bullet (`:4544-4590`) enumerates (1),
(2a) + both absent-operand cases + the fifth positive, (2c) at level 0 and its level-≥1 mirror,
(2b), the level-≥1 structural check and §6.4b's row-space refusal — no ambiguity-refusal entry.

**Edit:** §10/m51 — at least one round-trip coverage item MUST be the bare-key skim
`to_parquet(events.Jet, select={0: event_mask, 1: jet_mask})`; plus a new entry-check line for the
`{Jet, Muon}`-record bare-`1` refusal with the `("Jet", 1)` spelling as positive control.

## 8. MID (tests) — §6.4e's manifest levels field unanchored; "lists exactly" is a freeze hazard

**Verdict: APPLIED.** §6.4c r24 (`:2512-2521`) itself notes "m51's round-trip anchor supplies both
levels, so nothing in the frozen suite changes" — i.e. the levels entry is unobservable there; the
manifest anchor's "lists exactly the appended labels/columns/representations" is the exact-content
wording this plan already repaired for §6.3's params key set (r17), §7.2's schema key sets (r19) and
§2.3d's floors (r18), and would red the moment the required levels entry appears.

**Edit:** the m51 manifest anchor now asserts a literally spelled expected KEY SET that includes the
levels entry, plus one assertion that its value equals the levels the fixture supplied through
`select=` (both levels / `{0}`).

## 9. LOW ×3 — §3.4 / §9.1 operand phrase names two incompatible shapes

**Verdict: APPLIED.** Measured: `read_columns(arrays: Sequence[Array], source_nid: int) ->
tuple[str, ...] | None` (`python/graphed/projection.py:109`); `Session.walk(self, array, *, source,
op, external)` (`python/graphed/session.py:245-252`) — no source operand; §2.2's `graphed.labels(x)`
takes a single object. A reachability difference is source-agnostic, so `source_nid` has no role
(§5.3's stats verb legitimately keeps it — it CALLS `read_columns` per label).

**Edit:** §3.4 and §9.1 both now name one shape — the per-label output Arrays, the `Sequence[Array]`
half of `read_columns`' operands, WITHOUT `source_nid`.

## 10. LOW (design) — m49's target line takes §7 wholesale

**Verdict: APPLIED.** m48's line binds §7.2 to m48 ("§7.1/§7.3/§7.4 stay m49"); m49's read
"§3.3, §3.4 …, §5, §7, §8 — EXCEPT …". **Edit:** m49's line now reads "§7 — EXCEPT §7.2, which
lands at m48", mirroring the §8 treatment r23 added.

## 11. LOW (facts) — "two m48 anchors carry a non-empty `S`" undercounts

**Verdict: APPLIED.** `S` is defined at `:1672-1676` as labels borne by any AXIS value or a `Varied`
`sample=`; the §2.6/§6.1d ambient-fill bullet (`:3847-3851`) freezes "Jet-pT fill yields value
labels ∪ ambient labels", whose value-labels term must be non-empty for the union assertion to
discriminate. **Edit:** "at least two", with the ambient-fill bullet named as a third.

## 12. LOW (tests) — §4.3's "a frozen test cannot import an internal" is contradicted in-document

**Verdict: APPLIED.** m48's (α) anchor bindingly reads `graphed.aggregate._PartitionReduce`
(a module-private frozen dataclass, `python/graphed/aggregate.py:44-55`), and the house pattern the
plan cites is `s._store.nodes()` in `graphed-histogram
tests/frozen/m29/test_multi_weight_fills.py:84` (verified: that line reads
`node = next(n for n in s._store.nodes() if n["id"] == h.fill_nodes()[0].node_id)`).
**Edit:** §4.3's sentence scoped — private access is tolerated where an anchor PINS the route; what
is unreachable is a label correspondence that exists nowhere.

## 13. LOW (tests) — §2.2's `type(x)` pairing undefined for a `Varied` target; §6.1a's
`graphed.nominal` unanchored at m48

**Verdict: both APPLIED** (two one-line edits).
- §2.1(a) admits an `Array | Varied` target (`:433-434`), for which `type(x)` IS the container class.
  Probed in `graphed-latest`'s venv: `dir(graphed.Array)` public = 6 names, `dir(NumpyArray)` = 32 —
  the idiom split is load-bearing. **Edit:** pairing is with `type(x)` for an `Array` and
  `type(graphed.nominal(x))` when `x` is already a `Varied`.
- §2.2 r24 binds `graphed.nominal` on both result shapes; only the axis-mode answer was anchored
  (m50 (i-bis), `:4394-4396`), while m48's §6.1a anchor named only `universe`/`labels`. **Edit:**
  `graphed.nominal` added to that anchor's uniform-narrowing assertion, naming the
  "return the argument unchanged" implementation it discriminates against.

---

## Rejected / deferred

None. No finding's resolution required reversing an owner-locked decision (naming, functional
surface, e-form tags, event-context attachment, record-time expansion, m48–m51 scope, the Phase-2
pull-in), so no "OPEN ITEMS (owner)" block was added.

## Files touched

- `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-plan.md` (status → r25, 16 edits,
  r25 revision-history entry)
- `/Users/lgray/vibe-coding/graphed-workdir/systematics-vary-plan-revision-r25-notes.md` (this file)
