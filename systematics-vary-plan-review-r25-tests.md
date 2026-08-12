# `systematics-vary-plan.md` r25 — review round 17, TEST ARCHITECTURE lens

- **Lens**: test architecture — non-vacuity/discrimination, witness-of-mechanism (R0.10), R0.10a
  (no wall-clock/size thresholds in frozen tests), determinism-gate compatibility, freeze-order
  hazards, requirement↔anchor traceability, buildability of the stated fixtures.
- **Plan revision reviewed**: r25 (6036 lines; the task brief said "~1000 lines" — read in full).
- **Date**: 2026-07-30.
- **Verification roots used** (every code fact below was measured by me in this session):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607` (`git rev-parse --short HEAD`), probes run
    in its own `.venv`
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe` (`git rev-parse --short HEAD`) —
    the revision the plan cites as `graphed-histogram@211cbbe`; probes run in its `.venv`
    (boost_histogram 1.8.0)
  - `/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md` (R0.10 `:196-202`,
    R0.10a `:203-215`, R0.11 `:216-`)
  - Not needed for any finding: `graphed-exec-check`, `uproot5-graphed`, `graphed-corpus-latest`,
    `prior-art/*`, `coffea-workdir`.

Findings are ordered by severity. Nine findings; the plan is in good shape on this lens and most
of what r25 added is correctly anchored — see the verdict for what I checked and found clean.

---

## HIGH-1 — §8.2(i)'s `variation_labels` has no bound PRODUCER, so m49's "carries BOTH labels" clause is either self-derived or unbuildable in the repo §10 assigns it to

**Where**: §8.2(i) (`:3044-3114`), §7.2 (β) (`:2794-2806`), §10/m49 anchor (`:4306-4333`).

**What the plan binds.** §8.2(i) declares `variation_labels` as a field of `_PartitionReduce`
(`:3044-3058`) whose value is a sorted association list from `(reduced_node_id, member_index)` to
that node's labels. §7.2 binds the *transport*: "(β) IS THE HOOK'S RETURN CHANNEL, NOT A CALL-TIME
PARAMETER" (`:2794`) — i.e. the value is computed by **whoever supplies the hook** to
`aggregate_plan` and returned from it. §7.2 r18 names the only bound owner of the label→node
correspondence: "the owner of the `(output, label) → node id` map, i.e. `graphed-histogram`'s
group-plan builder (`plan()`, `src/graphed_histogram/boost.py:256-295`), NOT `compile_ir` and NOT
`aggregate_plan`" (`:2887-2890`).

**The anchor.** §10/m49 places the §8.2(i) anchor in **`graphed`** — "the accessor half in
`tests/frozen/frontend/m49` (a `compile_ir`-shaped program)" (`:4307-4309`) — and its
discriminating clause is:

> "that node maps to ONE `(reduced_id, member_index)` key **whose `variation_labels` entry carries
> BOTH labels**" (`:4326-4328`)

which the plan itself designates as load-bearing: "The extended form is the actual non-vacuity
witness for §8.2's SET-VALUED keying claim" (`:4333`).

