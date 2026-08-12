# systematics-vary-plan r27 — adjudicated closure of review round 18 (audit trail)

Scope: the 18 severe findings of review round 18 (r26 reviews: facts / design / tests). Closure
discipline: fix exactly these findings, prefer deletion/weakening over new specification, descope to
§12.4 rather than write substantial new contract surface. Every retained factual claim is measured
in this session against the pinned verification roots.

Verification roots used: `/private/tmp/claude-501/graphed-latest` (@ff7c607, incl. its own `.venv`,
awkward 2.12.0, CPython 3.12), `/private/tmp/claude-501/graphed-histogram-latest` (@211cbbe).

Verdict tally: **17 fixed, 0 refuted, 3 items additionally ledgered to §12.4** (two of them are
partial descopes attached to fixed findings, one is a cost question the fix raises). Findings #1 and
#12 are the same defect raised by two lenses and were fixed once.

---

## Session measurements (the basis for every "measured" word added to the plan)

| Probe | Result |
|---|---|
| `b = a*2.0; c = a*2.0` on one Session | `b.node_id == c.node_id == 1`, `b is c` False, `node_count() == 2` |
| `type(b == c)` / `bool(b == c)` | `graphed.array.Array` / `True` |
| `Array` dunders | `__eq__` at `python/graphed/array.py:236`; no `__bool__`/`__len__`; `__slots__` at `:127-128` |
| `read_columns([ev.Jet.pt], src)` vs `+ ev.Jet.eta` (nested record) | `('Jet',)` and `('Jet',)` — unchanged |
| same on a FLAT record (`Jet_pt`/`Jet_eta`/`Muon_pt`) | `('Jet_pt',)` → `('Jet_eta','Jet_pt')` — extra column sorts FIRST |
| `sorted([0, ["Jet", 1]])` | `TypeError: '<' not supported between instances of 'list' and 'int'` |
| `json.dumps({"levels":[0,["Jet",1]]}, sort_keys=True)` | `{"levels": [0, ["Jet", 1]]}` — list element order untouched |
| `hasattr(graphed.numpy, "to_parquet")` | `False` |
| `signature(graphed.numpy.io.to_parquet)` | `(array, destination, *, steps_per_file, compute, executor, prefix, column)` — no `select=` |
| `signature(graphed.awkward.io.to_parquet)` | same + `behavior` |
| annotation-wide `Array` filter over `graphed.__all__` | `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']` |
| `NodeKey::is_boundary` | `!matches!(self, NodeKey::Op { .. })`, `src/node.rs:100-104` |
| `plan()` in graphed-histogram | `fill_nodes` at `boost.py:281`, `layout` `:282`, `aggregate_plan(...)` `:286-295`; `fill_nodes()` returns bare `list[Array]` `:218-219` |
| `session.walk` | `def walk(` `:245`, `-> object:` `:252`, `root = array.node_id` `:268`, `return cache[root]` `:288` |
| `Projection` / `BufferProjection` | `projection.py:34-44` (`read_columns`) / `:60-72` (`read_buffers`); `project`/`project_buffers` at `awkward/projection.py:105,119` |
| `FORMAT_VERSION` | `= 1`, `preserve/manifest.py:17`; `canonical_bytes` `:20-22` |

---

## Per-finding disposition

### 1 + 12 — HIGH (design + tests): §8.2(i)'s r26 producer cannot produce what §8.2 binds
**Verdict: FIXED** (one edit serving both). Verified: `plan()` owns only the
`(output, label) → fill node id` roots (`boost.py:281,286-295`); an `External` fill is a stage
BOUNDARY (`is_boundary` = `!matches!(self, NodeKey::Op {..})`, `src/node.rs:100-104`), so the
universe's compute chain fuses into a stage whose key is never a fill-node key, and §8.2(iii)'s
op-dispatch lookups all miss. Composition over the roots alone is also single-valued, so §8.2's
set-valuedness argument and m49's "two labels' cones both reach one key" bullet had no witness.

Edit — §8.2(i) producer clause: replaced "by composing that map with the m49 core accessor" with the
per-label record-CONE walk (`session.walk` from each label's marked output, every reached id mapped
through the m49 accessor, labels UNIONED per `(reduced_node_id, member_index)` key), plus the
measured reason composition-over-roots cannot serve (`src/node.rs:100-104`). The `(output, label)`
map is re-cast as the cone ROOTS; `plan()` holds those fill nodes hence a `Session`.

