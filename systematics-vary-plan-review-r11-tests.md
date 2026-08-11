# systematics-vary-plan review — round 3, TEST ARCHITECTURE lens

**Plan revision reviewed:** r11 (`systematics-vary-plan.md`, 1804 lines, read in full: Part I, all of
PART II §§1–12, §10 milestones m48–m51, Anchors appendix, revision history).
**Lens:** test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
(no wall-clock/size thresholds frozen), determinism-gate compatibility, freeze-order hazards,
traceability, testability-as-stated.
**Date:** 2026-07-30.
**Verification roots used** (all code facts below come from these, never from the workdir submodules):

| Root | Revision | Used for |
|---|---|---|
| `/private/tmp/claude-501/graphed-latest` | `ff7c607` | gak surface, `Array`/`Session`/`execute`, frozen tree + `pyproject`/CI, m4 benchmark precedent, live reduction probe |
| `/private/tmp/claude-501/graphed-histogram-latest` | `211cbbe` | `boost.py` fill/`FillEvaluator`/`_GroupReduce`, frozen dirs, deps |
| `/private/tmp/claude-501/graphed-exec-check` | `201ea42` | executors deps + frozen layout + `m7/adl.py` house pattern |
| `/private/tmp/claude-501/graphed-corpus-latest` | `49650e4` | `analyses/systematics.py`, wheel packaging |
| `graphed-root-prompt.md` | workdir | R0.10 / R0.10a / R0.11 / R22.3 text |

Two live probes were run in a clean venv built from
`graphed-latest/target/wheels/graphed-0.0.1-cp312-cp312-macosx_11_0_arm64.whl` (CPython 3.12.10,
awkward 2.12.0); both are quoted inline where they matter.

**Owner-locked decisions were treated as fixed.** No finding below asks for a different naming,
surface, encoding, attachment point, architecture, or scope.

---

## What I verified clean (stated so the reader knows the lens actually ran on it)

- **R0.10a compliance is genuinely good.** Every scaling/size claim is demoted to an R0.11
  implementer-report measurement with methodology (§6.2 N≈100 wall clock; §6.4c compression;
  m51 representation sizes), and the one frozen wall-clock gate (§3.3) is a *named* carve-out with a
  real precedent: `tests/frozen/core/m4/test_benchmark.py:35-43` already freezes
  `growth < 24.0` over `{1k,2k,4k,8k}` and `test_systematics.py:47` freezes `elapsed < 1.0`. The
  carve-out is defensible and correctly scoped; no other frozen anchor in m48–m51 carries a clock or
  a byte threshold.
- **§3.3 / §5.2a pinned integers reproduce exactly.** I rebuilt the bound builder (source → D=500
  shared prefix → per universe {1 fork op, K=50 chain ops, 1 terminating reduction}, every reduction
  marked as its own output) against `graphed-latest` and measured:
  `N=16 → stages 17, reduced 34`; `N=128 → stages 129, reduced 258`; `Δ(N=1→2) = 52`. Without the
  terminating reduction: `reduced 18 / 130`, `Δ = 51`. The plan's numbers and its "the terminating
  reduction is load-bearing" warning are both correct, and `stages`/`reduced_nodes` are real report
  keys (`src/optimizer/mod.rs:39-42`, `src/lib.rs:448-451`).
- **The four historical vacuity traps stay fixed.** §4.3's equal-counts tautology (now structural),
  §5.2a's self-derived `delta == len(cone)` (now a literal integer bound to a spelled-out builder),
  m51's self-derived `OR(masks) == OR(masks)` (now an eager out-of-graphed reference, the
  `m23/test_group_plan.py:60-66` / `m7/adl.py:156-158` house pattern — both verified present), and
  §6.4g's committed-parquet-blob hazard (now a same-process comparison; the writer-version argument
  is sound). I found no *new* instance of the self-derived-reference shape.
- **Determinism-gate compatibility is clean.** §3.2's anchor is in the strong R22.3 form (fresh
  processes, differing `PYTHONHASHSEED`, byte-identical `compile_ir` output — and `compile_ir`
  really does return a `CompiledGraph` with `.ir`, `execute.py:54-90`); §5.5's content-seeded
  randomness anchor asserts run-to-run byte-identity, never ordering; m49(i) correctly separates
  "fingerprint-exact vs the rounded references" from "run-to-run `array_equal`".