**Why it fails.** In a `compile_ir`-shaped program in `graphed` there is no `variation_labels` at
all — no `aggregate_plan` call, no hook, no `_PartitionReduce`. Nor can the anchor reach one
through a *varied* plan in `graphed`: §2.3d bindingly makes `graphed.compile_ir` and
`graphed.aggregate_plan` **refuse** a `Varied` output ("the varied route to a plan is the §6.1c
group API", `:803-807`). The three routes left are all defective:

1. The test calls `aggregate_plan(*per_label_arrays, on_compiled=hook)` with a **hook it writes
   itself** — then the asserted `variation_labels` content is exactly what the test just computed:
   a self-derived comparison, the tautology class §5.2a names ("a self-derived `delta == len(cone)`
   comparison is tautological", `:1492`) and §10/m51's own superset anchor was rewritten to avoid
   (`:4582-4589`).
2. The test reaches for `graphed_histogram.plan()` — which needs
   `pytest.importorskip("graphed_histogram")` in `graphed` (measured basis the plan itself pins:
   `graphed pyproject.toml:29-48` vs CI's `.[dev]`), i.e. a **SKIP in CI**, the
   silently-discharged-gate shape §10 repairs four separate times.
3. The clause is read narrowly as being about the **accessor's** map only. But that map is
   `record_node_id -> (reduced_node_id, member_index | None)` — a *function*, "which it is by
   type" in the plan's own words (`:4332`) — and it carries no labels whatsoever, so under that
   reading the clause cannot witness set-valuedness and the plan's claim at `:4333` is false.

This is precisely the defect class r10/r12/r13 fixed one layer at a time for §8.2 itself ("the
channel it named does not exist", `:3029`; "r11's replacement re-introduced the same defect one
layer down", `:3081-3083`) and r15/r16/r24 fixed for §2.5's diagnostic channel, §5.3's stats verb
and §3.4's impact API: a frozen assertion is written through a surface that no bound production
code produces.

**Suggested fix** (either, not both):
- Move the BOTH-labels clause into `graphed-histogram`'s flat `tests/frozen/m49`, where a real
  `gh.plan({...})` over a varied program produces `variation_labels` through the bound owner, and
  leave `graphed`'s `frontend/m49` half asserting only the accessor's record→reduced map (dropping
  the `:4333` set-valuedness claim from that half); **or**
- bind a `graphed`-side PRODUCER — a read-only verb composing a `{label: record ids}` map (§3.4's
  own shape) with the m49 record→reduced accessor into the §8.2(i) association list, listed in §9.1
  with "exact spelling pinned at m49 freeze" like every other new surface — and word the anchor
  over it, so the labels the assertion reads are produced by src, not by the test.

---

## MID-1 — r25 made `sample=` a first-class operand of §6.1d's unification/divergence check and no anchor exercises it

**Where**: §6.1d (`:1978-1992`), §10/m48 (`:3981-3982`, `:3908-3928`).

r25 added `sample=` to the fill's binding unification enumeration:

> "the fill runs the same most-derived unification and divergence check across all axis values, all
> explicit weight factors, **`sample=`** and the winning context's ambient weight (**`sample=`
> added r25** …)" (`:1981-1983`)

with the rationale that "`sample=` is the one input nothing upstream catches — it dies at execution
with a length message about the wrong thing, or silently samples the wrong universe's rows when the
counts coincide, the §2.5 confidently-wrong class" (`:1988-1992`). r25 also states that "An
ancestor-context `sample=` is re-indexed like any other ancestor VALUE" (`:1991`).

Neither half has an anchor. Measured over §10's whole milestone block (`:3273-4773`), every
`sample=` mention is in the fold-order anchor (`:3908-3928`) or m50's sample-only-label anchor
(`:4413-4425`), and both build `sample=` from **one** context. m48's divergence anchor is worded
over axis values only — "`h.fill(a_from_ctx1, b_from_ctx2)` — handles no op ever combined"
(`:3981`) — and m48's re-indexing anchor is `h.fill(events.MET.pt, sel.MET.pt)`, again two axis
values (`:4003`). An implementation that unifies over `args` + `weights` and leaves `sample`
untouched — which is exactly what today's code shape invites, since `fill` type-checks `args` and
`weights` and appends `sample` with no check (`graphed-histogram src/graphed_histogram/boost.py:
160-178`, cited by the plan at `:1987-1988`) — passes every m48–m51 anchor while violating the
binding sentence, and its failure mode is the silent one the clause was added to prevent.

**Suggested fix**: extend m48's divergent-lineage-at-the-fill anchor with a third assertion —
`h.fill(a_from_ctx, weight=[w_from_ctx], sample=s_from_divergent_ctx)` raises the divergence error
naming both contexts — and add an ancestor-context `sample=` to the link-kind-(1) re-indexing
fixture (both live in `graphed-histogram`'s flat `tests/frozen/m48` under §10's "needs a fill ⇒
`graphed-histogram`" rule, `:3424-3426`). Both need the `Mean`/`WeightedMean` storage pin r22
already applies to the fold-order fixture (`:3918-3925`) — I re-measured in
`graphed-histogram-latest`'s venv (bh 1.8.0) that `Mean()` and `WeightedMean()` accept `sample=`
*and* `weight=` together on a two-axis histogram, so the same fixture shape carries it.

---

## MID-2 — §2.3d r25's `graphed.numpy` disposition gate is absent from §10/m48's anchor bullet, the skeleton the test-author works from

**Where**: §2.3d (`:912-930`), §10/m48 §2.3d bullet (`:3682-3724`, discovery rule at `:3687-3690`).

§2.3d r25 binds new m48 behaviour: "`graphed.numpy`'s public module verbs are in scope too, and the
gate runs PER IDIOM PACKAGE" (`:912`), classifying the four `*_like` verbs and `apply_gufunc` as
*broadcast* and `project` as *expanding*, and requiring "m48's gate runs the identical dynamic
enumeration over `graphed.numpy.__all__`, in the same repo and the same anchor, with the same
containment floor" (`:928-930`).

I verified the discovery claim exactly (in `graphed-latest`'s `.venv`, enumerating each module's
`__all__`, keeping `inspect.isfunction` members any of whose parameter annotations mentions
`Array`):

```
graphed: ['aggregate_plan','apply','join','join_plan','pack_key','read_columns','repartition','shuffle_plan']
graphed.numpy (22 names in __all__): ['apply_gufunc','empty_like','full_like','ones_like','project','zeros_like']
```

But §10/m48's §2.3d anchor — "One table-driven test in `graphed`'s `tests/frozen/frontend/m48`,
driven by the §2.3d **discovery rule** (dynamic over `graphed.__all__`, filtered to
`inspect.isfunction` members ANY of whose parameter annotations mentions `Array`, **UNION the named
floor list** … and MINUS `graphed.vary`)" (`:3687-3708`) — never mentions `graphed.numpy`. §10 is
declared "the acceptance skeleton the test-author starts from" (`:3346`), so a suite written from
it freezes only the `graphed.__all__` enumeration and the six numpy dispositions ship as m48 source
with **zero frozen-suite diff coverage** — the DoD argument the plan itself uses at `:850`, `:1795-
1797`, `:3404-3408` and `:4650`. The failure this leaves open is the one §2.3d r25 names: a
numpy-idiom user handing a `Varied` to `gnp.full_like` "reached NO bound behaviour" (`:918-919`).

I also checked the obvious freeze-order hazard and it is **clean**: `graphed.numpy`'s own
`to_parquet` is *not* in `graphed.numpy.__all__` and its first parameter is annotated `Any`
(`(array: 'Any', destination: 'str', …)`), so the m48 numpy gate cannot discover the verb whose
disposition §6.4f changes at m51 — symmetric with §2.3d r18's treatment of awkward `to_parquet`.

**Suggested fix**: add the second enumeration to §10/m48's §2.3d bullet in one clause — "plus the
identical enumeration over `graphed.numpy.__all__`, whose discovered members carry the §2.3d r25
classifications (`*_like`/`apply_gufunc` broadcasting, `project` expanding), under the same
containment floor (non-empty, ≥ the freeze-time count, never an exact set)".

---

## LOW-1 — m51's numpy-backend refusal anchor has no pinned directory, and the only `graphed` directory §10 pins for m51 is in the wrong package subtree

**Where**: §10 header (`:3278-3279`), m51 anchor (`:4766-4767`).

§10 pins `graphed`'s m51 home as `tests/frozen/awkward/m51` and justifies directory pinning by that
repo's per-package partitioning (`:3275-3282`). m51's last-but-two bullet reads: "ROOT half:
`graphed_write` gains IR evaluation … with the same round-trip anchor; **numpy-backend refusal
test (§6.4f)**" (`:4766-4767`) — grouping a `graphed`-side numpy-idiom anchor under the uproot
half, with no directory of its own.

Measured in `graphed-latest`: the frozen tree has a distinct `tests/frozen/numpy` subtree and
`scripts/run-tests.sh:16-25` runs it as its own suite (`"numpy:tests/frozen/numpy
tests/extra/numpy"`), with `SPLIT_PKGS="frontend numpy awkward"` at `:30`. The source under test is
`python/graphed/numpy/io.py` (the plan's own anchor row, `:4901`). Putting a numpy-idiom refusal
anchor into `tests/frozen/awkward/m51` crosses the package partition §10 exists to respect, and
leaving it unpinned re-opens the per-file basename hazard §10 binds at `:3303-3309`.

**Suggested fix**: pin `graphed tests/frozen/numpy/m51` for that one anchor (unique basename per the
same rule) and move the bullet out of the ROOT-half line.

---

## LOW-2 — m48's §2.1 stacking anchor is spelled with the `Varied[label]` subscript §2.2 deleted

**Where**: `:3596`, against §2.2 (`:628-630`).

The r25 strengthening of the stacking anchor states the assertion as:

> "the assertion reads `graphed.weight(sel2)[jes_up] == old_ambient[jes_up] × factor[jes_up]["jes_up"]`" (`:3596`)

§2.2 binds the opposite for that syntax: "String subscription `v["pt"]` is **field access**
(broadcast per §2.3a, Array-coherent), **NEVER label lookup** — r5's `[label]` indexing collided
with awkward's string-getitem field access and is removed" (`:628-630`). A test-author transcribing
the anchor literally therefore records a `field` op named `"jes_up"` (the exact hazard §2.2's
reserved-name rule is built around, `:676-681`) instead of extracting a universe. The nesting makes
it worse: `factor[jes_up]` is not "the factor's `jes_up` member" — `jes_up` is *new to the
container*, so under §2.1 r24's two-level rule the operand is the container's `"nominal"` member,
then that member's own `jes_up`, i.e. `graphed.universe(graphed.nominal(factor), "jes_up")`.

This is the same mid-freeze-discovery service m48 already pays for `gak.full_like`,
`stable()`-rounding, `h.axes.name` and the pt-cut jets.

**Suggested fix**: respell the anchor in the bound surface —
`graphed.universe(graphed.weight(sel2), "jes_up") == old_ambient_jes_up * graphed.universe(
graphed.nominal(factor), "jes_up")` — or state once that `x[L]` is prose notation for
`graphed.universe(x, L)` throughout §§2.1/2.4.

---

## LOW-3 — r25's `Varied`-target class-pairing rule is exercised by no m48 anchor

**Where**: §2.2 (`:550-554`), §10/m48 stacking anchor (`:3582-3620`).

r25 bound the open half of §2.2's per-idiom container rule: `graphed.vary(x, …)` returns the
container class paired "with `type(graphed.nominal(x))` when `x` is ALREADY a `Varied` (r25 —
§2.1(a)'s target is `Array | Varied` and stacking on a loose container is public, for which
`type(x)` IS the container class and the pairing rule had no defined answer)" (`:550-554`).

Reading every m48 anchor that calls `graphed.vary`, the target is always an `Array` or a context:
`graphed.vary(events.Jet, "jes", up=j_up, …)` (`:3816`, `:4044`, `:3773`), the weight/shift forms on
contexts (`:3586-3599`, `:4078`). §10's stacking bullet opens "`vary` on a target that already
carries variations…" (`:3583`) without saying what kind of target, and its only elaborated case is
the r11/r25 **context** extension. So a conforming suite can freeze the milestone without ever
constructing `graphed.vary(<a Varied>, …)`, leaving both r25's pairing branch and §2.1(a)'s
"inherited members pass through unchanged" for the loose form unwitnessed.

**Suggested fix**: one clause on the stacking bullet — "the base case's target is a LOOSE `Varied`
(§2.1a), and `type()` of the result is the container class paired with `type(graphed.nominal(target))`
(§2.2 r25); the r11 extension's target is a context."

---

## LOW-4 — m51's manifest levels assertion has no bound serialized shape for a field-scoped level

**Where**: m51 manifest anchor (`:4728-4737`), §6.4e (`:2628-2631`), §6.4a key grammar
(`:2265-2296`).

r25 rightly repaired the manifest anchor to a literally spelled expected KEY SET and added "one
assertion that the levels entry's **value** equals the set of levels the fixture supplied through
`select=`" (`:4729-4731`). But the `select=` key space is heterogeneous by §6.4a: level 0 is the
bare int `0`; a level-k ≥ 1 entry is **field-scoped**, `("Jet", 1)` (r22, `:2270-2273`), *except*
where the level-k structure is the record's own, which takes the bare `k` (r24, `:2273-2287`). The
manifest is serialized into parquet key-value metadata "with SORTED keys" (`:2679-2681`), and a
`(path, depth)` tuple has no JSON-native rendering. The anchor's two named cases even span both key
spaces — "both levels for the object-migration item" (the multi-field record, `("Jet", 1)`,
`:4598-4601`) and `{0, 1}` for r25's new bare-key round-trip item (`:4602-4606`).

So the test-author must invent the serialized form of a field-scoped level and freeze it read-only —
the "unwritable as stated" class r15 repaired for §2.5's channel and r16 for §5.3's verb.

**Suggested fix**: bind the levels entry's serialized shape in §6.4e in one sentence (e.g. a sorted
list whose elements are either an integer depth or a two-element `[field_path, depth]` array, with
`field_path` the `_`-flattened path §6.4b already binds), "exact spelling pinned at m51 freeze".

---

## LOW-5 — m49's §3.4 impact fixture is spelled only in raw-`GraphStore` terms while §3.4's verb consumes per-label output `Array`s

**Where**: m49 §3.4 anchor (`:4264-4284`), §3.4 (`:1359-1382`), against the §5.2a/§5.2c precedent
(`:1493-1497`, `:1535-1555`).

r24 re-pinned this fixture with a measurement stated entirely as raw core calls — "`src`;
`k = add_op("scale",[src])`; `nom = add_op("sel",[src])`; `up = add_op("shift",[src,k],{"d":"up"})`
…" (`:4274-4277`). §3.4's verb, however, is "a read-only `graphed` module verb over the per-label
output Arrays" (`:1365-1367`), which a raw `GraphStore` cannot supply (it has no `Session`, no
`Array`s and no labels). §5.2a and §5.2c each needed an explicit correction for exactly this —
"**The witness MUST be built through the public `graphed.vary` surface** (r14): §3.3 tells the
author to replicate `tests/frozen/core/m4/test_benchmark.py`, which builds with the raw
`graphed.core.GraphStore` API … so an author following §3.3 can hit every pinned integer while
witnessing only `GraphStore::intern`" (`:1493-1497`) — and §3.4's anchor carries no such sentence,
while the r24 text invites the raw spelling. (The frontend program exists and is cheap: `k = src *
2.0`; `up`/`down` two different expressions over `(src, k)`; `graphed.vary(src_arr, "jes", up=…,
down=…)` — nominal is the target, so `k ∉ reachable(nominal)` and `impact(up) ≠ impact(down)` both
hold.)

**Suggested fix**: add the same one-liner §5.2a/§5.2c carry — "built through the public
`graphed.vary` surface; the raw-`GraphStore` construction above is the existence measurement, not
the fixture."

---

## LOW-6 — §6.2(3)'s "no `boost_histogram` import in `graphed` proper" is binding, unanchored, and not marked knowingly-unanchored

**Where**: §6.2 (`:2185-2194`).

The plan's convention is to mark every binding rule it deliberately leaves without a frozen witness,
so a reviewer does not read it as a coverage gap — done for §6.1d's reindex ordering (`:1950-1959`),
§6.4e's no-private-import rule (`:2669-2677`), §7.2's "MUST NOT compile a second time" (`:2847-2852`)
and §1.1's `"1e1000000000"` (`:296-298`). §6.2(3) is the same shape (a static, import-level
constraint no behavioural anchor discriminates: `boost-histogram` is in `graphed`'s `dev` extra, so
an implementation that imports it inside `graphed.labels` is green on every gate) and is not marked.

**Suggested fix**: mark it knowingly UNANCHORED on the §6.4e footing, and optionally note the same
`tests/extra` static assertion §6.4e offers (the module's source contains no `boost_histogram`
import).

---

## What I checked and found CLEAN

Recorded so the next round need not re-derive it. Every item below was measured in this session.

- **R0.10a (category c) — clean.** Scanning §10 (`:3273-4773`) for timing/size predicates yields
  exactly one frozen wall-clock gate, §3.3's ratio bound, which the plan declares "the ONE frozen
  wall-clock gate in m48–m51, and it is a deliberate, named carve-out to R0.10a" (`:1351-1355`). I
  read the cited precedent — `graphed-latest tests/frozen/core/m4/test_benchmark.py` — and it is
  indeed a frozen ratio gate (`growth < 24.0`) plus an absolute `elapsed < 1.0` budget, so the
  carve-out is precedented and §3.3 copies only the *ratio* half. Every other performance claim
  (§6.2 scaling, §6.4c compression, §7.2's compile count) is explicitly demoted to R0.11
  implementer-report measurements (`:1245-1261`, `:4438-4535`, `:4710-4720`).
- **§7.3's interrupt/resume byte-identity (a hypothesis I tested and falsified).** I suspected the
  same defect §5.5a's r15 repaired — float-combine regrouping making byte-identity red against a
  correct implementation. Measured: `run_resumable` collects `(idx, partial)` pairs from *both* the
  journal and fresh execution (`python/graphed/checkpoint/runner.py:88,101,116`) and
  `_reduce_partials` folds them `sorted(partials, key=lambda kv: kv[0])` — "deterministic order: by
  task index, so an interrupted+resumed run reduces in the same order as an uninterrupted run"
  (`:150-158`). Byte-identity is safe for float payloads here. **No finding.**
- **The property-classification gate (§2.2 r19 / §10 r19-r20) is exactly right.** Measured against
  `graphed-latest@ff7c607` on a 1-D numpy source (`gnp.ones(s, (5,))`): `dtype`/`ndim`/`shape` →
  `Session.node_count()` delta **0**; `T` → delta **1** and returns a `NumpyArray`. On a 2-D source
  `gnp.ones(s, (4,3)).T` raises `GraphedTypeError: ill-typed op 'transpose' … displacing the
  partitioned axis 0` — so §10's r20 pin of the fixture to a 1-D source is load-bearing and correct.
  The discovered sets are as claimed: `Array` public = 6, `NumpyArray` = 32 (26 extra); properties
  `['node_id','session']` vs `['T','dtype','ndim','node_id','session','shape']`; `isfunction`
  methods 4 vs 26.
- **The `sample=` storage pins (§6.1b r21, §10 r22) are correct and sufficient.** bh 1.8.0 in
  `graphed-histogram-latest`'s venv: `Mean()` and `WeightedMean()` both accept `sample=` *and*
  `sample=`+`weight=` on a two-axis fill, so m48's four-way fold anchor is buildable on either. I
  also verified the axis-mode path end-to-end: a `StrCategory` with `__dict__["name"]="variation"`
  alongside a `Regular` axis on `Mean()` storage round-trips `spec_of`→`zero_of` as
  `[None, 'variation']`, the zero histogram adds to a filled one, and `h[{1: ax.index('jes_up')}]`
  slices — i.e. m50's (i-bis) and sample-only-label anchors are constructible as written.
- **Freeze-order sweep (category e) — clean.** Every anchor a later milestone must contradict is
  scoped at its own site: §6.1a/§6.1b/§1.2's m48 anchors are "in SIBLING mode"; `to_parquet` is out
  of m48's §2.3d table entirely and enters *accepting* at m51; every §2.3d/§2.3e floor is a
  containment floor plus a monotone count, never an exact set; m48's `.plan()` refusal is worded
  over the disjunction and (r25) explicitly *not* over the spec comparison, which has no
  m48-constructible fixture; m49's arity anchor is sibling-scoped against m50's `1 + |S|`. I found
  no surviving r8-era (p-form-canonical) semantics in any anchor: m48's grammar anchor freezes the
  r9 e-form canonicalization with p-tags as *legal identifier tags* whose numeric-equal pairs are
  rejected in-family (`:4086-4139`), matching §1.1.
- **Determinism-gate compatibility (category d) — clean.** m48's §3.2 anchor, m49's plan-byte
  anchor and m51's manifest-determinism anchor are all "two fresh processes under differing
  `PYTHONHASHSEED`" (R22.3 form); §8.2(i)'s sorted-tuple binding and §6.4e's sorted manifest keys
  close the two measured seed-dependence holes; §5.5a's partition-invariance witness compares
  per-label smeared values and selection masks rather than a weighted float histogram, which is the
  right compared quantity.
- **m23 backward compatibility** (load-bearing for §6.1a's slot-key scoping): verified literally —
  `graphed-histogram tests/frozen/m23/test_group_plan.py` indexes `SequentialRunner().run(gh.plan(
  {...})).value` by bare output name (`out["hi"]`, `out["lo"]`, `grouped["0"]`, `zero["hi"]`), so
  §6.1a's "an output NO variation reaches keeps today's BARE `output_name` key" is what keeps that
  frozen suite green.

---

## Verdict — DIRTY (one HIGH, two MID, six LOW)

The suite architecture is, on the whole, unusually well developed for a plan this size: the
non-vacuity floors, containment-not-equality floors, oracle-vs-literal discipline, per-repo anchor
partitioning and R0.10a carve-out are all sound, and I could not break the four headline gates
(m48/m49 corpus matrices, m50 axis equality, m51 round-trip) on vacuity grounds.

The blocking item is **HIGH-1**: the one clause the plan itself designates as the non-vacuity
witness for §8.2's set-valued keying is written through a structure (`variation_labels`) that no
bound production code produces in the repo and program shape §10 assigns it to — so as frozen it is
either a self-derived tautology, an `importorskip` SKIP, or an assertion about a map that carries no
labels at all. **MID-1** and **MID-2** are both "new r25 binding behaviour, zero frozen coverage" of
the class this plan repairs consistently elsewhere; each is a one-clause fix. None of the findings
touches an owner-locked decision, and none requires re-opening a settled design choice.
