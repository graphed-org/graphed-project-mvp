# systematics-vary-plan r18 — revision notes (review round 9, r17 reviews)

Isolated plan reviser, 2026-07-30. Input: 24 findings (NITs excluded) from three independent r17
reviews (`systematics-vary-plan-review-r17-{facts,design,tests}.md`) — 1 BLOCKER, 5 HIGH, 11 MID,
7 LOW. Three cross-lens pairs were merged (design MID §7.2-site + tests MID §7.2-control; facts LOW
m49-DurablePlan + tests HIGH m49-determinism + tests LOW §7.3-"anchor states which").

Every finding was re-verified in this session against the pinned roots before acting:
`/private/tmp/claude-501/graphed-latest@ff7c607`, `/private/tmp/claude-501/graphed-histogram-latest@211cbbe`,
`/Users/lgray/vibe-coding/graphed-workdir/graphed-root-prompt.md`.
**Nothing rejected, nothing deferred** — no finding's resolution required reversing an owner-locked
decision, so no OPEN ITEMS block was added.

## Measurements taken this session (the basis for every new claim written into the plan)

| Probe | Result |
|---|---|
| `awk 'NR>=1284&&NR<=1288'` on `graphed-root-prompt.md` | `:1284` header, `:1285` BLANK, `:1286-1287` the "systematic variations as a graph axis" sentence |
| `graphed-histogram@211cbbe boost.py:100-130,254-292` | `_add_groups` = `{label: a[label]+b[label] for label in a}` (homogeneous key-wise `+`); `_GroupReduce`/`_GroupZero` take `layout`; `plan()` returns `Plan[dict[str,bh.Histogram]]` and nothing else |
| `graphed-latest core/execution.py:206-224` | `Plan(process, combine, empty, tasks, next_tasks, stop, open_once)` — no finalize hook; `ExecResult(value, n_partitions, n_combines, stopped)` |
| `graphed-latest numpy/array.py` | `shape` `:78`, `dtype` `:82`, `ndim` `:86`, `T` `:160` are plain `@property` (invisible to `inspect.isfunction`); `array.py:332-335` records a `field` op for any non-underscore name |
| `graphed-latest awkward/io.py:206-216` | `to_parquet(array, destination, *, steps_per_file, compute, executor, prefix, column, behavior)` — **no `select=`**; `_WritePart` is a frozen dataclass, `(out,) = evaluate_ir(...)` at `:121`, evaluated per partition in the worker |
| `src/store.rs:147-156` | `mark_output` de-dups (`if !g.outputs.contains(&id)`) |
| `core/plan.py:72-76` | `OpSpec.identity()` for `kind="ref"` is `b"ref\0"+ref` — closure fields absent from the plan bytes |
| §3.3 topology built on the raw `GraphStore` API (D=500, K=50), best-of-3 | N=16 → 1333 reachable nodes / stages 17 / reduced 34 / **3.77 ms**; N=128 → 7157 / 129 / 258 / **21.28 ms**. Node ratio **5.37**, time ratio **5.64** |
| cloudpickle 3.1.2, `PYTHONHASHSEED` ∈ {1,7,12345}, sha256[:16] of `cloudpickle.dumps(...)` | importable frozen dataclass + **sorted tuple** → `80e8024dc8f3b77d` ×3 (stable); + **frozenset** → `ff1b11d76cdaebb5` / `93a74f43226cc6fa` / `ca89af57ea4550fe`; **`__main__`-defined** dataclass + sorted tuple → `f76160abbc237ae9` / `7b2a91fcbece502f` / `4e263cf4767124a6` (unstable) |
| interning probe vs `graphed-latest` | `a = src*2.0; b = src*2.0` → `a.node_id == b.node_id == 1`, `a is b` False, `session.node_count() == 2` |

## Per-finding verdicts

### BLOCKER