- **Freeze-order hazards were swept and are mostly handled.** No anchor still describes r8-era
  p-form canonical semantics after the r9 switch (the p-form survives only as a *legal input* tag
  and in §9.1's dual parser and §6.4b's carried-over probe fixture — all deliberate). §6.1a is
  explicitly scoped to sibling mode with an instruction not to freeze a rule m50 must contradict;
  §7.2's schema-absence anchor is correctly scoped to KEY SETS so m49's §8.2(i) closure field does
  not detonate it. Two residual hazards below (L1, L2).

Findings follow, most severe first.

---

## HIGH-1 — §6.1d/m48: the already-flattened refusal names a raiser the bound mechanism never reaches

**Sections:** §6.1d (r11 execution-time refusal), m48 anchor "§2.6/§6.1d event-context anchors".

**Detail.** §6.1d binds two things that collide:

1. the ambient weight is delivered "already shaped to the fill's value structure through one neutral
   entry point; **the awkward implementation records `ak.broadcast_arrays`**" (plan :803-806) — i.e.
   the broadcast is a *recorded graph node upstream of the fill*; and
2. "the `FillEvaluator` raises when a weight input's flattened length differs from the axis values',
   with a message naming the ambient weight and pointing at 'pass the value unflattened'"
   (:813-816), frozen by the m48 anchor "the **execution-time** refusal when a per-object fill hands
   in an already-flattened value alongside a per-event ambient weight (§6.1d r11: `FillEvaluator`
   raises on the length mismatch naming the ambient weight)" (:1284-1287).

