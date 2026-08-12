# systematics-vary plan — review round 9, TEST ARCHITECTURE lens

- **Lens**: test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, traceability (requirement ↔ anchor), and buildability of the fixtures the anchors need.
- **Plan revision reviewed**: r17 (`systematics-vary-plan.md`, 3857 lines, read in full including
  Part I, every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Date**: 2026-07-30.
- **Verification roots used** (every code fact below was measured in this session against these,
  never against the stale submodules in `/Users/lgray/vibe-coding/graphed-workdir`):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (its own `.venv`; cloudpickle 3.1.2)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (its own `.venv`;
    boost_histogram 1.8.0)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10 / R0.10a / R0.11 text)
- **Owner-locked decisions** (naming, functional surface, e-form encoding, event-context semantics,
  record-time expansion, m48–m51 scope, the Phase-2 pull-in) are taken as given; nothing below asks
  for a different choice.

Findings are ordered by severity. Nine of the fourteen r17-introduced or r17-touched clauses I
checked are cleanly anchored; the defects below are the exceptions.

---

## HIGH-1 — m49's plan-byte determinism anchor is *blind to the defect it exists to catch* under the `DurablePlan` construction §7.3 itself offers (and *red against a correct implementation* under the obvious alternative)

**Section**: §10/m49 (`:2862-2866`), §7.3 (`:1980-1987`), §8.2(i) (`:2063-2079`).

**Detail.** §8.2(i) binds `variation_labels` as a *sorted tuple*, never a `frozenset`, because a
frozenset pickles in hash order and those bytes feed `OpSpec.identity()` → `DurablePlan.task_id()`
/`to_bytes()`. m49's anchor is the frozen guard: "the same varied program built in two fresh
processes under differing `PYTHONHASHSEED` yields byte-identical `DurablePlan.to_bytes()` and
identical per-partition `task_id`".

Measured: that guard only observes `variation_labels` when the plan's `process` `OpSpec` embeds
`_PartitionReduce` **by value**. `OpSpec.identity()` for `kind="ref"` is
`b"ref\0" + ref.encode()` (`python/graphed/core/plan.py:72-76`) — the closure's fields are simply
not in the bytes. And r17's own §7.3 clause offers the by-reference route as one of two acceptable
constructions for the m49 fixture ("either in the m8 pattern (module-level process functions,
`process=OpSpec.from_ref(...)`) … or as `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process), …)`"),
with the m8 frozen precedent (`tests/frozen/checkpoint/m8/analyses.py:114-123`) using `from_ref`
for all three specs. A test-author who follows the house precedent freezes a green anchor that a
`frozenset` implementation passes.

The other half is worse than vacuity. Measured this session (cloudpickle 3.1.2,
`PYTHONHASHSEED` ∈ {1, 7, 12345}):

| closure content | sha256[:16] per seed | stable? |
|---|---|---|
| dataclass + reader class both **importable**, `labels` = sorted tuple | `5ebf8e663b159b55` ×3 | yes |
| same, `labels` = `frozenset({...})` | `bca51bab689531bd` / `a7fb499fb8798875` / `a8519bd5a988a850` | **no** (the defect the anchor targets) |
| same, but the dataclass/reader defined in `__main__` (pickled **by value**) | 3 distinct digests for **both** the tuple and the frozenset form | **no** |
| a dynamically created class (`type("L",(object,),{})`) | `348bdc75…` / `336ba018…` / `a3f65460…` | **no** |

So a fixture whose `PartitionedSource`/`reduce` operands are defined inside a test function (or in a
`__main__` driver) makes the anchor **red against a correct implementation** — the R0.10a
"red for the wrong reason" shape, on a frozen test.

The same clause weakens the neighbouring §7.3 interrupt/resume anchor: under the m8 `from_ref`
pattern the process function is a hand-written module-level callable over a hand-built IR
(`analyses.py:100-105` builds its IR with raw `GraphStore`), so "a varied graph whose result is
byte-identical to an uninterrupted run" would exercise no varied lowering at all.