**1. design §6.1a/§6.1c — two incompatible shapes for one m48-frozen object. APPLIED.**
Verified: plan §6.1a said "the combine BRANCHES on the two shapes"; §6.1c(r17) said "The COMBINE
needs no branch … every slot's value is a plain `bh.Histogram`". Measured `_add_groups` is a
homogeneous key-wise `+` (boost.py:120-122) and §6.1c's `(output, label|None)` keying makes it work
unchanged; m50's scaling anchor already counts those slot keys. Edit: §6.1a now binds the plan's
COMBINED value as the flat slot-keyed `{(output, label|None) → bh.Histogram}` with `_add_groups`
staying homogeneous, and states that the nested `{output: hist | {label: hist}}` shape is the
UNPACK surface's type; the "combine BRANCHES" clause is withdrawn with its reason recorded. m48's
§6.1a anchor now freezes both halves together.

### HIGH

**2. design — §6.1a's result shape has no bound producer. APPLIED.**
Verified independently: no post-combine seam exists (`Plan` has no finalize hook, `ExecResult.value`
is exactly the combine output, `plan()` returns the `Plan`), and §7.2's m48 anchor freezes the
`Plan`/`ExecResult` schema KEY SETS, foreclosing a new field. Edit: bound a read-only
`graphed_histogram.unpack(value)`-shaped module verb over the executed plan value + layout
(spelling pinned at m48 freeze), returning §6.1a's union type and choosing per output from the
layout's MODE; listed in §9.1; §6.1c's "FRONTEND UNPACKER" and §7.2's "the frontend unpacks" now
point at it; m48's §6.1a anchor is worded over it.

**3. design §6.4b — stored varied weight factors unstorable where §6.4a(2a) says they come from.
APPLIED.** Verified from the plan's own binding text: the record is pre-selection on superset rows
(§6.4a/§6.4b) while §2.6c gives a selection-derived context per-label row sets with the ambient
registry re-indexed per label, and §6.4d refuses a stored field whose per-label offsets differ from
nominal's — so `graphed.weight(sel)` is refused by construction and with the wrong message; a mask
has no inverse, so no re-indexing rule is expressible. Edit: §6.4b binds the row-space precondition
(storable only across `vary` IDENTITY links; a selection-scoped weight is NOT storable in v1,
refused with a row-space message); §6.4a(2a)'s r16 justification is softened (admitting `vary` links
now rests on m51's own bridge anchor, which is independent); m51's round-trip anchor names the
storable spelling and the entry-check anchor carries the refusal.

**4. tests — m48 freezes `to_parquet`'s §2.3d disposition that m51 must change. APPLIED.**
Verified: `to_parquet` has no `select=` parameter today, and it is outside `graphed.__all__`, so the
dynamic discovery half never reaches it — it was in m48's table only by being NAMED. Also confirmed
r17's m48 refusal BEHAVIOUR is asserted by no m48 anchor (m48's refusal table splits into
boundary/plan and compile/aggregate verbs; `to_parquet` is in neither). Edit: `to_parquet` carries
NO disposition until m51 and is removed from m48's named floor list (costs no class coverage — the
8 dynamically discovered verbs supply *refusing*+*expanding*, `broadcast_like`/`context_of` supply
the other two); m48's per-class floor re-worded as CONTAINMENT ("at least one member of each of …"),
never an exact set; m51's bullet re-worded from "re-classification" to "enters the table as
*accepting*".

**5+6+7 (merged: facts LOW m49-DurablePlan, tests HIGH m49-determinism, tests LOW §7.3). APPLIED.**
Verified: `OpSpec.identity()` for `kind="ref"` is `b"ref\0"+ref`, so the closure's fields never reach
the plan bytes — a `from_ref` fixture freezes the §8.2(i) determinism anchor GREEN against a
`frozenset` `variation_labels`; and measured, a `__main__`-defined (by-value) closure operand makes
the digests seed-dependent for BOTH the tuple and frozenset forms, i.e. red against a correct
implementation. Edit: §7.3 drops the "either … or …; the anchor states which" and binds the BY-VALUE
construction `DurablePlan(ir=…, process=OpSpec.from_callable(plan.process), …)` over the plan
`aggregate_plan` returned, plus the module-level-importable requirement on closure operands, with
the measured digests; m49's §8.2(i) determinism bullet and the §7.3 interrupt/resume bullet both
state the construction explicitly. (`OpSpec.from_ref` remains the documented USER idiom.)