In the failure case the broadcast node executes first and dies there, so `FillEvaluator` is never
entered. Measured this session (awkward 2.12.0, the version the plan's own probes pin):

```
flat = ak.Array(np.arange(7.0))     # already-flattened per-object value, len 7
w    = ak.Array(np.arange(3.0)+1)   # per-event ambient weight, len 3
ak.broadcast_arrays(flat, w)
  -> ValueError: cannot broadcast RegularArray of size 3 with RegularArray of size 7
ak.broadcast_arrays(jagged_3x?, w)  -> OK (the legitimate unflattened case)
```

The plan is right that there is no *record-time* discriminator (a typetracer has no lengths), but the
execution-time raiser it names is the wrong one: it is the raiser you get in a world with **no**
broadcast seam (there, `FillEvaluator._flat` would hand boost two different lengths —
`boost.py:39-47,60-71`, verified). With the seam, the error is awkward's `ValueError` from the
broadcast op, with no mention of the ambient weight and no "pass the value unflattened" guidance.

A test-author freezing the anchor verbatim writes `pytest.raises(...)` against a message and a site
the correct implementation does not produce; the implementer's only routes are to file a dispute or
to bend the architecture (make the broadcast non-recorded, contradicting §6.1d).

**Evidence.** Plan :789-816 and :1284-1287; `graphed-histogram src/graphed_histogram/boost.py:39-47`
(`_flat`), `:60-71` (`FillEvaluator.__call__`); measured `ak.broadcast_arrays` ValueError above.

**Suggested fix.** Bind the *contract*, not the class: "at execution the varied fill fails with a
graphed error naming the ambient weight and pointing at 'pass the value unflattened'", and bind the
neutral broadcast seam's awkward implementation to wrap its evaluator so the broadcast failure is
translated into that message. Word the m48 anchor over the message contract + execution-time site;
drop the literal `FillEvaluator` naming (or state that the seam's evaluator, not
`FillEvaluator`, is the raiser).

---

## HIGH-2 — m49(i): the 15-reference matrix is pinned to a repo that cannot fill a histogram, and the §5.2b witness is bound to that run

**Sections:** §10/m49 anchor (i); cross-check §10/m48's own fixture analysis.

**Detail.** r11 correctly discovered that **`graphed` cannot host a fill-based corpus matrix**:
it has the 23 vendored references but no `graphed-histogram` in any extra, CI installs `.[dev]`, and
the house pattern is `pytest.importorskip("graphed_histogram")` — so such an anchor "would **SKIP in
CI**, silently discharging the milestone's headline gate" (plan :1170-1185). It applied that finding
to m48 (matrix moved to `graphed-histogram`, plus a bound dependency + reference-vendoring edit) and
to m49(ii) (`graphed-histogram` added to `graphed-executors`' dev extra) — but **left m49(i)
untouched**: "**`graphed`, `tests/frozen/frontend/m49`** — the matrix through the frontend,
fingerprint-exact against the 15 stored references" (:1324-1329), with "**The §5.2b read witness
binds to THIS run**".

I re-verified every fact the m48 analysis rests on, in the same repo m49(i) targets:
- `graphed pyproject.toml:41-48` — `dev` extra carries `boost-histogram>=1.4`, `hist>=2.7`, and no
  `graphed-histogram`; there is no `graphed-histogram` anywhere in the file.
- `.github/workflows/ci.yml:34,57,143` — all three install steps are `pip install -e ".[dev]"`.
- `tests/frozen/preserve/m30/test_producer_cross_seam.py:155` —
  `gh = pytest.importorskip("graphed_histogram")  # separate optional package`.

So m49(i) as written is underdetermined between two very different fixtures, and the
path of least resistance is the one the plan proved is fatal:
(a) `importorskip("graphed_histogram")` → the milestone's headline anchor **and** the §5.2b
single-read mechanism witness silently skip in CI and contribute zero frozen-suite diff coverage;
(b) build the `hist.Hist` driver-side from one multi-output `compile_ir`/`evaluate_ir` (legal in that
repo — `hist` is in `dev`, and a single compile keeps `part_reads == n_partitions` honest), which is
essentially the "materialize-then-fill-eagerly" shape the plan **explicitly rejects one bullet
later** for m49(ii) ("it reproduces the numbers while exercising none of §4.2/§6.1/§6.2", :1341-1342).
Nothing tells the test-author which is intended, and (b) needs an explicit blessing because it reads
as forbidden.

**Evidence.** Plan :1170-1185 (the m48 analysis), :1320-1344 (m49 anchors); `graphed
pyproject.toml:41-48`; `.github/workflows/ci.yml:34,57,143`;
`tests/frozen/preserve/m30/test_producer_cross_seam.py:155`.

**Suggested fix.** Apply the m48 resolution to m49(i) explicitly — one of:
(i) move m49(i) to `graphed-histogram`'s flat `tests/frozen/m49` (after m48 it already has the
corpus dep + vendored references, per the m48 binding), keeping `tests/frozen/frontend/m49` for the
non-fill shift anchors (§3.4, §5.2a/c, §5.3, §5.4, §3.3 lives in `core/m49`); or
(ii) keep it in `graphed` and **bind the driver-side eager-fill form explicitly** — one
`compile_ir` over all 15 label outputs, one `evaluate_ir`, `hist.Hist` filled driver-side —
stating that m49 does not target §4.2/§6.1 (those are m48/m50) so the exclusion in (ii)'s rejection
does not apply here. Either way add "**MUST NOT be guarded by `importorskip`**", the sentence m48
already carries.

---

## HIGH-3 — §2.3e's dynamic "every public gak function preserves the handle" gate is not buildable as stated

**Sections:** §2.3e (drop rule, ":gated by the SAME frozen exhaustiveness test as (c): every public
gak function and every `Array` dunder is asserted to preserve the handle, dynamically enumerated");
m48 anchor "Same dynamic enumeration gates §2.3e context-handle propagation."

**Detail.** §2.3c's *classification* gate is a metadata assertion and is genuinely buildable from
`inspect.getmembers(gak, inspect.isfunction)` — no call needed. §2.3e's gate is **behavioural**: it
must *call* each discovered function with a contexted `Array` and assert the handle survives. The
measured surface makes that unbuildable without a per-function argument fixture the plan never
binds. Measured against `graphed-latest`
(`python/graphed/awkward/functions.py`, 73 `def`s / **65 public**):

- **Two do not take an `Array` first at all**: `apply_correction(payload, name, inputs, evaluator,
  …)` (`:476-482`) and `onnx_inference(payload, inputs, runner, …)` (`:513-519`) — calling them needs
  a correctionlib payload + evaluator and an ONNX payload + runner.
- **Three are eager and materialize**: `to_list` (`:693-698`), `head` (`:732-734`), `sample`
  (`:737-739`) — they return Python objects, so "preserves the handle" is undefined for them and
  calling them requires a real backend and data.
- **Three are metadata-only**: `fields` (`:717`), `type_of` (`:722`), `backend_of` (`:727`) — same
  problem, they return `list[str]`/`str`.
- **One must refuse**: `join` (`:18`), per §2.3c's *refusing* class.
- **Many need extra/typed operands**: `zip(fields: Mapping|Sequence, …)` (`:118`),
  `concatenate(arrays: Sequence)` (`:383`), `where(cond, a, b)` (`:400`), `unflatten(arr, counts)`
  (`:600`), `linear_fit(x, y, axis)` (`:346`), plus `corr`/`covar`/`isclose`/`moment`/`with_field`/
  `unzip` (record-typed input).

So the test needs a name-keyed table of constructor arguments and per-name expected outcomes — which
reintroduces exactly the drift the dynamic rule exists to delete, and breaks the plan's own
"self-repairing" claim: a *new* gak function is fixed in `src` for the classification gate, but for
the propagation gate the frozen test has no arguments for it and must either skip it (silently
vacuous — the failure §2.3c names) or fail with no legal fix (`tests/frozen/**` is read-only, §B.6).

**Evidence.** Plan :466-470, :1263-1272; `python/graphed/awkward/functions.py` — public-name census
run this session (65 public / 73 total), signatures at the lines above; the m24 precedent
(`tests/frozen/awkward/m24/test_interface_parity.py:39-79`) compares *signatures*, never calls.

**Suggested fix.** Split the two gates and bind the propagation one to the **chokepoint**, not the
surface — the plan already measured that every frontend `Array` is built at five `Session` sites
(`python/graphed/session.py:140,168,183,204,242`). Bind: (a) a dynamic classification gate over all
65 (metadata only, as §2.3c already says); (b) a propagation gate that dynamically enumerates
functions **classified `broadcast`/`container-traversing`/`tuple-returning`** and calls only those,
with the argument fixture derived from the classification metadata that lives in `src` (so a new
function's args arrive with its classification, and the frozen test stays untouched); (c) an
explicit statement that `eager-metadata` and `refusing` members are exempt from "preserves the
handle" (they return non-`Array`s or raise), with the exemption list itself derived from the
classification, not hand-written.

---

## HIGH-4 — §6.2/m50: the declaration-contract anchors freeze behaviour of a feature §6.2 leaves optional, and the headline clause is unreachable under the bound path

**Sections:** §6.2 (i)/(ii)/(iii); m50 anchor "**§6.2 declaration contract**".

**Detail.** §6.2(i) binds "**the FRONTEND declares the axis, at FILL time** … from the §6.1d inferred
label set (which IS known at fill time)". Under that path the declared bin set **is** the inferred
label set by construction, so "a label not among the declared bins" **cannot occur** — the
divergence case is instead the separately-bound cross-fill agreement rule. §6.2(ii) then hedges:
"**if** a user-declared axis is supported at all, an exact-set check runs at fill", while §6.2(iii)
speaks as if user-supplied bins definitely exist ("a user-supplied bin ORDER is normalized to
sorted order").

The m50 anchor freezes both hedged behaviours as hard requirements:

> an **undeclared label at fill is a hard error naming it** … ; a declared bin no label reaches emits
> the §2.5 diagnostic; an **unsorted user-supplied bin order** yields the same spec as sorted (§6.2 iii)

If the implementer takes §6.2(ii)'s option and does not support user-declared axes (entirely
conforming), two frozen tests are unimplementable → a test dispute at the worst possible moment. If
the implementer does support them, the anchor is fine — but the plan never says which, and never
names the **opt-in spelling** for axis mode either (no `fill(..., variation_axis=…)` / constructor
flag / `graphed.plan_group(...)` option is bound, and no "spelling pinned at m50 freeze" note appears
here as it does for every other new surface in this plan).

The rest of the m50 declaration anchor is good: the `h.sum(flow=True) == h.sum()` positive control is
a genuinely direct discriminator against the measured silent-overflow behaviour of a non-growth
`StrCategory`, and the cross-fill agreement clause is reachable under the bound path.

**Evidence.** Plan :836-876 (§6.2 i/ii/iii, note the conditional at :866-868), :1373-1380 (the m50
anchor); `graphed-histogram src/graphed_histogram/boost.py:146-150` (`self._spec = spec_of(self)`)
and `:180-212` (`chash = content_hash(self._spec)`, `params={"spec": …}`) — the measured basis for
"fill time", verified.

**Suggested fix.** Remove the hedge: state whether a user-declared `"variation"` axis is supported in
v1. If **yes**, drop "if … supported at all" and keep both anchors. If **no** (the simpler, and the
one §6.2(i) argues for), delete the "undeclared label" and "unsorted user-supplied bin order"
anchors, keep the cross-fill agreement anchor and the `sum(flow=True)` control, and park
user-declared axes in §11. Either way, name the axis-mode opt-in spelling (or add the standard
"exact spelling pinned at m50 freeze" clause) so the test-author can write the fixture.

---

## MID-1 — §2.3c: only "has a classification" is frozen; three of the five classes have no behavioural anchor anywhere in m48–m51

**Sections:** §2.3c; m48 anchor (":the classification test freezes only that every DISCOVERED public
gak function has a classification; the *behaviour* of the `refusing` class is an m49 anchor").

**Detail.** §2.3c binds five behavioural contracts: *broadcast*, *container-traversing*
(`gak.zip`/`concatenate` detect `Varied` **inside** their Mapping/Sequence arguments),
*tuple-returning* (`gak.unzip`/`broadcast_arrays` return a tuple of `Varied`), *eager-metadata*
(answer on the nominal member), *refusing*. Frozen coverage across all four milestones is:
*broadcast* — implicitly exercised by the corpus matrices (which use the `with_field`-shaped
elementwise path); *refusing* — m49's §5.4 anchor; **container-traversing, tuple-returning and
eager-metadata — nothing**. I searched all four milestone anchor lists (plan :1186-1447): no anchor
mentions `zip`, `unzip`, `concatenate`, `broadcast_arrays`, `fields` or `type_of`.

That leaves the plan's own headline failure mode unguarded: a member classified into the wrong
class passes the exhaustiveness gate (which asserts a classification exists, not that it is right),
and the corpus matrices never reach it — the corpus fixture uses `ak.with_field`, not `ak.zip`
(verified: `graphed-corpus src/graphed_corpus/analyses/systematics.py:39-45`). A `gak.zip`
classified *broadcast* would hand the `Varied` object straight into `record_op` and surface as an
`AttributeError` on `.node_id` — invisible until a user hits it.

**Evidence.** Plan :417-433 (§2.3c classes), :1263-1272 (the m48 anchor's explicit scope);
`graphed-corpus …/systematics.py:39-45`; `python/graphed/awkward/functions.py:118` (`zip` takes a
`Mapping | Sequence`), `:687` (`unzip` returns a tuple), `:677` (`broadcast_arrays` returns a tuple).

**Suggested fix.** Add one m48 anchor with a named representative per class: `gak.zip({"pt":
varied_pt, "eta": plain})` returns a `Varied` carrying the labels; `gak.unzip(varied_record)` returns
a tuple of `Varied`; `gak.fields(varied)`/`type_of(varied)` answer on the nominal member. Three
assertions, all cheap, and they turn the exhaustiveness gate from "a classification exists" into "the
classification means something".

---

## MID-2 — m48's per-repo partition still leaves fill-observable clauses inside `graphed`-assigned anchors (no accessor exists for a context's ambient weight)

**Sections:** §10/m48 partition; the §1.2, §2.1-stacking and §2.6/§6.1d anchors.

**Detail.** The r11 partition assigns "§1.1 grammar, §2.x semantics, §2.6 context lineage, §1.2
label-out-of-identity, §3.2 determinism, §7.2 schema absence" to `graphed tests/frozen/frontend/m48`
and "every anchor that needs a fill" to `graphed-histogram`. Three listed anchors straddle that line:

1. **§1.2's dedup half** — "two labels whose members are structurally identical give arena Δ = 0, the
   same node id, and — per §7.2 — **both keys present in the result with ONE evaluated fill**"
   (:1213-1215). The "result" with per-label keys is `_GroupReduce`'s `{label: hist}`
   (`graphed-histogram boost.py:100-122`); it does not exist in `graphed`. The first half (Δ = 0,
   same node id, `compile_ir` over two identical outputs returning one value) is fine in `graphed`.
2. **§2.1 stacking's r11 extension** — "assert the **inherited** shift label's ambient member is
   `old_ambient[L] × factor[L]`" (:1228-1230). A context's ambient weight has **no bound accessor**:
   §2.2/§9.1 expose `labels`/`universe`/`nominal`/`variations` only, and `graphed.variations(ctx)`
   returns "tags and kinds" (+ parsed float), not the factor Arrays — and it lands in **m50**
   anyway. So the assertion is observable only through a fill result → `graphed-histogram`.
3. **The §2.6/§6.1d mega-bullet** (:1279-1302) is a single undivided list mixing pure-frontend
   clauses (tag grammar, no-reserved-names, `graphed.universe`/`labels`/`nominal`, lockstep
   validation, data-context guard, lineage) with unambiguously fill-shaped ones (ambient fill on a
   per-object quantity, manual-broadcast reference, execution-time refusal, divergent-lineage **at
   the fill**, `unweighted=True`). It is exactly the "which anchor is frozen where" gap r11 says it
   closed for the list as a whole.

**Evidence.** Plan :1164-1185 (the partition), :1209-1215, :1220-1230, :1279-1302;
`graphed-histogram src/graphed_histogram/boost.py:100-122` (`_GroupReduce`/`_add_groups` — the only
producer of `{label: hist}`); plan :1115-1119 (§9.1's surface list, `graphed.variations` marked m50).

**Suggested fix.** Either (a) split the three bullets per repo the way the rest of the list is split
— §1.2's dedup half, §2.1's `old_ambient[L] × factor[L]` assertion, and the fill-shaped half of the
§2.6/§6.1d bullet move to `graphed-histogram`, flat `tests/frozen/m48`; or (b) bind a read-only
accessor for a context's ambient weight (`graphed.universe(graphed.weight(ctx), label)`-shaped) in
m48, which makes (2) frontend-observable and is independently useful for §7.4/§8 debugging. (a) is
the lazier fix and needs no new API.

---

## MID-3 — §4.3's structural predicate names no extraction mechanism, and the only bound per-label node API was explicitly withdrawn as the predicate

**Sections:** §4.3; m48 anchor "§4.3 structural selection-invariance, in the r10 binding form".

**Detail.** The bound assertion is "**the selection cone's node ids MUST be identical across all
weight labels**", with r9's impact-set wording explicitly WITHDRAWN as false. But in a weight-only
program the selection is a plain (unvaried) `Array` — there is exactly one selection cone and no
per-label one — so the assertion only has content as "the set of selection-cone nodes reachable from
each label's fill node is the same for every label". Nothing in the plan says how a frozen test gets
either operand:

- per-label fill nodes: §7.2 says "the frontend owns `(output, label) → node id`" but binds no public
  accessor; the reachable route is `h._fill_nodes` (private, `graphed-histogram boost.py:149,209`)
  plus §6.1c's re-bound `_GroupReduce.layout` (also private) to map slot → label;
- the selection cone: `session.walk` exists and takes an `Array` plus handler callbacks
  (`python/graphed/session.py:245-252`), so it can produce a reachable set — but the plan never says
  to use it here (it names `session.walk` only for §3.4), and §3.4's impact API — the one public
  per-label node-set surface — was just deleted from this role.

This is the third revision spent on §4.3's predicate (r1 made it structural, r10 replaced the
impact-set form). Leaving the *extraction* unbound invites a fourth.

**Evidence.** Plan :656-665 (§4.3 incl. the r10 withdrawal), :1206-1208 (the m48 anchor),
:623-629 (§3.4); `python/graphed/session.py:245-252` (`walk`);
`graphed-histogram src/graphed_histogram/boost.py:149` (`self._fill_nodes: list[Array]`), `:100-117`
(`layout`).

**Suggested fix.** Add one sentence naming the mechanism, e.g.: "the anchor computes, per label,
`reachable(fill_node[label])` via `session.walk` and asserts
`reachable(selection_mask) ⊆ reachable(fill_node[label])` with an identical intersection across
labels; `fill_node[label]` comes from the §6.1c layout." (The repaired impact-set form also works and
is public: `impact(L) \ {L's own output node}` must be disjoint from `reachable(selection_mask)` —
that predicate *is* true for a correct implementation, unlike the withdrawn one.)

---

## MID-4 — §2.6c's derived-context re-indexing anchor asserts length only, which passes for a wrongly-indexed weight

**Sections:** §2.6c; m48 anchor "the derived context's ambient weight re-indexed to the derived row
count (§2.6c — **length equality** against a manual re-index)".

**Detail.** The named failure mode (inheriting the parent's un-re-indexed members) is caught by a
length check, but the adjacent and more likely bug is not: re-indexing by the **wrong** mask. Under
§2.6c a derived context can carry per-label row sets (`sel = events[varied_mask]`), so an
implementation that re-indexes every label's ambient member by *nominal's* mask — or by the mask of
whichever label it happened to iterate first — produces arrays of the right length whenever the
per-label counts coincide, and silently mis-weights events. The plan says "against a manual
re-index", so the reference array is already in the test; comparing values instead of lengths is
free.

**Evidence.** Plan :519-537 (§2.6c, incl. per-label re-indexing), :1293-1296 (the anchor).

**Suggested fix.** Change "length equality" to "elementwise equality against the manually re-indexed
reference, **per label**" and keep the varied-mask case (per-label row sets) in the same anchor —
that is the case where a length-only check is weakest.

---

## MID-5 — §2.3e's op-level divergence error has no anchor; only the fill-level one is frozen

**Sections:** §2.3e ("handles on divergent branches are an error **at that op** naming both … the
op-level rule is *early* detection, not the sole raiser"); §6.1d; m48 anchors.

**Detail.** §2.3e binds two raisers. The m48 anchor list freezes only the second: "**divergent-lineage
detection AT THE FILL** (§2.3e/§6.1d: `h.fill(a_from_ctx1, b_from_ctx2)` — handles no op ever
combined — is a hard error naming both contexts)" and, later in the same bullet, "divergent-lineage
fill → hard error". Nothing anchors `a_from_ctx1 + b_from_ctx2` (or `gak.zip`/`where` over two
divergent contexts) raising **at the op**. An implementation that checks only at the fill satisfies
every m48 anchor while leaving §2.3e's early-detection half unimplemented — and the user-visible
consequence is a diagnostic pointing at the fill line instead of the line that actually mixed the
contexts, which is precisely the §A.3 #8 failure this project exists to delete.

**Evidence.** Plan :466-470 (the op-level rule + "the op is not the only raiser"), :1288-1290 (the
fill-level anchor only).

**Suggested fix.** Add one clause to the m48 context bullet: "and divergent-lineage detection **at
the op** — a binary op over Arrays from two divergent contexts raises naming both, at that op — with
a positive control that an ancestor-chain pair unifies silently to the most-derived context."

---

## LOW-1 — m49's §6.1b arity anchor is not scoped to sibling mode, unlike §6.1a which r11 explicitly scoped

**Sections:** §6.1b; §6.2 ("Axis-mode fill-node arity is therefore `1 + |S|`"); m49 anchor
"§2.4/§6.1b structural no-cross-product count (`1 + |S| + |W|` fill nodes)".

**Detail.** r11 correctly hardened the m48 §6.1a anchor with an explicit instruction — "**in SIBLING
mode** … word the anchor so it does not freeze a general rule m50 must contradict" — and §6.1b's
prose carries the same scoping ("again **sibling-mode only**"). The **m49 anchor line** carries
neither: as worded it is a general count that m50's axis mode contradicts (`1 + |S|`). The prose
protects the requirement; the anchor is what gets frozen.

**Evidence.** Plan :737-741 (§6.1b prose), :831-833 (§6.2's `1 + |S|`), :1233-1238 (the m48 §6.1a
anchor with its scoping instruction), :1357 (the bare m49 anchor line).

**Suggested fix.** Copy the §6.1a treatment onto the m49 line: "§2.4/§6.1b structural
no-cross-product count — **in SIBLING mode** — `1 + |S| + |W|` fill nodes (axis mode's `1 + |S|` is
m50, §6.2; word the anchor so it does not freeze a general rule m50 must contradict)."

---

## LOW-2 — m48's `.plan()` refusal is worded over "a varied Histogram" generally, which may over-freeze the weight-only axis-mode case

**Sections:** §6.1c; m48 anchor "§6.1c `.plan()` refusal"; §6.2.

**Detail.** The refusal's stated *reason* is that `_SumFills` sums ALL staged fills into one
histogram and would merge universes (`boost.py:88-98`, verified). In m50's axis mode with
**weight labels only**, the fill collapses into a single evaluator-side loop → one fill node → the
merge hazard does not exist and `_SumFills` would be correct. m48 would have frozen a blanket
refusal. Nothing in §6.2 claims `.plan()` must work in axis mode, so this is speculative rather than
a contradiction — but it is the same class of hazard r11 scoped for §6.1a/§6.1b, and the wording fix
is free.

**Evidence.** Plan :745-758 (§6.1c), :1216-1219 (the anchor), :819-833 (§6.2 axis mode);
`graphed-histogram src/graphed_histogram/boost.py:88-98` (`_SumFills`).

**Suggested fix.** Word the anchor as "`.plan()` on a histogram carrying **more than one staged fill
node with varied labels** raises, naming the group API" (or explicitly "in sibling mode"), keeping
the unvaried positive control.

---

## LOW-3 — §5.3's per-label projection-stats surface is binding but unanchored

**Sections:** §5.3 ("Per-label projection stats are exposed via §3.4 so the read-width cost of a
shift is visible"); m49 anchor "§5.3 projection-union test".

**Detail.** m49 freezes the union-growth behaviour (correct, and a real discriminator: the union
grows by exactly the extra field), but nothing freezes the *exposure* of per-label projection stats.
It is a small surface, and §3.4's own anchor covers impact sets rather than projection widths, so the
requirement can ship unimplemented with every m49 anchor green.

**Evidence.** Plan :695-698 (§5.3), :1355-1358 (m49 anchors: §3.4 impact-set anchor and the §5.3
projection-union test, neither covering the stats).

**Suggested fix.** Either fold it into the §5.3 anchor ("…and the per-label projection stats report
the shifted label's extra column"), or demote the sentence in §5.3 from binding to a Phase-2/§11
note.

---

## LOW-4 — m50's `graphed.variations(ctx)` anchor contradicts the pinned "preservation/docs only" scope of `tests/frozen/preserve/m50`

**Sections:** §10 preamble ("m50's `graphed` half is `tests/frozen/preserve/m50`, **preservation/docs
only**"); m50 anchor "**§9.1 `graphed.variations(ctx)`**".

**Detail.** `graphed.variations(ctx)` is a frontend context-introspection API (per-name tags, kinds,
parsed float values under both parsers) with nothing to do with preservation, yet the only pinned
`graphed`-side directory for m50 is `tests/frozen/preserve/m50`, explicitly scoped to
preservation/docs. The test-author is left choosing between contradicting the stated scope and
creating an unpinned directory — in a repo where §10 says directories are pinned *now* because
duplicate basenames have bitten it before. (I checked the mechanics: this is a bookkeeping
inconsistency only, not a technical barrier — `scripts/run-tests.sh` runs `frontend`/`awkward`
per-milestone and `preserve` per-package, and frozen tests already import across package boundaries,
e.g. `tests/frozen/frontend/m40/*` importing `graphed.awkward`.)

**Evidence.** Plan :1141-1152 (directory pinning), :1395-1399 (the m50 anchor);
`graphed scripts/run-tests.sh:16-24,29` (the suite/split map);
`graphed tests/frozen/frontend/m40/test_noninner_null_key_option.py` (cross-package import precedent).

**Suggested fix.** Either pin `tests/frozen/frontend/m50` for the introspection anchor and drop
"preservation/docs only", or state that `preserve/m50` also hosts m50's frontend-introspection
anchor.

---

## Verdict

**Dirty** — but narrowly, and none of it touches an owner-locked decision.

Four HIGH findings block a clean round: one anchor names a raiser the bound mechanism provably never
reaches (HIGH-1, measured), one milestone's headline anchor is pinned to a repo that cannot run it
and inherits the skip hazard the plan itself documented for the previous milestone (HIGH-2, measured),
one dynamic gate is unbuildable over the measured 65-function surface (HIGH-3, measured), and one
anchor pair freezes behaviour of a feature the requirement leaves optional (HIGH-4). Each has a
local fix — three of them a sentence, one a directory move.

The MIDs are coverage/mechanism gaps of the kind that survive a freeze silently (a misclassified gak
function, a length-only re-index check, an unanchored op-level raiser, an unbound extraction
mechanism); the LOWs are scoping words on anchors r11 already learned to scope elsewhere.

Everything else in this lens is in good shape, and unusually so for a plan this size: the R0.10a
discipline is real and consistently applied, the one frozen clock is a justified carve-out with a
verified precedent, the §3.3/§5.2a literal integers reproduce exactly against `graphed-latest`, and
all four historical vacuity traps the plan names for itself remain closed with no new instance of
the self-derived-reference shape.