**Suggested fix.** In m49's anchor (and in §7.3), bind the construction for **both** anchors to the
by-value form — `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process), …)` over the plan
`aggregate_plan` actually returned — and add one sentence pinning the fixture's closure operands
(the `PartitionedSource`, the `reduce`/`combine`/`empty` callables) to **module-level, importable**
definitions, with the measured reason: a by-value-pickled class is itself seed-dependent, so the
anchor would go red for a reason unrelated to `variation_labels`. Delete the `from_ref` alternative
from §7.3 for these two anchors (it remains the right *documented user idiom*, which is exactly why
§7.3's churn scoping is correct — but it is the wrong *test* construction here).

---

## HIGH-2 — m48 freezes `to_parquet`'s §2.3d disposition, which m51 is bindingly required to change: a frozen anchor blocking a later bound requirement

**Section**: §2.3d (`:603-611`), §10/m48 (`:2464-2491`), §10/m51 (`:3088-3091`).

**Detail.** r17 made `to_parquet`'s disposition milestone-dependent: *refusing* at m48 (with an error
naming `select=` and m51), *accepting* at m51. `graphed.awkward.to_parquet` is simultaneously
placed in m48's **named floor list** for the table-driven gate
(`{graphed.compile_ir, graphed.context_of, graphed.broadcast_like, graphed.awkward.to_parquet}`),
and §2.3d's justification for the m48 classification is explicitly that "the table records the
milestone's truth" and that classifying it *accepting* at m48 "would make the m48 gate **certify a
table entry**". A gate that certifies table entries, run over a floor list that names `to_parquet`,
is a gate a test-author will most plausibly write as an assertion on that entry's *value* — frozen
read-only for three milestones. At m51 the entry becomes *accepting* and the m48 frozen test turns
red; the only exits are a Test Dispute or an integrity violation.

The same hazard sits in the per-class floor wording, which r17 phrases as an *exact* set — "at m48
`graphed`'s half hosts the first four **only**" (`:2485-2486`). An exact class-set assertion is
false the moment m51 adds an *accepting* member to the same table.

Second, smaller half: §2.3d binds a **behaviour** for m48 (`to_parquet` refuses "with an error
naming `select=` and m51"). That is new m48 source — measured, today's
`to_parquet(array, destination, *, steps_per_file, compute, executor, prefix, column, behavior)`
(`python/graphed/awkward/io.py:206-216`) has no `select=` parameter at all, so m48 must add one
purely to refuse — and no m48 anchor asserts it: the m48 refusal table is split into
"boundary/plan verbs" and "compile/aggregate verbs" (`:2492-2505`), and `to_parquet` is in neither.
New m48 source with zero frozen coverage is exactly the DoD ≥90 %-diff-coverage-from-the-frozen-suite
argument r14/r16/r17 used to move §3.4, the m50 listing and m51's `graphed.selection` cases.

**Suggested fix.** Drop `graphed.awkward.to_parquet` from m48's named floor list — it is the sole
representative of nothing (measured: the annotation-wide filter over `graphed.__all__` yields
`aggregate_plan`/`apply`/`join`/`join_plan`/`pack_key`/`read_columns`/`repartition`/`shuffle_plan`,
six of which are *refusing*), so removing it costs no class coverage. Then either (a) leave
`to_parquet` undisposed until m51 and delete the m48 refusal behaviour (simplest: at m48 a `Varied`
`select=` is just an unexpected keyword), or (b) keep the m48 refusal and anchor it, but state
explicitly that m48's frozen test asserts *only* that a disposition exists for it and **must not**
assert its value or an exact class-set equality. Re-word the per-class floor as "**≥ one** member of
each of {refusing, expanding, broadcasting, eager-metadata}" and delete "only".

---

## HIGH-3 — §6.1d's mask-derivation ancestor re-indexing (link kind (1)) — the mainline case — has no value-asserting anchor, while the sibling case (link kind (3)) got exactly that repair in r15

**Section**: §6.1d (`:1340-1356`), §10/m48 (`:2635-2673`).

**Detail.** §6.1d binds three link kinds for re-indexing an ancestor-context value to the unified
context. m48 anchors two of them properly and the third not at all:

- link kind (3) (universe/nominal projection): anchored, and r15 explicitly strengthened it to be
  "asserted over the resulting VALUE, not merely over the absence of the divergence error … compared
  elementwise against a manually projected reference, so a guess that unifies but silently
  mis-weights cannot pass" (`:2669-2673`);
- link kind (2) (`vary`, identity): nothing to assert beyond lineage — covered;
- link kind (1) (**mask derivation**, `ctx[mask]`): the only m48 assertion is a *positive control at
  the op* — "an ancestor-chain pair unifies silently to the most-derived context" (`:2640-2641`) —
  which is an assertion of **absence of an error**, precisely the shape r15 rejected for link
  kind (3).

§6.1d's own worked example is a link-kind-(1) program (`h.fill(events.MET.pt, sel.Jet.pt)`,
`:1357-1360`), and §2.6c (r17) makes it the central idiom ("`sel.Jet` IS `events.Jet` re-indexed by
`sel`'s derivation mask"). Note also that `:880` claims "m48's re-indexing anchor" is defined against
this rule — measured against the anchor list, the only m48 re-indexing anchor is the **ambient
weight** one (`:2652-2658`), a different operation (registry inheritance at `ctx[mask]`, not
ancestor-value re-indexing at the fill). Mixing a per-event root quantity with a selected quantity in
one fill is the most common shape in the exemplars this plan surveys; an implementation that unifies
handles but does not re-index the ancestor value satisfies every m48 anchor.

**Suggested fix.** Add to m48's §2.6/§6.1d anchor (the `graphed-histogram` half, per r16's split
rule) an explicit link-kind-(1) case: `h.fill(events.MET.pt, sel.Jet.pt)` with `sel = events[mask]`
and a `Varied` mask, asserted **elementwise against a manually re-indexed reference** — the same
wording r15 gave the universe/nominal clause — plus the label-aligned per-label re-index (each
label's member by that label's mask). Also correct `:880`'s cross-reference, which currently points
at the ambient-weight anchor.