**8. tests — §6.1d link kind (1) has no value-asserting anchor. APPLIED.**
Verified: m48's only re-indexing anchor is the §2.6c ambient-REGISTRY one (a different operation);
link kind (1) was covered only by "a positive control that an ancestor-chain pair unifies silently",
the absence-of-error shape r15 explicitly rejected for link kind (3). Edit: m48's §2.6/§6.1d
mega-bullet gains a link-kind-(1) case — `h.fill(events.MET.pt, sel.Jet.pt)` with
`sel = events[varied_mask]`, compared ELEMENTWISE label-aligned against a manually re-indexed
reference; the §2.6c cross-reference at the "read through a derived context" rule now names both
re-indexing anchors; the m48 split enumeration puts the new (fill-shaped) clause in
`graphed-histogram`'s half.

### MID

**9. design §2.1(a)/(b) "members are Arrays". APPLIED.** Verified purely internally: the stacking
rule three paragraphs below requires `Varied` members (`graphed.nominal(v)` fallback;
`old_ambient[L] × factor[L]` "evaluated in that label's own universe"), and the §2.6 sketch passes
`btag_sf(sel.Jet)` — a `Varied` — as `nominal=`/`up=`/`down=`. Edit: one rule stated once (a member
may be an `Array` OR a `Varied`; (a)/(c) reduce to the central universe, (b) keeps it label-aligned;
checks apply per flattened member), with both per-overload type declarations removed.

**10. design §2.2/§2.3a — numpy-idiom PROPERTIES have no disposition. APPLIED.** Verified:
`shape`/`dtype`/`ndim`/`T` are plain properties on `NumpyArray`, `inspect.isfunction` never sees
them, and `Array.__getattr__` records a `field` op for any non-underscore name. Edit: §2.2's rule
widened from two names to a property DISCOVERY rule (`node_id`/`session` raise; every other property
answers eagerly on the nominal member); §2.3a gains a third enumeration over properties with a
`node_count()`-delta-0 assertion; m48's parity anchor names `varied.dtype`.

**11+12 (merged: design §7.2 site/scope, tests §7.2 positive control). APPLIED.** Verified both
probes reproduce (`compile_ir(s, nom, w*1.0, w*2.0, w*0.5)` → 3 outputs from 4 record ids; the fill
path collapses two fill nodes to one output) and that §6.3 bindingly says no-variation paths are
unchanged. Edit: §7.2 binds the SITE (the `(output, label) → node id` map's owner — the group-plan
builder, not `compile_ir`/`aggregate_plan`) and the SCOPE (varied programs only); m48's §1.2 anchor
gains the positive control that an unvaried optimizer-merged program (`compile_ir(s, b, b * 1.0)`)
still compiles and runs as today.

**13. design §6.4f — widened unpack not bound to node-id keying. APPLIED.** Verified `_WritePart`
is a frozen dataclass evaluated per partition in the worker with `(out,) = evaluate_ir(...)`, and
that m51's round-trip anchor puts the collapse case ("a label structurally equal to nominal") in
scope. Edit: §6.4f binds resolution BY NODE ID per §7.2 with replication of a shared value, and
makes the `record node id → output position` table a driver-derived FIELD of `_WritePart`; it also
settles that the §7.2 shortfall refusal guards the varied write path at m51 (record-time, at the
`to_parquet` call); m51's round-trip anchor now witnesses the replication.

**14. tests §3.3 — the 24.0 literal on a 5.4× span. APPLIED.** Re-measured the exact §3.3 builder
myself: nodes 1333 → 7157 (5.37×), time 3.77 → 21.28 ms (5.64×). m4's 24.0 buys 3× headroom over an
8× span; copied here it fails only exponents ≥ 1.89, and a node-quadratic reducer measures ≈28.8×,
1.2× above the gate. Edit: the bound becomes **16.0** with the derivation and both measured ratios
recorded, and the self-scaling alternative (`< 3 × nodes(128)/nodes(16)`, `reachable_nodes` is in
`reduce()`'s report) named as an equivalent option.

**15. tests — m49's §8.2(i) accessor anchor passes under a constant map. APPLIED.** Verified the
three clauses are type constraints, and that §3.3's topology reduces to `stages == N+1` (17 at
N=16, 129 at N=128 — re-measured), making an image-cardinality assertion exact and free. Edit: the
anchor gains the partitioning clause (shared prefix → ONE reduced id; each universe's chain → a
distinct one; image = exactly N+1).