Edit — §10/m49's `variation_labels` population bullet: added the fixture shape requirement (the
shared node is UPSTREAM of the label fork, §3.4 r24 shape), with §6.1b's `1 + |S| + |W|` as the
reason no fill-node key is ever reached by two labels.

Ledger: §12.4(3) — the cone walk's cost inside `plan()` is a driver-side once-per-plan traversal;
m49 decomposition confirms it against §3.3's budget and states the measurement (R0.11) rather than
the plan asserting an unmeasured number.

### 2 — MID (design): `Sequence[Varied]` cannot be formed for the primary sink
**Verdict: FIXED (weakening).** Verified: §9.1 binds `fill_nodes_by_label(h) -> dict[str, Array]`;
`Histogram.fill_nodes()` is a bare `list[Array]` (`boost.py:218-219`); §4.3 reaches `fill_node[label]`
through that same accessor (read in full this session). `Array.__slots__` carries no label
attribution (`array.py:127-128`), so r26's premise stands — only its conclusion was too narrow.

Edit: widened the operand of both m49 verbs to `Sequence[Varied] | Mapping[str, Sequence[Array]]` at
all four sites — §3.4, §5.3, §9.1 (both verb entries) — and in §10/m49's impact-fixture parenthetical.
§5.3's computation sentence now reads "each label's members (`graphed.universe(v, L)` for a `Varied`
operand, the mapping's own entry for a labelled mapping)". This is a widening of an accepted operand,
not new surface. Ledger: §12.4(1) — exact annotation and ill-formed-operand rejection at m49 freeze.

### 3 — MID (design): §2.1's r26 row-space parenthetical vs §2.6c's per-label row sets
**Verdict: FIXED (ordering, no new machinery).** Verified from the plan text: §2.6c binds a
`Varied`-mask-derived context's row set as per-label; §2.1's parenthetical reduced a re-index-produced
`Varied` to its central universe, landing members at nominal's rows while `context_of` answers a
handle whose reads are per-label; `Session.record_op` validates only `op_form`
(`session.py:142-168`), so such a program records cleanly and dies at execution.

Edit: the parenthetical now ORDERS the two rules — reduce AS SUPPLIED, then re-index LABEL-ALIGNED
per §2.4 (the operation §2.6c already binds for the ambient registry) — and restates the invariant
per label ("every member answers in the container handle's PER-LABEL row spaces"), which is what
§6.1d(B)'s identity clause assumes. No new verb, no new check.

### 4 — MID (design): §6.4f's numpy write refusal had no trigger, spelling or entry point
**Verdict: FIXED (descoped trigger).** Verified: `hasattr(graphed.numpy, "to_parquet")` is `False`;
the function is `graphed.numpy.io.to_parquet` with NO `select=` (`numpy/io.py:182-191`).

Edit — §6.4f: pinned the entry point (module path, measured not a package attribute) and the trigger
(a `Varied` FIRST POSITIONAL), raised as a graphed error naming the awkward backend instead of §2.2's
reserved-name `AttributeError`. Explicitly **descoped the `select=` arm**: the numpy idiom gains no
such keyword, so a `select=` call stays an ordinary `TypeError` and no anchor may freeze a graphed
error for it. This is the deletion-flavoured half of the finding's suggested fix — the suggestion
would have required the implementer to ADD a keyword purely to refuse it.
Edit — §10/m51's numpy bullet: worded over that trigger, with the explicit "do NOT freeze a `select=`
arm". Ledger: §12.4(2) — error class/message at m51 freeze.

### 5 — LOW (design): `project_buffers` classified as returning `{label: Projection}`
**Verdict: FIXED.** Verified: `project(...) -> Projection` at `awkward/projection.py:105`,
`project_buffers(...) -> BufferProjection` at `:119`; the two dataclasses are distinct
(`projection.py:34-44` `read_columns` vs `:60-72` `read_buffers`).
Edit: §2.3d and §10/m48's idiom-enumeration bullet now say `{label: Projection}` and
`{label: BufferProjection}` respectively, each with its file:line.

### 6 — LOW (design): §2.3d r20's stated ground for classifying the m49 verbs is falsified
**Verdict: FIXED (deletion of a false justification).** Verified by re-running the filter myself:
over `graphed.__all__` it yields exactly the eight names listed in the table above — neither m49 verb
would be discovered, and after r26/r27 neither annotation mentions `Array`.
Edit: the clause now states that the annotation-wide filter does NOT discover them (with the measured
eight-name result), that they are classified for table completeness, and that the containment floor is
unaffected. The false "makes the m48 frozen gate discover them one milestone after the freeze" is gone.

### 7 — LOW (design): §6.4 never bound the stored masks' row length nor the check ordering
**Verdict: FIXED (one clause).** Verified from the plan: §6.4a stores one packed per-label mask per
supplied entry, §6.4b writes on superset rows, §6.4c requires bit-exact reconstruction from the stored
data; the level-≥1 structural predicate is raised from `_WritePart` before any buffer is stored
(`awkward/io.py:111-127`), i.e. against the pre-OR record.
Edit: §6.4a now binds every stored per-label mask (level 0 and every k ≥ 1) to the SUPERSET rows
(level-0-OR-restricted), with the structural predicate running against the offsets AS EVALUATED and
the restriction then applied to mask and buffers alike. This is the on-disk contract §6.4e's manifest
describes to third-party readers, so it belongs in the plan rather than in an implementation.

### 8 — LOW (design): m48's `context_of` fixture note argues from a reversed premise
**Verdict: FIXED (deletion of the stale rationale).** Verified from the plan: §2.1 r26 accepts the
mask-derived container by re-indexing it, so "freezing it would foreclose a §2.1 construction check"
is no longer true.
Edit — §10/m48: the r21 rationale is replaced; the identity link is kept, now justified by row-space
stability and §6.4a(2a) proximity alone.
Edit — §2.1 (the mirror sentence at the other end of the same argument): "m48's `context_of` fixture
note already declines to freeze that program as constructible precisely to keep this check open" →
the fixture pins the identity-link spelling for row-space stability, NOT to keep a construction check
open, since §2.1 decides the mask-derived case by re-indexing it. Both readings now agree.

### 9 — LOW (design): §2.3d's accepting disposition covers `select=` only
**Verdict: FIXED.** Verified: §6.4's canonical skim is `to_parquet(events.Jet, select=…)` and §2.6b
makes `events.<Collection>` a `Varied` after a shift-form `vary`; `to_parquet(array: Any, …)` reads
the array's Session (`awkward/io.py:206-216`), so an unhandled `Varied` first positional dies as
§2.2's reserved-name `AttributeError`.
Edit: §2.3d's disposition and §10/m51's table-entry anchor now read "a `Varied` RECORD and/or a
`Varied` `select=`", both arms.

### 10 — LOW (design): §2.6c's "its collections are Varied per §2.6b" vs §2.2 term (b)
**Verdict: FIXED (cross-reference).** Verified from the plan: §2.2 scopes term (b) to collections a
shift-form `vary` REPLACED, explicitly excluding the implicitly-varied reads §2.6c produces; §2.6c
pointed at §2.6b (the registration clause) for exactly those reads.
Edit: §2.6c now reads "its collections READ as `Varied` (§2.4-aligned per label) — an implicit
property of the derivation, NOT a shift-form registration, so §2.2's `graphed.labels` term (b) does
not count them; the mask's own labels enter through term (c)". Resolved at the definition site
instead of three sections away.

### 11 — HIGH (tests): m48's stacking anchor asserts `==` between two recorded expressions
**Verdict: FIXED.** Measured this session: `Array.__eq__` records an op (`array.py:236`), `Array`
defines no `__bool__`/`__len__` (`__slots__` `:127-128`), and `bool(b == c)` is `True` — so the
anchor's assertion is green for every operand pair, including the one-level wrong answer it exists to
reject, and it records a stray comparison node. Node-id equality is the sound alternative: two
independently recorded `a * 2.0` expressions share `node_id == 1` while being distinct objects
(interning, `src/store.rs:73-88`).
Edit — §10/m48: the assertion is respelled with `.node_id` on both sides, with the measurement, the
interning basis, and `Session.materialize` (`session.py:291-301`) named as the equally acceptable
elementwise form.
Edit — §2.2, beside r26's `x[L]` prose rule (this is the same transcription-hazard class, and r26
established that literal transcription IS the expected test-author behaviour): a general rule that
`==` between two RECORDED expressions in this document's prose denotes structural identity
(`.node_id`), never a Python `assert` on the recorded comparison. This closes the class, not just the
instance — it was the only `Array`-vs-`Array` equality in the §10 anchor list.