---

## MID-1 — §3.3's frozen wall-clock bound copies m4's literal `24.0` onto a *5.4×* size span, so it only discriminates exponents ≥ 1.89 — a node-quadratic reducer can pass the ONE frozen timing gate in this plan

**Section**: §3.3 (`:990-998`), §10/m49 (`:2843-2844`).

**Detail.** §3.3 declares itself "the ONE frozen wall-clock gate in m48–m51 … a deliberate, named
carve-out to R0.10a", justified by M4's mandate, and sets `time(128)/time(16) < 24.0` "the m4
threshold style". Measured this session against `graphed-latest` on §3.3's exact builder
(D=500, K=50, per-universe {1 fork, 50 chain ops, 1 terminating reduction}, every reduction marked):

| N | `reachable_nodes` | `stages` | `reduced_nodes` | reduce time (single run) |
|---|---|---|---|---|
| 16 | 1333 | 17 | 34 | 3.62 ms |
| 128 | 7157 | 129 | 258 | 17.5 ms |

(The `stages == N+1` / `reduced_nodes == 2N+2` literals and the load-bearing terminating reduction
are confirmed exactly: without the reduction the same builder gives 18 / 130.)

The problem is the *span*, not the numbers. m4's frozen gate spans 1k→8k nodes: 8× size against a
24.0 bound, so it fails any exponent ≥ ln24/ln8 = **1.53**, with linear ≈ 8 giving 3× headroom.
§3.3's topology grows the node count by only 1333→7157 = **5.37×** (N grows 8×, but the shared
D=500 prefix and the constant per-universe suffix dilute it), so the same 24.0 literal fails only
exponents ≥ ln24/ln5.37 = **1.89**. A reducer that is quadratic in node count would measure
5.37² = 28.8× *asymptotically* — 1.2× above the gate — and any non-negligible linear term pulls the
measured ratio under 24. The single most important guard in the project plan is thus reproduced at
roughly a quarter of its original discriminating margin.

**Suggested fix.** Keep the m4 *headroom ratio*, not the m4 *literal*: with a measured 4.8–5.4×
growth, a bound of ~16 preserves ≈3× headroom (as m4 has) and fails exponents ≥ ln16/ln5.37 = 1.66.
Better still, make the bound self-scaling and state it that way: assert
`time(128)/time(16) < 3 * (nodes(128)/nodes(16))` with the node counts read in-test from
`reduce()`'s report (`reachable_nodes` is in the returned dict — measured above), which is stable
across matrix legs and cannot drift if the builder's D/K are ever tuned. Either way, record the
measured N=16/N=128 times and the chosen headroom in §3.3 so the freeze is auditable.