**16. tests §6.4a(2a) — node-id-equality rule has no discriminating anchor. APPLIED.** Verified the
interning probe (`a*2.0` recorded twice → same node id, distinct objects). Edit: m51's bridge anchor
gains the positive control that a re-recorded equal `select=` expression is ACCEPTED and round-trips
identically, so `mask is ctx._selection` cannot pass.

**17. tests §6.1c — per-output MODE unanchored. APPLIED.** Verified every m50 anchor is single-mode
(equality = two separate programs; scaling pins output count 1; (i-bis) one histogram;
declaration/mode-mismatch one histogram; the §9.1 listing anchor is sibling+unvaried). Edit: m50
gains a MIXED-MODE plan anchor (one axis-mode + one sibling-mode output in one `plan(...)`),
asserting both unpacked shapes and noting it is the only thing exercising `_GroupZero`'s per-slot
spec across two different specs. §6.1c cross-references it.

**18. tests — m50's target line demands the design r17 withdrew. APPLIED.** Edit: the target line
now reads "the `(output, None)` keying, the per-OUTPUT mode recorded in the layout, and the per-slot
spec taken from the fill node", with the withdrawal recorded.

**19. tests §6.3(2)/§6.1d — contexted-but-unvaried broadcast trigger unanchored. APPLIED.** Verified
the trigger is stated once as a DISJUNCTION and that `FillEvaluator` flattens inputs independently
and multiplies factors after flattening (boost.py:60-71), so the mismatch is real. Edit: m48's
broadcast anchor gains a third assertion (context with no registrations, no `Varied` input,
per-object value + explicit per-event factor) against the manual reference, PLUS a witness that the
seam node was recorded (fill-node cone or a `node_count()` delta vs the same fill without a handle).

### LOW

**20. facts — root-prompt Out-of-scope anchor. APPLIED.** Verified `:1285` is blank and the sentence
runs `:1286-1287`. Edit: corrected in the scope-deviation block, §12.3(b) and the appendix row, and
r17's history line now records that its own correction was off by one.

**21. design §10 — m49/m51 target lines under-list. APPLIED.** Edit: m49 gains "§2.5's
shift-after-weight diagnostic"; m51 gains "§9.1's `graphed.selection` and §2.3d's `to_parquet` table
entry".

**22. design §1.1 — magnitude rejection over the rendered digit string. APPLIED.** Edit: the
magnitude test runs on the computed DIGIT COUNT (mantissa digits + exponent) before rendering, with
`"1e1000000000"` named as the spelling that makes render-then-measure untenable.

**23. design §2.1/§2.3e — context-handle divergence not among the construction checks. APPLIED.**
Verified `vary` is not an op and reaches none of the five `_array_cls` chokepoints, and that §2.3d
classifies `context_of` eager-metadata on the nominal member (so a mismatch is invisible). Edit:
§2.1's construction checks gain handle unification (one ancestry chain; most-derived carried;
divergence is a construction-time error naming both), and m48's divergent-lineage anchor gains the
`vary`-construction case.

**24. tests §2.3e(3) — "the refusing class is exactly `{gak.join}`". APPLIED.** Edit: re-worded as
containment plus a monotone count, matching the shape already used for the broadcast class; the
self-repairing sentence in the same clause no longer contradicts it.

**25. tests §6.2(ii)/m50 — stale circularity parenthetical. APPLIED.** Edit: "which §6.2(i-bis)
DERIVES FROM the axis bin set — so the comparison is circular on CONTENT regardless of order".

## Rejections / deferrals

None. No finding was refuted on measurement, and none required reversing an owner-locked decision
(the §6.1a/§6.1c settlement, the `to_parquet` table timing, and the §6.4b row-space precondition are
all internal-consistency repairs within the owner-locked scope, naming, and architecture).