### 13 — HIGH (tests): §5.3's `Jet.eta` union-growth anchor is unsatisfiable
**Verdict: FIXED (example withdrawn, fixture pinned).** Measured: `read_columns` counts a
`field`/`fields` op only when its input IS the source node (`projection.py:129-141`), so
`read_columns([ev.Jet.pt], src)` and `read_columns([ev.Jet.pt, ev.Jet.eta], src)` are BOTH `('Jet',)`;
on a flat source the same pair gives `('Jet_pt',)` → `('Jet_eta','Jet_pt')`.
Edit — §5.3: the `Jet.eta` example is explicitly WITHDRAWN as not expressible through this verb; the
granularity is stated once with its file:line and both measurements; the m49 fixture's source is
pinned FLAT (`Jet_pt`/`Jet_eta`/`Muon_pt`) with `Jet_eta` as the shift's extra top-level column;
buffer-level projection is named as not what §5.3 binds.
Edit — §10/m49's projection bullet: same pin, stated where the test-author reads it.

### 14 — MID (tests): the "immune" per-label restatement is red against §5.3's sorted return
**Verdict: FIXED.** Measured: returns are `tuple(sorted(needed))` (`projection.py:147`) and on the
r27 flat fixture the extra column sorts FIRST (`('Jet_eta','Jet_pt')`), so
`('Jet_pt',) + ('Jet_eta',)` ≠ the correct answer.
Edit (both occurrences — §5.3 body and §10/m49): replaced with the order-insensitive pair
`set(stats["jes_up"]) - set(stats["nominal"]) == {"Jet_eta"}` AND
`set(stats["nominal"]) - set(stats["jes_up"]) == set()` (the second conjunct prevents degeneration to
a containment test), with `tuple(sorted(stats["nominal"] + ("Jet_eta",)))` named as the acceptable
concatenation form and plain concatenation marked RED with its reason.