---

## MID-2 — m49's §8.2(i) accessor anchor is satisfied by a degenerate constant map: all three of its clauses pass under `record_id → (one_stage_id, 0)`

**Section**: §10/m49 (`:2845-2862`).

**Detail.** The anchor exists because "the new read-only core accessor is an m49 Implementation
Target in `graphed`, yet every anchor exercising it sat in `graphed-executors`" and "its own
correctness is also never asserted directly". Its three clauses are:

1. every surviving record id maps to a `(reduced_id, member_index)` whose reduced id is **in** the
   compiled output/stage set;
2. the deliberately unmarked branch's record id maps to `None`;
3. one derived node consumed by two non-nominal universes maps to ONE key whose `variation_labels`
   entry carries **both** labels.

An implementation returning `(first_stage_id, 0)` for every live record id and `None` for every
DCE'd one satisfies (1) trivially, satisfies (2) (it must compute reachability anyway), and
satisfies (3) *a fortiori* — under a constant map every key collects every label, so "both labels"
is present. The clauses constrain the map's *type*, not its content.

The real discriminator exists but lives in another repo (`graphed-executors`' single-label
`variation == "jes_up"` anchor, which a constant map would fail by rendering all labels) — which is
exactly the per-repo-coverage argument that motivated this anchor in the first place.

**Suggested fix.** Add one *partitioning* clause that the §3.3 topology makes free and exact: the
record ids of the shared prefix all map to ONE reduced id, and each universe's chain maps to a
reduced id **distinct from every other universe's** — i.e. the map's image over the topology has
exactly `N + 1` distinct reduced ids, matching the `stages == N + 1` shape §3.3 already pins
(measured above: 17 and 129). That kills the constant map and is a genuine mechanism witness for
"keyed on POST-REDUCTION node ids".

---

## MID-3 — §6.4a(2a)'s r17 node-id-equality rule has no discriminating anchor: an object-identity implementation passes every m51 anchor and refuses a legal program

**Section**: §6.4a (`:1705-1711`), §10/m51 (`:3014-3025`).

**Detail.** r17 binds how "the supplied mask IS `graphed.selection(c)`" is decided: **per-label
node-id equality**, with Python object identity only as a fast path — and states the reason
outright: "m51's anchor passes the same object either way, so the freeze cannot disambiguate it and
an implementer would otherwise guess." The rule was bound; the anchor that would discriminate it was
not added. Every m51 bridge anchor still passes the *same object*
(`select=graphed.selection(sel)`), so an implementer who ships `mask is ctx._selection` passes m51
and permanently refuses the legal re-recorded spelling.

Measured against `graphed-latest`: re-recording an identical expression yields a *different* Python
object with the *same* node id (`src * 2.0` recorded twice → node ids `1` and `1`, `a is b` False,
`node_count() == 2`), so the discriminating fixture is one line.

**Suggested fix.** Extend m51's `graphed.selection(ctx)` bridge anchor with a positive control: a
`select=` value that is a **re-recorded equal expression** (a distinct Python object interning to
the same node ids as the mask the context retains) is **ACCEPTED** and round-trips identically. Pair
it with the existing refusal cases so both directions are pinned.

---

## MID-4 — §6.1c's per-OUTPUT MODE (r17) is unanchored: no m50 anchor builds the mixed sibling+axis plan that is the mode field's only reason to exist

**Section**: §6.1c (`:1287-1308`), §10/m50 (`:2882-2960`).

**Detail.** r17 binds: "A plan MAY therefore carry sibling-mode and axis-mode outputs together, so
the **layout records the per-OUTPUT MODE** (sibling / axis) — the information the FRONTEND UNPACKER
needs to choose between `{label: hist}` and a bare histogram per §6.1a/§6.2(i-bis)." Every m50
anchor is single-mode: the equality anchor compares an axis-mode program against its sibling-fill
decomposition (two programs), the scaling anchor pins "the fixture's output count **at 1**", the
(i-bis) shape anchor is one axis-mode histogram, and the declaration/mode-mismatch anchors are about
one histogram. In a single-mode plan the unpacker can infer the shape from the key form alone
(`(output, None)` vs `(output, label)`) or from a global flag, so the mode field can be omitted
entirely and every m50 anchor stays green.

