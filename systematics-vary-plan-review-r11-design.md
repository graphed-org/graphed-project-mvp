# systematics-vary-plan r11 — review round 3, DESIGN SOUNDNESS lens

- **Lens:** design soundness (is PART II a coherent, implementable specification? contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  violations, milestone-boundary consistency).
- **Plan revision reviewed:** r11 (`systematics-vary-plan.md`, 1804 lines, read in full including
  Part I, every PART II section, §10 milestones, the Anchors appendix and the revision history).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts below come from these, never from the stale
  submodules in `/Users/lgray/vibe-coding/graphed-workdir`):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, ff7c607)
  - `/private/tmp/claude-501/graphed-histogram-latest` (211cbbe)
  - `/private/tmp/claude-501/graphed-corpus-latest` (49650e4)
  - runtime probe: `boost_histogram 1.8.0` in the `graphed-histogram-latest` environment
    (the plan's own StrCategory probes are recorded at 1.7.2 — noted where it matters).
- **Owner-locked decisions** (naming, functional surface, e-form canonical, context attachment,
  record-time expansion + interning, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2
  pull-in) were treated as fixed; nothing below asks for a different choice, only for internal
  consistency in how a locked choice is specified.

Findings are ordered by severity. Every one carries evidence I read or ran myself in this session.

---

## HIGH-1 — §8.2(i): the label-transport map is keyed on post-reduction node ids, and **no channel produces them** (the r10 defect, one layer down)

**Section:** §8.2(i), §8.2(ii), §3.4, §7.2; m49 anchor "cross-process labeled StageError".

**Detail.** r10 withdrew r9's transport sentence because "the channel it named does not exist". r11's
replacement re-introduces the same class of defect: it binds `variation_labels: tuple[tuple[int,
frozenset[str]], ...]` "keyed on **POST-REDUCTION node ids** taken from the same `compile_ir` call
that produced the shipped `ir`", explicitly rejecting record-time ids because "DCE compacts and
remaps". But the frontend has no way to obtain a post-reduction id for any node:

1. `CompiledGraph` carries **only** `ir: bytes` and `source_names: tuple[str, ...]` — no remap, no id
   table (`graphed-latest/python/graphed/execute.py:36-45`; `compile_ir` at `:54-80` returns exactly
   that).
2. The PyO3 surface exposes no mapping. I enumerated every `#[pymethods]` entry in
   `graphed-latest/src/lib.rs`: `add_source/add_op/add_reduction/add_external/add_exchange/add_join/
   mark_output/node_count/to_dot/serialize/deserialize/nodes/outputs/reduce/reduce_incremental/
   reduction_report` (+ `IncrementalReducer.step/watermark/total_work/canonical_count/finalize`).
   The `remap` vector exists only inside Rust (`src/optimizer/mod.rs:101-114`, `:135-151`) and is
   never returned; `reduction_report` returns a `HashMap<String, usize>` of counts
   (`src/lib.rs:403-416`, `report_to_map` `:445`).
3. Even if a mapping existed, **most varied nodes have no post-reduction id at all**: fusion collapses
   a universe's chain into ONE `Stage` node whose members are inlined at evaluation
   (`execute.py:110-117`, `kind == "stage"` evaluates `nd["members"]` inline). The plan's own §3.3
   measurement is the proof: N=128 universes × 50 chain ops reduce to **129 stages / 258 nodes**.
4. §8.2(ii) additionally requires shipping "the per-node provenance the map keys alongside", and
   provenance is keyed by **record-time** ids (`Session._provenance`, `session.py:30`, populated in
   `record_op` at `session.py:141-166`) — so it needs the same non-existent mapping.

Consequence: m49's headline anchor ("a failure raised inside the `jes_up` universe on a worker
re-raises driver-side carrying `variation == "jes_up"` AND the user's analysis line") is bound to a
mechanism that cannot be built without new `graphed-core` Rust/PyO3 work that the plan neither scopes
nor lists as an m49 target (§3.1 says "no Rust IR variant, no serialize tag, no optimizer change is
added for variations", and m49's targets are §3.3/§3.4/§5/§7/§8 with no core surface named).

**Suggested fix.** Either (a) scope a read-only core addition explicitly as an m49 Implementation
Target — a `reduce(...)`/`compile_ir` accessor returning `record_id -> reduced_id | None` plus, for
fused nodes, `record_id -> (stage_id, member_index)` — and state that it is a *read-only accessor*, not
an optimizer/IR change, so §3.1 still holds; or (b) re-bind the transport to the one id space the
frontend provably owns: the **output** positions (`store.outputs()` order is the deduped
first-occurrence order of the requested ids, `src/store.rs:147-156` + `execute.py:126`), attributing a
worker failure to the label(s) of the output(s) whose evaluation raised, and state the coarser
granularity honestly. Whichever is chosen, the plan must show the measured channel, as it did for
§2.3e and §7.2.

---

## HIGH-2 — §6.4a: the bound entry check provably cannot refuse the silent-corruption case the m51 anchor names as its positive control

**Section:** §6.4a ("The 'record is pre-selection' precondition is a DECIDABLE entry check"), m51
anchor "Entry check (§6.4a r11)".

**Detail.** r11 replaced the undecidable "a record expression that already embeds a `Varied`
selection" refusal with: "at entry the writer checks that every **per-label member's offsets equal
nominal's** at every level it will store … One predicate, one error message, and it catches the
embedded-selection case and the multiplicity-changing case together."

That claim is false for the case the plan itself calls "the case that actually corrupts data". Take
the plan's own example: `sel = events[nominal_mask]` (a **non-varied** mask), then
`to_parquet(sel.Jet, select=varied_mask)`.

- If `events.Jet` is unvaried, `sel.Jet` is a plain `Array`: the predicate quantifies over per-label
  members and is **vacuously true**.
- If `events.Jet` *is* JES-varied, every member of `sel.Jet` is that member masked by the **same**
  `nominal_mask`, so all members share nominal's offsets at every level — the predicate **passes**.

In both cases the writer proceeds and applies a superset mask built in the parent's row space to a
record already reduced to the nominal-selected rows. The predicate is a *within-record, across-label*
comparison; the corruption is a *record-vs-mask row-space* mismatch, which it never inspects. The same
hole swallows the chained-context case that §6.4a's own bridge creates: `graphed.selection(sel2)` for
`sel2 = sel[mask2]` returns a mask in `sel`'s row space, while the plan's canonical spelling writes
`events.Jet` (root row space) — again passing the offsets predicate.

The m51 frozen anchor pairs the predicate with this exact positive control ("a record carrying a
NON-varied embedded selection … is refused, not written on mismatched rows"). A test-author freezes
it; an implementer implements the bound predicate; the test fails → dispute and churn, on the last
milestone.

**Suggested fix.** Keep the offsets predicate for the multiplicity case (it is right for that), and
add the missing one: **row-space agreement between `record` and every `select=` level** — bind it
structurally, not numerically, since the frontend has it for free under §2.6b lineage (`record`'s
context and the mask's parent context must be the same context object / the mask must be the
selection that derives directly from the context the record was read from), with a runtime row-count
equality as the belt-and-braces check. Then re-word the m51 anchor so each positive control names the
predicate that decides it.

---

## HIGH-3 — §6.2(ii) makes user-declared axes OPTIONAL while three of m50's four declaration-contract sub-anchors presuppose them (and today's `fill` cannot accept one)

**Section:** §6.2(i)/(ii)/(iii); m50 anchor "§6.2 declaration contract".

**Detail.** §6.2(i) binds "**the FRONTEND declares the axis, at FILL time** … from the §6.1d inferred
label set (which IS known at fill time)". Under that rule **no label can ever be undeclared** — the
declared bin set *is* the inferred label set, by construction. §6.2(ii) then says "**if a
user-declared axis is supported at all**, an exact-set check runs at fill: a label not among the
declared bins is a hard error …, and a declared bin no label reaches is a diagnostic", and (iii)
normalizes a "user-supplied bin ORDER".

The m50 frozen anchor requires all of it: "an **undeclared label at fill is a hard error naming it**
…; a declared bin no label reaches emits the §2.5 diagnostic; an unsorted user-supplied bin order
yields the same spec as sorted". Three of those four sub-anchors are only reachable through a
user-declared axis, i.e. through a feature §6.2(ii) leaves conditional. An implementer who reads
§6.2(i) as the binding rule (it is the one stated unconditionally) ships no user-declared path and
fails the frozen suite.

The conditional is not academic — a user-declared axis is **not fillable today**: `Histogram.fill`
requires one array per axis (`graphed-histogram-latest/src/graphed_histogram/boost.py:160-161`,
`if len(args) != len(self.axes): raise TypeError(f"this histogram has {len(self.axes)} axes; fill got
{len(args)} arrays")`), so a histogram constructed with a `"variation"` StrCategory axis rejects the
user's N-array fill before anything else happens. Supporting it is real work (an arity carve-out for
the variation axis) that the plan neither names nor scopes.

**Suggested fix.** Decide it, don't leave "if … at all": either (a) frontend-declared only — delete
§6.2(ii)/(iii) and cut the three user-declaration sub-anchors from m50, keeping only the cross-fill
agreement anchor (which IS reachable under (i)); or (b) support user declaration — make it
unconditional, bind the `fill` arity carve-out as an Implementation Target, and say which wins when a
user-declared bin set and the inferred label set disagree (the exact-set error).

---

## HIGH-4 — §2.3's dispatch enumeration omits the module verbs that consume `Array`s, and `Varied`'s field-access `__getattr__` turns their duck-typed reads into silently recorded ops

**Section:** §2.3(a)/(d), §2.5.

**Detail.** §2.3(d) is titled "Module verbs and sinks" but classifies exactly two verbs
(`graphed.join`, `graphed.repartition`) plus `Histogram.fill`. Measured, `graphed`'s public surface
exports several more `Array`-consuming entry points (`graphed-latest/python/graphed/__init__.py:8-25`
and `__all__` `:27-58`): `apply`, `compile_ir`, `aggregate_plan`, `read_columns`, `evaluate_ir`, plus
`graphed.awkward.to_parquet`. None is classified.

That would be a documentation gap if these verbs raised on a `Varied`. They do not, because §2.3(a)
binds `Varied` to implement "field access" over labels:

- `compile_ir` does `ids = [arr.node_id for arr in outputs]` (`execute.py:74`);
- `aggregate_plan` does `outputs[0].session` / `o.session is not session`
  (`aggregate.py:66-72`);
- `Array.__getattr__` raises only for leading underscores (`array.py:332-335`), and `node_id` /
  `session` are properties on `Array`, i.e. *not* dunders and not underscore-prefixed.

So a `Varied` whose `__getattr__` maps field access over labels answers `varied.node_id` with a
recorded `field` op named `"node_id"` (or a `Varied` of them) instead of raising —
`compile_ir(session, varied)` silently compiles a nonsense field access, `aggregate_plan(varied, …)`
silently compares field-op wrappers. That is precisely the confidently-wrong-answer class §2.5 exists
to delete, and the m48 "dunder-parity" anchor cannot see it (it enumerates dunders).

**Suggested fix.** Extend §2.3(d) to enumerate every public `Array`-consuming module verb, with a
bound disposition each (`compile_ir`/`aggregate_plan`/`read_columns`: accept a `Varied` by expanding
it into its universes, or refuse naming `graphed.universe`; `graphed.apply`: broadcast per universe;
`to_parquet`: the §6.4 path). Additionally bind that `Varied` **reserves the `Array` protocol
attribute names** (`node_id`, `session`) as errors rather than field accesses, and add that
assertion to the m48 anchor next to "string getitem = field access".

---

## MID-1 — §6.1d requires broadcasting *every* weight factor but binds a mechanism that can only supply the ambient one

**Section:** §6.1d.

**Detail.** r11 correctly widened the requirement: "**Every weight factor the fill applies — the
ambient one AND explicit `weight=[...]` factors — is broadcast to the fill's value structure**", with
the measured justification that `FillEvaluator` flattens each input independently and multiplies
after flattening (verified: `boost.py:39-47` `_flat`, `:60-71` `weight = weight * _flat(rest.pop(0))`).

But the bound mechanism covers only the ambient one: "the **event context** … supplies its ambient
weight already shaped to the fill's value structure through one neutral entry point". An explicit
`weight=[events.genWeight]` factor is a user-owned `Array` that the context never sees, and
`graphed-histogram` may not name a gak call (the plan's own factorization argument, verified:
runtime deps `["graphed", "boost-histogram>=1.4", "numpy>=1.24"]`, awkward dev-only). Worse, an
**all-loose fill** (explicitly still supported — "an all-loose fill is unweighted (the r4 primitive
path, still supported)") has no context at all, so a loose per-event weight against a per-object value
has no bound broadcaster.

The bound execution-time refusal inherits the same skew: it "raises when a weight input's flattened
length differs from the axis values', with a message naming **the ambient weight** and pointing at
'pass the value unflattened'" — wrong text when the offending factor is an explicit one, and wrong
advice when the value is legitimately per-event.

**Suggested fix.** Bind the neutral seam over an **arbitrary factor**, not over "the ambient weight":
one entry point `broadcast_like(value, factor) -> Array` owned by `graphed` proper and dispatched to
the backend idiom (awkward records `ak.broadcast_arrays`; numpy no-op), which the fill applies to the
ambient weight and to every explicit factor alike; and make the execution-time error name **which**
factor mismatched.

---

## MID-2 — §6.2 axis mode leaves the reduce/zero **spec** sourced from `h._spec`, which by construction lacks the variation axis

**Section:** §6.2(i), §6.1c, §6.1a.

**Detail.** §6.2(i) binds fill-time axis declaration ("adding a `"variation"` axis after the fill
nodes exist would leave nodes, evaluators, `_GroupReduce`'s per-slot spec and `_GroupZero`
disagreeing"), which means the fill node's spec ≠ the user histogram's own spec. §6.1c re-binds
`_GroupReduce.layout` from counts to per-slot output **indices** but keeps the third tuple element as
"spec" without saying which spec. Measured, every consumer takes it from the histogram object:

- `self._spec = spec_of(self)` fixed in `__init__` (`boost.py:146-150`);
- `layout = tuple((label, len(h._fill_nodes), h._spec) for label, h in items)` (`boost.py:282`);
- `_GroupZero`/`_GroupReduce` build the identity with `zero_of(spec)` (`boost.py:100-122`);
- `Histogram.plan()` passes `_SumFills(self._spec)` / `_ZeroHist(self._spec)` (`boost.py:245-255`).

Under axis mode all of those would build a zero histogram **without** the variation axis and then add
it to evaluator output **with** it. Related and unstated: a histogram whose first fill is unvaried and
whose second fill is varied produces two different specs on ONE histogram — the "cross-fill agreement
rule" is worded over *label sets*, not over *axis presence*, so it does not cover this.

**Suggested fix.** State in §6.2(i) that the fill-time declared spec is the **slot spec** for
`_GroupReduce`/`_GroupZero` (and that `.plan()`/`_SumFills` stays refused per §6.1c), and extend the
cross-fill agreement rule to "same declared axis presence AND same label set".

---

## MID-3 — §6.2(i-bis) binds `graphed.universe(h, label) = h[{"variation": label}]`, which measurably does not work on a bare `bh.Histogram`

**Section:** §6.2(i-bis); m50 anchor "axis-mode result shape".

**Detail.** The bound result type is "a **bare `bh.Histogram`** carrying the `"variation"` axis", and
extraction is bound as the `h[{"variation": label}]` slice. boost_histogram has no name-based axis
lookup — that is a `hist` feature. Measured this session (bh 1.8.0, in the `graphed-histogram-latest`
environment):

```
ax = bh.axis.StrCategory(['nominal','jes_up']); ax.__dict__['name'] = 'variation'
h = bh.Histogram(bh.axis.Regular(3,0,3), ax); h.fill([1,1], ['nominal','jes_up'])
h[{'variation':'nominal'}]  -> TypeError: list indices must be integers or slices, not str
h[{1: bh.loc('nominal')}]   -> works (sum 1.0)
getattr(h.axes, 'name', '<none>') -> '<none>'
```

Two consequences: (1) the bound expression must be positional (`h[{idx: bh.loc(label)}]`) or the
result type must become a `hist.Hist`; (2) the axis **name** only survives the spec round-trip if it
is written into `axis.__dict__` — `_axis_spec` stores a StrCategory as `{"type", "categories",
"metadata"}` and `_metadata_of` harvests `axis.__dict__` (`graphed-histogram-latest/src/
graphed_histogram/_spec.py:30-37, 74-76`), and `zero_of` rebuilds a plain `bh.Histogram`
(`:115-135`). Nothing in §6.2 binds the frontend to set that name, so "the axis named `variation`" —
the only handle `graphed.labels` has for distinguishing an axis-mode result from an ordinary one — is
not guaranteed to exist on the returned object.

**Suggested fix.** Bind (a) the axis-name carrier explicitly (`axis.__dict__["name"] = "variation"`,
the `hist` convention the spec codec already round-trips) and (b) the extraction by axis **position**
resolved from that name, not by `h[{"variation": …}]`. Word the m50 anchor over behaviour
("`graphed.universe(h, label)` returns the single-label slice") rather than over the literal
expression.

---

## MID-4 — §2.3 binds the `Array` **dunder** surface only; the public **method** surface (both idioms) is unbound and the dynamic parity gate cannot catch it

**Section:** §2.3(a), §2.2; m48 anchor "dunder-parity".

**Detail.** §2.3(a) binds "the full `Array` dunder surface … enumerated at implementation from
`array.py`", and the m48 anchor freezes exactly that, dynamically enumerated. Measured, `Array` also
carries four public **non-dunder** methods that are mainline idiom:
`filter`, `map`, `reduce`, `repartition` (`graphed-latest/python/graphed/array.py:374-391`) — `filter`
is the M2 method explicitly "kept". §2.3(b) binds only the *mirror* property (a plain `Array` learning
a `Varied` **mask**); nothing binds `varied.filter(mask)`, `varied.reduce("sum")`,
`varied.repartition(...)` (which §5.4 should refuse), or `varied.map(fn)`.

The numpy idiom widens the hole: `NumpyArray` overrides `__getitem__` for tuple subscripts and adds
~25 public methods (`sum`, `mean`, `std`, `reshape`, `ravel`, `astype`, `round`, `take`, `transpose`,
`T`, …) — `graphed-latest/python/graphed/numpy/array.py:71-190`, tuple `__getitem__` at `:132-136`.
Enumerating "from `array.py`" (the neutral base) leaves every one of them unbound on a
numpy-idiom `Varied`.

Because §2.3(a)'s gate enumerates *dunders*, the frozen suite is blind to the whole category, and
§2.2's `Varied.__getattr__`-as-field-access means the failure mode is a nonsense recorded `field` op,
not a clean `AttributeError`.

**Suggested fix.** Widen §2.3(a) to "the `Array` **public** surface — dunders **and** methods —
enumerated dynamically from `type(nominal_member)` at test time (so the numpy idiom's own additions
are covered), with a bound per-method classification mirroring §2.3(c) (broadcast / refusing —
`repartition`)"; extend the m48 anchor's non-vacuity floor to name at least one method.

---

## MID-5 — §6.4a's entry check is a per-partition **execution-time** predicate, not an "up front" refusal

**Section:** §6.4a, §6.4d; m51 anchors "Entry check", "Structure refusal".

**Detail.** Offsets are data. At the `to_parquet(...)` call the frontend holds a recorded graph and
typetracer forms; per-label offsets do not exist. Measured, the write is evaluated **per partition
inside the worker**: `_WritePart.__call__` reads the partition, then
`(out,) = evaluate_ir(self.compiled, backend, {self.source_name: chunk})` and writes one part
(`graphed-latest/python/graphed/awkward/io.py:111-127`); `to_parquet(compute=False)` returns that
plan (`io.py:206-…`, `graphed/write.py:32-43` `write_plan`). So the bound predicate can only run N
times, in workers, after the read.

The plan already did exactly this analysis for §6.1d in r11 ("the already-flattened-value case is an
EXECUTION-time refusal, not a record-time one … there is no static discriminator") and correctly
re-bound the raiser. §6.4a still says "at entry … run once up front", and the m51 anchor says
"refused up front" — which a test-author will freeze as a record-time raise from the `to_parquet`
call.

**Suggested fix.** Mirror the §6.1d treatment: name the raiser (`_WritePart`, before any buffer is
stored), state that the refusal is per partition and surfaces through the executor's error path, and
re-word the m51 anchor accordingly. Note also that §6.4f's "appended columns are extra marked
outputs" requires `_WritePart` to stop unpacking a single output (`(out,) = evaluate_ir(...)`,
`io.py:124`) — worth naming as part of the same target.

---

## MID-6 — the §2.6 context exposes no ambient-weight accessor, yet §6.4b expects varied weight factors to be storable fields

**Section:** §2.6a, §9.1, §6.4b.

**Detail.** §2.6a binds that a context resolves attribute/string access to **tree content only**, and
§9.1 lists the whole context surface: `labels`, `universe`, `nominal`, `variations`, `selection` (m51)
— none returns the ambient weight `Varied`. §9.1's `graphed.variations(ctx)` is bound to report "tags
and kinds … and the parsed float value", i.e. metadata, not Arrays.

§6.4b nevertheless says "Weight-only labels contribute no kinematic deltas — **their varied factors,
when among the stored fields**, augment like any other varied field". Under the owner-locked context
idiom the user never holds those factors: they were handed to `graphed.vary(..., is_weight=True)` and
absorbed into an immutable registry. This is exactly the gap r11 identified and fixed for masks
(`graphed.selection(ctx)` — "without a bridge the m51 sink would be reachable only from the loose
§2.1a style"); the identical bridge for weights is missing, and it is needed one milestone earlier
than m51 for anything that wants the event weight explicitly (e.g. a counts-vs-weighted comparison
alongside `unweighted=True`).

**Suggested fix.** Add `graphed.weight(ctx)` (returning the ambient `Varied`, `None` for a context
with no registrations) to §9.1 next to `graphed.selection`, land it in m48 with the rest of the
context surface, and cross-reference it from §6.4b.

---

## MID-7 — §6.4a: "the writer applies NONE of them to the stored buffers" contradicts the superset row rule

**Section:** §6.4a vs §6.4b/§6.4d.

**Detail.** In one sentence: "The writer applies NONE of them to the stored buffers (that is the point
of §6.4d's widest-common-structure rule); it stores one packed per-label validity mask per supplied
level **and builds the level-0 OR for the row superset**." But §6.4a's opening rule is "the writer
materializes the **superset**: rows passing ANY universe's selection", and §6.4b/§6.4d say the stored
values are "on superset rows" / "pre-object-cut values on the **event-row superset**".

Both readings are defensible from the text — write every row and store masks, or write superset rows
and store masks — and they produce different files, different sizes, and a different reader. The
single most consequential fact about the on-disk artifact should not be ambiguous going into a freeze.

**Suggested fix.** Re-word to the intended rule explicitly: "the writer applies the **level-0 OR** to
the stored rows (the superset) and applies **no other supplied mask** to the stored buffers; every
supplied level, including level 0, is additionally stored as packed per-label validity masks."

---

## LOW-1 — `Varied.apply` collides with the existing module verb `graphed.apply`, which is the very contract the rename was made to avoid

**Section:** §2.2.

**Detail.** §2.2: "(Named `apply`, NOT `map`: `Array.map` is an execution-time data callable,
`array.py:377-379`; the two contracts must not share a name.)" Measured, `apply` is already a public
module-level verb with **exactly** that execution-time contract — and it interns with `Array.map`:
`graphed.apply(fn, *arrays)` records an External `"map"` node
(`graphed-latest/python/graphed/array.py:397-410`, docstring: "With one array this IS `Array.map`
(interns with it)"), exported at `python/graphed/__init__.py:9` and in `__all__` `:44`.

So `graphed.apply(fn, x)` = run `fn` on data at execution time, while `Varied.apply(fn)` = run `fn` on
the graph at record time. The stated criterion for rejecting `map` disqualifies `apply` equally.

**Suggested fix.** Pick a name that is not already taken by the opposite contract — `Varied.per_label`
/ `Varied.for_each` / module `graphed.map_universes(v, fn)` — or, if `apply` is kept, say in §2.2 why
the collision with `graphed.apply` is acceptable, so the m48 test-author does not freeze a name that
gets changed later.

---

## LOW-2 — m50's frozen-directory pinning ("preservation/docs only") excludes two of m50's own anchors

**Section:** §10 header + m50 anchor list.

**Detail.** §10 pins m50's `graphed` half as `tests/frozen/preserve/m50`, "**preservation/docs
only**". But m50's anchor list includes `§9.1 graphed.variations(ctx)` (a frontend introspection verb,
not preservation) and the §6.2(i-bis) narrowing-helper behaviour of `graphed.labels`/`graphed.universe`
(which live in `graphed`, over histogram objects). r11 did precisely this partitioning work for m48
("leaving m48 a single flat list for two repos left 'which anchor is frozen where' undecided while
§10 pins directories") and for m49; m50 keeps the defect.

**Suggested fix.** Either widen the m50 `graphed` directory description (drop "preservation/docs
only") or pin a third location for the frontend-introspection anchors, and say which repo hosts the
`graphed.labels`-over-a-histogram anchor given `graphed` carries boost-histogram in its dev extra
only (the same fixture analysis m48 already did).

---

## LOW-3 — m48's target list omits §7.2, which m48's own anchors and §6.1c depend on

**Section:** §10 m48 targets vs m48 anchors.

**Detail.** m48's Targets read "§1, §2 (incl. the §2.6 event context), §3.2/§3.4 (API only), §4, §6.1
(incl. §6.1d ambient fills), §6.3", and §7 is listed only under m49. But m48 freezes the §7.2 schema
absence anchor, and §6.1a/§6.1c (m48 targets) cannot be implemented without §7.2's
`(output, label) → node id` map and the indices-based `_GroupReduce.layout` it feeds — the plan says
so itself: layout indices are "derived frontend-side from the compiled output list **per §7.2**".

**Suggested fix.** Add "§7.2" to m48's target list (and scope §7.1/§7.3/§7.4 to m49), so the DoD's
"Implementation Targets done exactly as specified" is checkable per milestone.

---

## LOW-4 — §6.1d's "unify to the most-derived context" says nothing about row-count agreement, and the bound error text misdirects

**Section:** §6.1d, §2.6c.

**Detail.** "inputs whose contexts sit on one ancestry chain unify to the **most-derived** context"
makes `h.fill(events.MET.pt, sel.Jet.pt)` legal (one chain), and then applies `sel`'s ambient weight —
whose members are re-indexed to `sel`'s row count (§2.6c) — against a value read at the **parent's**
row count. The failure surfaces only at execution, through §6.1d's length check, whose bound message
"names the ambient weight and points at 'pass the value unflattened'" — advice that is wrong here
(the value is already unflattened; the real fault is a value read from an ancestor context).

**Suggested fix.** Either bind ancestor-context *values* (not just weights) to be re-indexed to the
unified context, or refuse a fill whose axis values come from different levels of one chain, naming
both contexts. Either way, widen the execution-time message beyond the ambient-weight case (see
MID-1).

---

## Clean/dirty verdict

**Dirty.** Four HIGH findings, seven MID and four LOW. None of them touches an owner-locked decision;
all are internal-consistency or missing-mechanism defects, and each has a small, local fix.

The concentration is where the prompt predicted: the newest surfaces. Three of the four HIGHs are in
r10/r11-era material (§8.2's rebuilt transport, §6.4a's rebuilt entry check, §6.2's relocated
declaration contract), and the pattern in all three is the same one r10 diagnosed and r11 partly
repeated — **a mechanism named without a measured channel behind it**. §8.2(i) is the sharpest: the
plan explicitly rejected record-time ids in favour of post-reduction ids, and post-reduction ids are
not obtainable from Python at all today (and mostly do not exist after fusion).

The older material held up well under this lens. §2.4's label-aligned union composes correctly with
§2.6c's per-label re-indexing and with §2.1(b)'s weight-form stacking — I traced the corpus case
(`graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:60-76`: `sel_jets = good[sel]`
then `_btag_weight(sel_jets, variation=variation)`) through the union rule for a jes-inherited label
and for a new btag label, including the nested case where the registered factor is itself `Varied`,
and it lands on the reference semantics in both. §1.1's e-canonicalization survived the edge cases I
pushed at it (exact-decimal spellings, `"20e-1"`, non-minimal canonical re-rendering, negative zero,
the 32-char cap forcing rejection of ≥10³² magnitudes, cross-notation p/e equality) with no internal
contradiction. §5.4/§6.4's boundary interaction is clean (the write path never touches
`Exchange`/`Join`), and §7.3's one-time `task_id` churn is correctly scoped to `_PartitionReduce`,
which the m51 write path does not use. No package-boundary violation was found: §6.1d's neutral
broadcast seam, §6.4a's awkward-idiom `to_parquet`, and §2.3e's neutral `_context` slot all respect
the factorization rule (the only smell, `graphed.labels` over histogram results, is LOW-2's
placement question, not a layering break).