### 15 — MID (tests): §6.4e's "SORTED list" has no defined total order
**Verdict: FIXED (order bound).** Measured: `sorted([0, ["Jet", 1]])` raises `TypeError`;
`json.dumps(..., sort_keys=True)` leaves list element order untouched; the house serializer is
`preserve/manifest.py:20-22`.
Edit — §6.4e: dropped the undefined "SORTED" adjective and bound the total order explicitly as
`(depth, field_path or "")` — bare-depth entries before field-scoped entries of the same depth,
field-scoped by the `_`-flattened path §6.4b already binds — with both measurements as the reason
neither `sorted()` nor the serializer supplies it.
Edit — §10/m51's manifest-determinism anchor: reworded over that order ("the serialized MAPPING-key
order is asserted sorted and the levels LIST is asserted in §6.4e's r27 order").

### 16 — MID (tests): §9.2's bound `FORMAT_VERSION` bump is witnessed by no anchor
**Verdict: FIXED (anchor clause, not a new rule).** Verified: `FORMAT_VERSION = 1`
(`manifest.py:17`); the fingerprint is SHA-256 of the canonical manifest (`:20-26`); m50's §9.2 anchor
asserted only the round-trip, the unvaried control and `inspect()` — all green whether or not the
version moves.
Edit — §10/m50's §9.2 bullet: added two assertions on fixtures the anchor already builds (varied
bundle carries the bumped `format_version`, unvaried control still carries `1`), with the reason
(otherwise an unbumped varied bundle is indistinguishable by version from a v1 bundle a v1 reader
mis-parses). Chose the anchor over the "mark it knowingly UNANCHORED" alternative because the cost is
two assertions on existing fixtures and the failure mode is a silent on-disk format collision.

### 17 — LOW (tests): m51's manifest anchor asserts a SET against §6.4e's LIST
**Verdict: FIXED.** Verified: §6.4e binds a JSON list of ints and two-element arrays; the round-trip
shape is `{"levels": [0, ["Jet", 1]]}`.
Edit — §10/m51: "equals the set of levels the fixture supplied" → "equals the literally spelled
expected LIST, in §6.4e's r27 bound order" with `[0, ["Jet", 1]]` / `[0]` spelled out, and the reason
recorded so the mismatch is not re-introduced.

### 18 — LOW (facts): `session.walk` anchor span misses the "returns the root's value" half
**Verdict: FIXED.** Verified: `def walk(` `:245`, `-> object:` `:252`, docstring `:253-254`,
`root = array.node_id` `:268`, `return cache[root]` `:288` — the return-value half is at `:288`, not
inside `:245-255`.
Edit: both occurrences (§3.4 body and the r24 revision-history entry) now cite
`python/graphed/session.py:245-255,288`, matching the `:245-252` + `:268` pattern the plan already
uses elsewhere.

---

## Refutations

None. Every finding's core claim reproduced against the pinned roots. Two findings' *suggested fixes*
were partially declined on closure grounds, with the reasons recorded above:

- #4: the suggestion would have added a `select=` keyword to the numpy idiom purely so it could be
  refused. Declined — the refusal is bound on the `Varied` first positional and the `select=` arm is
  explicitly descoped, which is the smaller contract.