**Suggested fix.** Add to m50 one **two-output mixed-mode plan** anchor: one axis-mode output and one
sibling-mode varied output in the same `plan(...)` call, asserting the result mapping gives a bare
variation-axis histogram for the first and `{label: hist}` for the second, and that the narrowing
helper reads both. (This also exercises `_GroupZero`'s per-slot spec across two different specs,
which §6.1c binds and nothing else reaches.)

---

## MID-5 — m50's target line still demands the design r17 withdrew ("the per-slot value type in the layout and the combine's branch on it")

**Section**: §10/m50 (`:2877-2879`) vs §6.1c (`:1299-1308`).

**Detail.** §6.1c (r17) says explicitly: "**The COMBINE needs no branch** (r17 — r15's 'the per-slot
VALUE TYPE is recorded in the layout and the combine branches on it' asks for something the bound
keying makes unnecessary…)" and replaces it with the per-output MODE. m50's target line still reads
"**§6.1c's AXIS-MODE slot** (r16 — the `(output, None)` keying, **the per-slot value type in the
layout and the combine's branch on it**; …)". The milestone target list is what the test-author and
implementer work from; as written it directs them to build the withdrawn branch and to freeze
around it.

**Suggested fix.** Re-word m50's target to match §6.1c r17: "the `(output, None)` keying, the
per-OUTPUT mode recorded in the layout, and the per-slot spec taken from the fill node" — and drop
"the combine's branch on it".

---

## MID-6 — §6.1d/§6.3's broadcast-seam trigger has an unanchored half: the *contexted-but-unvaried* fill

**Section**: §6.3(2) (`:1602-1608`), §6.1d (`:1378-1379`), §10/m48 (`:2615-2634`, `:2543-2546`).

**Detail.** r16 states the trigger once, deliberately: "the seam is recorded for every weight factor
of a fill that carries a context handle **OR** any `Varied` input; a fill with NEITHER records
byte-identically to today". Two of the three cases are anchored — the "neither" case by §6.3's
golden GIR blob + params key-set equality, the "`Varied` input" case by the manual-broadcast
reference anchor. The **handle-but-no-variation** case (a context with zero registrations, a
per-object value, an explicit per-event `weight=[…]` factor) is anchored nowhere, and it is exactly
the case r16 added the disjunction for. An implementer reading the trigger as "any `Varied` input"
passes §6.3's golden *and* the varied broadcast anchor, and length-mismatches at execution on a
legal contexted program.

**Suggested fix.** Add that program as a third assertion inside m48's existing broadcast anchor in
`graphed-histogram`: a fill from a context with **no** registrations and **no** `Varied` input, on a
per-object value with a per-event explicit factor, produces the manually broadcast reference (and
the seam node is recorded — observable via the fill node's input cone or `Session.node_count()`
delta against the same fill with no handle).

---

## MID-7 — §7.2's new m48 refusal has no positive control bounding its scope; as worded it can be implemented so that unvaried multi-output programs newly raise

**Section**: §7.2 (`:1938-1961`), §10/m48 (`:2423-2428`).

**Detail.** The measured basis is solid — I reproduced both probes against the pinned roots:
`nom, m1, m2, mh = w, w*1.0, w*2.0, w*0.5` record ids `0,1,2,3`, `compile_ir(s, nom, m1, m2, mh)` →
`outputs() == [0, 1, 2]` and `evaluate_ir` returns 3 values; and on the fill path
(graphed-histogram @ `211cbbe`) two `Histogram.fill`s differing only in `weight=[w]` vs
`weight=[w * 1.0]` record fill nodes `2` and `4` and compile to `outputs() == [2]`.

The binding sentence is "after `compile_ir` **the frontend** compares the number of DISTINCT
compiled outputs … against the number of distinct record node ids **it marked** and, on a shortfall,
raises". "The frontend" is unlocated, and the m48 anchor asserts only the refusal
("the program is REFUSED with a message naming the labels"). Nothing pins that the guard is scoped
to *varied* unpacking. An implementer who puts it in `compile_ir`/`aggregate_plan` unconditionally
satisfies the anchor and newly raises on pre-existing unvaried multi-output programs whose outputs
the M4 identity/commutativity rules merge — a silent backward-compat break with no frozen control.

