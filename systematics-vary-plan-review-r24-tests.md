# systematics-vary-plan — review round 16, lens: TEST ARCHITECTURE

- **Plan revision reviewed:** r24 (`systematics-vary-plan.md`, 5842 lines, read in full — Part I, §§1–12, §10 anchors, Anchors appendix, revision history).
- **Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), no wall-clock/size in frozen tests (R0.10a), determinism-gate compatibility, freeze-order hazards, traceability requirement↔anchor, buildability of the fixtures as stated.
- **Date:** 2026-07-30.
- **Verification roots used (fresh clones at the pinned revisions; the stale submodules under `/Users/lgray/vibe-coding/graphed-workdir` were NOT used for any code fact):**
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (confirmed in-session via `git log --oneline -1`), including its own `.venv` for runtime probes.
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (confirmed in-session).
  - `/private/tmp/claude-501/graphed-corpus-latest` @ `49650e4` (confirmed in-session).
- **Owner-locked decisions were not relitigated.** No finding below asks for a different naming, encoding, surface shape, architecture, or scope choice; every one is an internal-consistency or coverage defect in how the plan *specifies* a decision it has already made.

Findings are ordered by severity. Four MID, four LOW, no BLOCKER and no HIGH.

---

## MID-1 — §6.1c's `.plan()` "equivalently" parenthetical is FALSE for the arm m48 freezes

**Section:** §6.1c (plan line 1707-1709), repeated in the r24 revision-history entry (line 4864-4866); consumed by §10/m48's `.plan()`-refusal anchor (line 3478-3494), which instructs the test-author to "word the anchor over the predicate".

**Detail.** r24 re-keys the refusal on the MODE and states the trigger twice:

> `.plan()` raises — pointing at the group API — on a `Histogram` that is VARIED *or* in §6.2 AXIS MODE (equivalently: whose staged fill nodes' spec differs from the `__init__`-time `self._spec`).

The two spellings are not equivalent, and they diverge precisely on the arm m48 exercises. In sibling mode — the default and the only mode that exists at m48 — a varied histogram's fill nodes carry the `__init__`-time spec **verbatim**:

- `graphed-histogram@211cbbe src/graphed_histogram/boost.py:148` — `self._spec: str = spec_of(self)` in `__init__`;
- `:180-212` — every `fill()` records `params={"spec": self._spec, "n_axes": …, "weighted": …, "sampled": …}` and `chash = content_hash(self._spec)` (read in-session; the `spec` value is literally the attribute, not a per-fill recomputation);
- §1.2 keeps labels out of `params`/content hashes in sibling mode, and §6.2's own r24 sentence says it in terms: "a **SIBLING-mode fill — varied or not — hashes exactly as today**".

So for a varied sibling-mode `Histogram`, `staged fill spec == self._spec` for every fill, and the parenthetical predicate is `False` while the binding disjunction is `True`. An implementer who codes the parenthetical (it reads as the cheap, mode-agnostic implementation, and it is offered as an equivalence) ships a `.plan()` that does **not** refuse a varied histogram — red against m48's own frozen refusal anchor, discovered only after the freeze. A test-author who takes §10's instruction literally ("word the anchor over the predicate") and writes the parenthetical form has no m48-constructible fixture at all: nothing at m48 makes a fill's spec differ from `self._spec`.

**Evidence.** `boost.py:144-150` and `:180-212` read at `211cbbe` (quoted above); plan §6.2 line 2051-2056 (sibling-mode hashing exemption); plan §6.3 line 2174-2177 (the unvaried fill's params key set is `{"spec","n_axes","weighted","sampled"}`, i.e. the spec is the *same* object, not a per-label one).

**Suggested fix.** Scope the parenthetical to the mode it is true of, or delete it: "…VARIED *or* in §6.2 AXIS MODE (in axis mode this is equivalently: whose staged fill nodes' spec differs from the `__init__`-time `self._spec`; in sibling mode the specs agree by §1.2, so the trigger there is the presence of variations)". Mirror the correction in the r24 revision-history entry and in §10/m48's bullet so "word the anchor over the predicate" cannot be read onto the spec test.

---

## MID-2 — §2.1's new TWO-LEVEL factor resolution is unwitnessed: m48's stacking anchor does not require a NESTED factor

**Section:** §2.1 stacking, r24 (lines 486-501); anchor = §10/m48 "§2.1 stacking" bullet (lines 3495-3519).

**Detail.** r24 binds a genuinely new semantic layer:

> **`factor[L]` means §2.4 applied TWICE when the factor NESTS, r24** … take the container's member for L (its `"nominal"` member when L is new to the container), then, if THAT member is itself `Varied`, take its own L …

and argues correctly that the one-level reading "is silently wrong exactly where the corpus is" (it would b-tag-weight `jes_up` with the SF computed on *nominal* jets and miss `ttbar_4j1b_jes_up`).

The only anchor is m48's stacking bullet, which requires "a WEIGHT `vary` on a context already carrying SHIFT labels" and asserts the inherited label's ambient member is `old_ambient[L] × factor[L]`. **That is satisfiable with a flat (non-nested) factor**, in which case the two-level branch is never exercised. Concretely: register the weight on a context whose collections were shift-varied but which is *not* mask-derived, using a factor read from an unvaried collection — e.g. `events2 = graphed.vary(events, "jes", Jet={…})` then `graphed.vary(events2, "pu", pu_sf(events2.MET.pt), is_weight=True, up=…, down=…)`. `events2.MET.pt` is a plain `Array` (only `Jet` was replaced), so the registered container's members are plain `Array`s, `factor[jes_up]` falls back to the factor's central universe at level one, and a one-level implementation is green.

The plan itself already identified this hazard class one layer up: the r11 extension of this very anchor exists because "m48's weight-only matrix cannot reach [the shift-stacking case], so a wrong reading survives m48 and only detonates against m49's 15-reference matrix, after m48 is frozen". r24 adds a *deeper* layer with the identical exposure and did not extend the anchor.

**Evidence.** Corpus semantics re-measured at `graphed-corpus-latest@49650e4`, `src/graphed_corpus/analyses/systematics.py`: `jets = _apply_jes(events.Jet, …)` → `good = jets[jets.pt > 25]` → `sel_jets = good[sel]` → `weight = _btag_weight(sel_jets, variation=variation)`, with `_btag_weight` returning the CENTRAL per-jet SF product (`ak.prod(central, axis=1)`) unless `variation` is `btag_up`/`btag_down` (`:25-36`). Under the §2.6 sketch's spelling (`sjets = sel.Jet[sel.Jet.pt > 25]`, a `Varied` over the jes labels), `btag_sf(sjets)` is a `Varied`, so the registered container's members are themselves `Varied` — the nested shape. §2.2's r24 sentence confirms the intended flatness of the *result* ("the AMBIENT weight `graphed.weight(ctx)` returns is always flat"), which is the property the assertion must pin.

Buildability of the fix is not in doubt: the nested fixture needs no fill (the anchor is explicitly frontend-observable through `graphed.weight(ctx)` and stays in `graphed`'s half), and §2.1(b)'s row-space rule is satisfied by construction because the factor is read through the target context.

**Suggested fix.** In §10/m48's stacking bullet, require the registered factor to be **nested**: its members must themselves be `Varied` over the inherited shift labels (the corpus spelling `btag_sf(sel.Jet[sel.Jet.pt > 25])` on a `Varied`-mask-derived `sel`), and assert `graphed.weight(sel)[jes_up]` equals `old_ambient[jes_up] × factor[jes_up]["jes_up"]` — i.e. the SF evaluated on the JES-shifted jets — with the one-level answer (the factor's `"nominal"` member) named as the wrong result the anchor discriminates against. One sentence, same fixture family the bullet already describes.

---

## MID-3 — §6.4a's r24 BARE depth-`k` key: neither branch is required by any m51 anchor

**Section:** §6.4a r24 (lines 2216-2243) and §6.4d (lines 2548-2556); anchors = §10/m51 round-trip bullet (lines 4482-4506) and entry-check bullet (lines 4544-4590).

**Detail.** r24 adds a new, decidable grammar branch to `select=`:

> the bare depth `k ≥ 1` key is legal **iff** the record is itself jagged at depth `k` … a record carrying two or more independently jagged fields at that depth **REFUSES** the bare key at the `to_parquet` call, naming the ambiguity and the field paths.

Both halves are new m51 source (a record-time form inspection plus a refusal path with its own message), and neither is anchored:

- **Accept branch:** the round-trip bullet now pins the object-migration coverage item to the **MULTI-FIELD** record written through the FIELD-SCOPED `select={0: event_mask, ("Jet", 1): jet_mask}`, and mentions the bare form only descriptively ("while §6.4's canonical single-collection skim … uses §6.4a's r24 BARE depth-`k` key; state which shape each coverage item writes"). r22 made the coverage items separable ("MAY be SEPARATE fixtures"), so a conforming suite can write every level-≥1 item field-scoped and never exercise the bare key. The other m51 write anchors (`graphed.selection` bridge, entry checks, representation) all supply level 0 only or depth-0 fields.
- **Refuse branch:** the ambiguity refusal appears in **no** m51 anchor. The entry-check bullet enumerates predicate (1) multiplicity, (2a) lineage + both absent-operand cases + the fifth positive control, (2c) depth at level 0 and its level-≥1 mirror, (2b) row-count, the level-≥1 structural check, and §6.4b's row-space refusal — and stops there.

This is exactly the "new source with zero frozen-suite diff coverage" class the plan repairs elsewhere (r14 moving §3.4 to m49, r16/r17 for the `importorskip` cases, r18 for `to_parquet`, r22 for §6.4f's write-path refusal): under the DoD's ≥90 % diff coverage **from the frozen suite**, an m51 implementation of these two branches is coverable only in `tests/extra/**`, which the gate excludes.

**Evidence.** Plan lines 2216-2243 (the r24 rule and its refusal), 2548-2556 (§6.4d's restatement), 4484-4494 (the round-trip bullet's field-scoped pinning and the passing mention of the bare key), 4544-4590 (the entry-check bullet's complete predicate list — read in full; no ambiguity-refusal entry). The measured discriminator the rule rests on (`var * {pt: float64, eta: float64}` vs `{Jet: var * {…}, Muon: var * {…}}`) is a record-time form property and is therefore assertable at the call, so both anchors are cheap to build.

**Suggested fix.** In §10/m51: (a) require at least one round-trip coverage item to be the **single-collection** skim written with a bare depth-`k` key (`to_parquet(events.Jet, select={0: event_mask, 1: jet_mask})`), stated as such; (b) add one line to the entry-check bullet: a record with two independently jagged depth-1 fields (`{Jet: …, Muon: …}`) supplied a **bare** `1` key is refused at the `to_parquet` call naming the ambiguity and the field paths, with the field-scoped `("Jet", 1)` spelling on the same record as its positive control.

---

## MID-4 — §6.4e's r24 manifest addition (stored selection LEVELS) is unanchored, and m51's manifest anchor's "exactly" wording is a red-against-correct-implementation hazard

**Section:** §6.4e r24 (lines 2567-2571) and §6.4c r24 (lines 2512-2521); anchor = §10/m51 manifest bullet (lines 4609-4617).

**Detail.** r24 scopes bit-exact reconstruction to "the levels the user supplied through `select=`" and, consequently, adds a manifest field:

> A manifest (labels → appended columns → representation, **plus the selection LEVELS whose per-label masks are stored, r24** …)

m51's manifest anchor still reads:

> Manifest: parquet KV metadata lists **exactly** the appended labels/columns/representations and reads back; …

Two problems, in the plan's own vocabulary. First, the new field has no assertion anywhere — a reader that silently omits it still passes the round-trip anchor (which supplies both levels, so the reader never needs to consult the levels list to know what to reconstruct), which is the "invisible violation" shape r13/r14 caught for §8.2(i)'s sorted tuple and for manifest determinism. Second, "lists **exactly** the appended labels/columns/representations" is the exact-set wording this plan repeatedly identifies as a freeze hazard (§6.3 r17's params key set, §7.2 r19's schema key sets, §2.3d r18's containment floors): a test-author freezing it as an exact key-set/content assertion reds a correct m51 implementation the moment the levels entry is present.

**Evidence.** Plan lines 2512-2521 (§6.4c's r24 scoping and its explicit "§6.4e's manifest records which levels are stored"), 2567-2571 (§6.4e's field), 4609-4611 (the anchor's "lists exactly …"). The round-trip anchor at 4482-4506 supplies both levels, so it cannot discriminate a manifest missing the levels entry.

**Suggested fix.** Reword the m51 manifest anchor to a literally spelled expected manifest **key set that includes the levels entry**, and add one assertion: the manifest's stored-levels value equals the set of levels the fixture supplied through `select=` (both levels for the object-migration item, `{0}` for the weight-only one). Keep "exactly" only against the literally spelled set, per §6.3 r17's own repair.

---

## LOW-1 — §3.4's r24 operand names two incompatible shapes

**Section:** §3.4 (lines 1336-1348) and §9.1 (lines 3161-3163).

**Detail.** r24 shapes the impact API as "a read-only `graphed` module verb over the same operands as `read_columns`/`graphed.labels`, returning `{label: tuple[int, ...]}`" (§9.1 says "over `read_columns`' operands"). Those are not one operand shape: measured at `graphed-latest@ff7c607`, `read_columns(arrays: Sequence[Array], source_nid: int)` (`python/graphed/projection.py:109`) takes a source node id that is meaningless for a reachability difference, while `graphed.labels(x)` takes a single `Varied`/context/result. §5.3's stats verb legitimately inherits `read_columns`' operands (it *computes* read sets and needs `source_nid`); §3.4 does not. The m49 anchor asserts membership only, so nothing reds — but the test-author pins the spelling at freeze and will carry whichever reading they picked, plus possibly a vestigial `source_nid` parameter, read-only for the rest of the project.

**Suggested fix.** Name one operand: "over the outputs a label reaches — the same `Sequence[Array]` `read_columns` takes, without `source_nid`" (or `graphed.labels`' single operand), consistently in §3.4 and §9.1.

---

## LOW-2 — m48's §7.2 (α) anchor bindingly reads a private class, against §4.3's own "a frozen test cannot import an internal"

**Section:** §10/m48 §7.2 (α) bullet, r23 read-back route (lines 3545-3552); vs §4.3 r13 (lines 1428-1434).

**Detail.** The (α) anchor pins the read-back route as "the field off the CONCRETE closure type, `graphed.aggregate._PartitionReduce` (`python/graphed/aggregate.py:44-55`), via a narrowing `isinstance`/cast". §4.3, arguing for a *public* per-label fill-node accessor, states the opposite principle: "ownership is not an importable surface, and **a frozen test cannot import an internal**". Both are binding text in the same document, and the m48 suite would do both. (The plan also records a counter-precedent — "The house pattern for reaching the store from a frozen test is `s._store.nodes()`", §10/m48 §1.2 bullet — so the practice is tolerated; verified at `graphed-latest@ff7c607` that `_PartitionReduce` is a module-private frozen dataclass at `python/graphed/aggregate.py:44-55`.)

**Suggested fix.** One clause in the (α) bullet acknowledging the private-access precedent (`s._store.nodes()`, `graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84`) and scoping §4.3's sentence to *importable public surfaces the anchor's assertion depends on* — or, cheaper, have (α) read the returned payload through the same public seam the hook already is.

---

## LOW-3 — §2.2's "container class PAIRED WITH `type(x)`" is undefined for §2.1(a)'s `Varied` target

**Section:** §2.2 r24 (lines 548-553); §2.1(a) (lines 433-435).

**Detail.** r24 binds `graphed.vary(x, …)` to return "the container class PAIRED WITH `type(x)`, exactly as the session pairs its proxy class with the backend". §2.1(a) admits an **`Array | Varied` target** (stacking on a loose container is explicitly public, and m48's stacking anchor exercises stacking). When `x` is already a `Varied`, `type(x)` is the container class, not the idiom's `Array` class, so the pairing rule has no defined answer. Measured surfaces that make the distinction load-bearing: `dir(graphed.Array)` public = `['filter','map','node_id','reduce','repartition','session']` (6) vs `dir(graphed.numpy.NumpyArray)` = 32 (probed in-session in `graphed-latest`'s `.venv` at `ff7c607`).

**Suggested fix.** "…paired with `type(x)` when `x` is an `Array`, and with `type(graphed.nominal(x))` when `x` is already a `Varied` (i.e. the idiom is taken from the members, never from the container)."

---

## LOW-4 — §2.2's r24 `graphed.nominal` on the two RESULT shapes is anchored only for the axis-mode shape

**Section:** §2.2 r24 (lines 573-581); anchors = §10/m50 (i-bis) (lines 4394-4396) and §10/m48 §6.1a (lines 3682-3706).

**Detail.** r24 binds `graphed.nominal(x) ≡ graphed.universe(x, "nominal")` on **both** result shapes and gives three answers: identity for a bare unvaried histogram, `x["nominal"]` for a `{label: hist}` mapping, and the nominal slice for an axis-mode histogram. Only the third is anchored (m50's (i-bis) bullet, r24). m48's §6.1a anchor names only `graphed.universe`/`graphed.labels` ("narrow both shapes uniformly"), and §6.1a's own prose likewise names only those two. The unanchored halves are the trivial ones, hence LOW — but they are m48 source under the same diff-coverage gate, and the identity answer for a bare `hist` is the one an implementer is most likely to spell as "return the argument" for *every* histogram, which is the confidently-wrong case §2.2 cites as its reason for binding the rule.

**Suggested fix.** Add `graphed.nominal` to the m48 §6.1a anchor's narrowing assertion ("`graphed.universe`/`graphed.nominal`/`graphed.labels` narrow both shapes uniformly"), one word.

---

## Clean/dirty verdict

**Dirty — but only at MID and below.** Nothing in this lens blocks a milestone: no anchor as worded is unbuildable, no frozen anchor would freeze a semantics that a later bound requirement must contradict, no new tautology or self-derived oracle was introduced in r24, R0.10a is respected (§3.3 remains the single, explicitly named wall-clock carve-out; m50's scaling and m51's compression stay structural / R0.11), and the determinism anchors (m48 `PYTHONHASHSEED` IR byte-identity, m49 plan bytes with the module-level by-value `DurablePlan`, m51 manifest bytes) remain compatible with what they measure.

The residue is concentrated in r24's own new bindings: one false stated equivalence in a predicate the m48 test-author is told to word an anchor over (MID-1), and three coverage/discrimination gaps where a rule bound in r24 has no anchor that can fail its plausible wrong implementation (MID-2 two-level factor resolution, MID-3 the bare depth-`k` key and its ambiguity refusal, MID-4 the manifest's stored-levels field plus its "exactly"-worded anchor). All four are one-to-three-sentence edits to §10 and to the sections that introduced them; none touches an owner-locked decision, none reopens a settled design, and none requires re-measuring anything.