- #2: the suggestion offered `Sequence[Varied] | Mapping[str, Sequence[Array]]` or a mapping-only
  operand. Took the union (a widening) rather than replacing the operand, so m49's existing
  loose-container anchors are unaffected and no frozen-suite change is implied.

## Plan-level edits

- Status line: `draft for review (r26)` → **`review-clean (r27, adjudicated closure)`**.
- New **§12.1a** recording the closure decision (18 rounds, converged substance, no-new-surface
  discipline, cycle terminates).
- New **§12.4 Closure ledger** with three one-line deferrals to m48/m49/m51 decomposition:
  (1) the two-form operand's exact annotation; (2) the numpy refusal's error class/message (and the
  bindingly absent `select=` arm); (3) the §8.2(i) cone-walk cost measurement under R0.11.
- Revision-history entry **r27 (2026-08-12)** summarizing the three HIGH fixes, the six MID fixes and
  the eight LOW fixes, with the measurements each rests on.

Diff: 242 insertions, 55 deletions in `systematics-vary-plan.md` (6250 → 6437 lines).

---

## Repair pass (round-18 re-check of r27's own new text)

One finding was reported unresolved after the r27 sweep — the re-check of §2.3d's m49 discovery
clause. It is the only item in this pass.

### Finding 6 (LOW) — §2.3d: r20's stated ground for classifying the m49 verbs — **fixed**

**Verdict: fixed** (the original round-18 finding was correct that r20's ground was stale; r27's
first replacement over-corrected and became false in the opposite direction).

**Evidence (measured this session, not inherited):**
- The filter is defined in §2.3d itself at plan `:919-920`: `graphed.__all__` filtered to
  `inspect.isfunction` members "**any of whose parameter annotations MENTIONS `Array`**
  (including `Sequence[Array]`, unions and `*args: Array`)".
- The r27 operand, spelled in the same sentence and at plan `:1437,:1657,:3416,:3422,:4534,:5157`,
  is `Sequence[Varied] | Mapping[str, Sequence[Array]]` — a union that literally contains `Array`.
  So the filter reaches the m49 verbs once they land; r27's claim that it "does NOT discover them"
  contradicts the filter definition eight lines above it.
- The measurement r27 cited is itself true but does not support the claim: run in
  `/private/tmp/claude-501/graphed-latest` (@ff7c607) with its own `.venv`, the filter over
  `graphed.__all__` yields exactly
  `['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']`
  — a repo in which **neither m49 verb exists yet**, so it says nothing about post-m49 discovery.
- The round-18 finding anticipated this: its suggested_fix carried the contingency "If the operand
  becomes the labelled mapping per the §3.4/§5.3 finding, state it there instead." r27 applied the
  MID §3.4/§5.3 widening (union incl. the mapping) and the LOW reword independently, so the two
  fixes collided.

**Exact edit** — plan `:1014-1023`, the "m49 verbs … enter the table *expanding*" clause. The
false ground is replaced, no new contract surface added (the classification, the self-repair rule
and the containment floor are untouched):

- before: "**Their operands are LABELLED CONTAINERS after r26/r27 (`Sequence[Varied] | Mapping[str,
  Sequence[Array]]`), so the annotation-wide filter does NOT discover them**"
- after: "**Their r27 operand `Sequence[Varied] | Mapping[str, Sequence[Array]]` MENTIONS `Array`,
  so the annotation-wide filter DOES discover them one milestone after the m48 freeze**", with the
  parenthetical now recording all three states (r20 presumed bare `Array`; r26's narrowing to bare
  `Sequence[Varied]` would have hidden them; r27's widening restores r20's prediction under the
  filter's own "unions" clause) and the measurement re-labelled as taken on a repo "where neither
  verb exists yet". The dangling "They are classified here for the table's completeness" half-
  sentence is dropped, since under the corrected ground the verbs ARE discovered and the
  classification is load-bearing, not decorative.

**Revision history** — the r27 LOW bullet at `:5331-5333` repeated the false claim ("yields exactly
eight names, none of them the m49 verbs" used as evidence of non-discovery); reworded to "the
widened r27 operand mentions `Array`, so the filter does reach the m49 verbs once they land". A
short **Repair pass** line is appended to the r27 entry recording the self-correction.

**No ledger entry, no refutation.** Nothing else in the plan depends on the non-discovery reading:
grep for the operand string shows the other six sites state the type only, and the m48 gate's floor
is a containment floor either way (plan `:1021-1023`).