**Suggested fix.** Add the positive control to the m48 §1.2 anchor: an **unvaried** two-output
program whose outputs the optimizer merges (`compile_ir(s, b, b * 1.0)`) still compiles and runs
exactly as today, and state in §7.2 where the guard lives (the varied unpack path — the
`(output, label)` map's owner — not `compile_ir`).

---

## LOW-1 — §7.3 says "the anchor states which" `DurablePlan` construction; m49's anchor bullet does not

**Section**: §7.3 (`:1980-1987`) vs §10/m49 (`:2870-2871`).

**Detail.** §7.3 delegates the choice between the m8 `from_ref` pattern and
`OpSpec.from_callable(plan.process)` to the anchor; m49's list carries only "§7.3 interrupt/resume
byte-identity". The requirement is left with no addressee. (See HIGH-1 for why the choice is
load-bearing rather than cosmetic.)

**Suggested fix.** State the construction in the m49 anchor text itself; delete the "either …
or …" from §7.3 or reduce it to a note about the *user-facing* idiom.

---

## LOW-2 — §2.3e(3)'s "the refusing class is exactly `{gak.join}` at freeze time" is a frozen equality that contradicts the self-repairing rule stated in the same sentence

**Section**: §2.3e(3) (`:788-793`), §10/m48 (`:2568-2572`).

**Detail.** The clause pins the *refusing* membership as an exact set and then says "a future gak
boundary verb arrives with its classification in `src`, which is where the self-repairing rule wants
it". Both cannot hold: a frozen `refusing == {gak.join}` assertion goes red the moment such a verb is
classified. Measured, `gak` currently has 65 public functions in
`graphed.awkward.functions` and `join` (`:18`) is the only boundary verb, so nothing inside m48–m51
trips it — this is a maintenance trap, not a milestone blocker.

**Suggested fix.** Word the floor as containment plus a monotone count — "`gak.join` **is in** the
refusing class" and "the refusing count is ≥ the freeze-time count" — matching the shape already
used for the broadcast class.

---

## LOW-3 — §6.2(ii)'s circularity parenthetical is stale after r17 re-ordered `graphed.labels(h)`

**Section**: §6.2(ii)/m50 declaration anchor (`:2904-2906`).

**Detail.** The anchor warns against reading the expected label list back "from `graphed.labels(h)`
(which §6.2(i-bis) defines **AS** the axis bin set — that comparison would be circular)". After r17,
§6.2(i-bis) defines `graphed.labels(h)` as the axis bin set **re-ordered** to §2.2's rule
(nominal first), so the parenthetical's stated reason no longer matches its own cross-reference. The
guidance (compare against a literally spelled list) remains right, and the m50 (i-bis) anchor
correctly asserts both orders — only the justification is stale, and a test-author reconciling the
two could reasonably conclude the comparison is no longer circular and use `graphed.labels(h)` as
the oracle, restoring the circularity for the *content* half.

**Suggested fix.** Re-word to "…which §6.2(i-bis) derives FROM the axis bin set — so the comparison
would be circular on content regardless of order".

---

## Verified clean (checked, no finding)

For the record, the following were examined under this lens and hold:

- **§3.3 / §5.2a / §5.2c literals** — `stages == N+1`, `reduced_nodes == 2N+2`, the load-bearing
  terminating reduction (34 vs 18 at N=16; 258 vs 130 at N=128) and Δ = K+2 all reproduce exactly;
  §5.2a/§5.2c's *independent hand-built oracle* construction is genuinely independent (not the
  self-derived `delta == len(cone)` trap) and is obtainable pre-implementation.
- **§4.3's extraction mechanism is buildable**: `params["n_axes"]` is recorded on every fill
  (`boost.py:198-212`) and the house pattern for reaching record-time nodes from a frozen test is
  already `s._store.nodes()` (`graphed-histogram tests/frozen/m29/test_multi_weight_fills.py:84,95`).
  The r16 replacement predicate (non-weight input-id prefix identity) does fail a
  `mask_L = mask & g_L` implementation, unlike the withdrawn intersection form.
- **§6.3's params KEY-SET literal** — measured, an unvaried single-weight fill node's params are
  exactly `{"spec", "n_axes", "sampled", "weighted"}`; the r17 replacement of the vacuous
  `"<new key>" not in params` placeholder is correct and non-tautological.
- **§2.3a/c/d discovery rules and their non-vacuity floors** — measured: `dir(Array)` public =
  `['filter','map','node_id','reduce','repartition','session']` with `node_id`/`session` as
  properties (`inspect.isfunction` does not enumerate them, so §2.2's reserved-name anchor really
  does need its own test); `dir(NumpyArray)` = 32 public names; the annotation-wide filter over
  `graphed.__all__` yields exactly the 8 verbs r15/r17 name, all refusing/expanding — so r17's
  naming of `context_of`/`broadcast_like` as the sole *broadcasting*/*eager-metadata*
  representatives is measured-correct; `graphed.awkward.functions` yields 65 functions while the
  package alias yields the wrong six-name set.
- **Fixture buildability of the m48/m49 corpus matrices in `graphed-histogram`** — the corpus
  generates its events synthetically (`make_events()`), so vendoring `graphed_corpus` + the
  reference JSONs needs no data files; `graphed-histogram`'s `dev` extra already carries
  `graphed[awkward,numpy]`, `awkward`, `hist`, `pyarrow`, `graphed-executors`; the read-counting
  `ChunkedSource` the §5.2b witness needs already exists at `tests/frozen/m23/test_group_plan.py:30-44`
  and that directory is on the repo's `pythonpath`.
- **m48's §7.2 schema-absence anchor is hostable in `graphed`** — `Plan`, `ExecResult` and
  `TaskEvent` all live in `python/graphed/core/execution.py:207,220,336`.
- **m50's §9.2 preservation anchors are hostable in `graphed`** — `build_bundle`'s `histogram=` is a
  plain `{name, bins, lo, hi}` dict, not a `graphed_histogram` object, so no `importorskip` skip.
- **§5.3's `| None`** — `read_columns` really does return `None` ("read every column") on
  whole-record consumption or a bare source read (`projection.py:143-147`), so m49's conservative-label
  clause is a real, non-tautological assertion.
- **R0.10a compliance elsewhere** — §6.2's scaling claim is frozen structurally (payload-entry
  count), §6.4c's compression and m50's object-count/wall-clock halves are correctly demoted to
  R0.11 implementer reports, and §6.4g's parquet byte-identity is a same-process comparison rather
  than a committed blob. §3.3 is the only frozen timing gate, and it is declared as such (see MID-1
  for its margin).
- **Freeze-order scoping of the sibling/axis split** — §6.1a, §6.1b, §1.2 and the `.plan()` refusal
  are each scoped so m50's axis mode does not contradict an m48/m49 freeze; §7.2's schema-absence
  anchor is worded over key sets so m49's closure field does not break it; §1.2's rename/IR-byte
  anchor stays true at m49 (a rename changes the closure, not the IR).

---

## Verdict

**DIRTY.** Three HIGH findings, seven MID, three LOW — no BLOCKER. The plan's test architecture is
in good shape overall: the traps it names (§4.3's equal-counts tautology, §5.2a's self-derived delta,
the r0 impact-set-subset wording, §6.3's placeholder params assertion) are all closed, and I found no
*new* tautological anchor of that class. The defects concentrate in two places: (a) r17's own new
scoping — the `DurablePlan` construction (HIGH-1), the milestone-dependent `to_parquet` disposition
(HIGH-2), the node-id-equality rule (MID-3), the per-output mode (MID-4/5) — where a rule was bound
carefully but its anchor was not adjusted to match; and (b) two inherited gaps where a binding rule's
*mainline* case is anchored only by an absence-of-error control (HIGH-3) or not at all (MID-6). MID-1
is independent of r17 and worth fixing on its own merits: the one frozen timing gate in the plan
currently discriminates at roughly a quarter of the margin its M4 precedent has.

A further review round is warranted, but the residue is bounded — none of these findings requires
re-opening an owner-locked decision, and each has a one-to-three-sentence fix.
