# `systematics-vary-plan.md` — review round 10, DESIGN SOUNDNESS lens

- **Plan revision reviewed:** r18 (4209 lines, read in full: header, Part I, all of PART II §1–§12,
  the anchors appendix, and the revision history back through r16).
- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  violations, milestone-boundary consistency. New-surface priority: §2.6, §6.1d, §6.4/m51, §1.1 r9.
- **Date:** 2026-07-30.
- **Verification roots used** (every code fact below was read or executed by me in this session):
  - `/private/tmp/claude-501/graphed-latest` (consolidated `graphed`, `ff7c607`)
  - `/private/tmp/claude-501/graphed-histogram-latest` (`211cbbe`, confirmed via `git log -1`)
  - `/private/tmp/claude-501/graphed-corpus-latest` (`49650e4`)
- **Owner-locked decisions** (naming, functional surface, e-form canonicalization, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, JER-SF non-ordering, the Phase-2
  pull-in) were treated as fixed. No finding below asks for a different choice; each is an internal
  inconsistency, an unhandled interaction, or a missing operand in how a locked decision is
  *specified*.

Findings are ordered by severity. 1 BLOCKER, 3 HIGH, 2 MID, 5 LOW.

---

## BLOCKER-1 — §6.1a's r18 plan-value binding is unscoped and breaks the frozen m23 suite

**Section:** §6.1a (plan lines 1319–1343), against §10's closing rule (plan line 2459) and §6.3.

**Detail.** r18 settled the §6.1a/§6.1c shape conflict with this binding sentence (plan `:1324-1326`):

> Binding: **the plan's combined value is the FLAT slot-keyed mapping §6.1c binds — `{(output,
> label) → bh.Histogram}` in sibling mode, `{(output, None) → bh.Histogram}` in axis mode** — and
> `_add_groups` stays a homogeneous key-wise `+`

It carries no scope. "Sibling mode" is the default lowering for *every* program, varied or not, so
read as written it also re-keys the combined value of a wholly **unvaried** group plan from
`{output_name: hist}` to `{(output_name, "nominal"): hist}`.

Measured against `graphed-histogram@211cbbe`, that is exactly what the existing frozen m23 suite
asserts must NOT change:

- `src/graphed_histogram/boost.py:100-122` — `_GroupReduce.layout` is `(label, n_fills, spec)` where
  `label` is the OUTPUT name (built at `:282`, `layout = tuple((label, len(h._fill_nodes), h._spec)
  for label, h in items)` over `(output_name, Histogram)` pairs), and `__call__` returns
  `out[label] = total`, i.e. `{output_name: hist}`.
- `tests/frozen/m23/test_group_plan.py:74-75` — `assert np.array_equal(out["hi"].values(), …)` /
  `out["lo"]`; `:86,89` — `grouped["0"]`, `grouped["1"]`; `:99` — `zero["hi"].sum() == 0`, all over
  `SequentialRunner().run(gh.plan({...})).value`.

Under the r18 binding every one of those five assertions raises `KeyError`. §10 states explicitly
that "the frozen m05/m4/m9/m23/m29 artifacts are **binding and unchanged**" (plan `:2459`), and the
DoD requires the frozen suite green and unmodified. So the plan as written makes m48 unimplementable
without either a Test Dispute against an already-frozen milestone or an integrity violation. It also
contradicts §6.3's own binding "Data / no-variation paths are unchanged" and silently changes
`plan()`'s public return type (`Plan[dict[str, bh.Histogram]]`,
`src/graphed_histogram/boost.py:262`) under the DoD's `mypy --strict`.

Note the m48 anchor itself is fine — it freezes the slot shape "on a MIXED varied/unvaried output
set" (plan `:2703-2714`), which never exercises a wholly unvaried plan. The defect is that the
binding sentence reaches past its own anchor.

**Evidence.** Read: plan `:1319-1343`, `:2459`, `:2703-2714`;
`graphed-histogram-latest/src/graphed_histogram/boost.py:100-122,255-292`;
`graphed-histogram-latest/tests/frozen/m23/test_group_plan.py:74-75,86,89,99` (repo at `211cbbe`).

**Suggested fix.** Scope the slot keying to outputs that carry variations. Concretely: an output no
variation reaches keeps its bare `output_name` key (today's shape, m23 stays green); a varied
sibling-mode output uses `(output, label)`; an axis-mode output uses `(output, None)`. All three
value types are `bh.Histogram`, so `_add_groups`' key-wise `+` remains homogeneous and nothing else
in §6.1c changes. The unpacker (§6.1a r18) then maps a bare-string key to a bare `hist`, which is
already what §6.1a requires of it. Add one sentence to §6.1a and one to §6.1c, and give the m48
anchor a wholly-unvaried positive control asserting today's key shape survives.

---

## HIGH-1 — §6.4a predicate (2a) is not decidable from the lineage direction the plan binds

**Section:** §6.4a(2a) (plan lines 1781–1830), against §2.6b (plan `:926-932`) and §9.1
(plan `:2341-2359`).

**Detail.** (2a) is a *record-time* check whose operand is a context the plan gives no way to reach:

> the supplied mask must be the selection that derived **some context** from the context the record
> was read from … `graphed.selection(c)` … for a context `c` **reachable from the record's own
> context handle** by exactly one MASK DERIVATION plus any number of `vary` links.
> … **How "the supplied mask IS `graphed.selection(c)`" is DECIDED is bound, r17**: per-label
> **node-id equality against the mask the context retains**, with Python object identity as a
> sufficient fast path.

Deciding this requires resolving the supplied mask *forward* to the context it derived — i.e.
enumerating **children** of the record's context `R`. But §2.6b binds lineage in the opposite
direction only: "Each returned context links to its **parent**" (plan `:931`). There is no
parent→children index, no mask→context back-map, and §9.1's `graphed.selection(ctx)` goes
context→mask, never mask→context. §2.5's registration mechanism is scoped to `Varied` *containers*
("`vary()` registers each container with its Session (weak reference)", plan `:883-884`), not to
contexts, and is itself declared to be an m48 target "whose spelling is pinned at freeze — nothing
in the anchors depends on it directly" (plan `:896-898`). The same gap swallows the (ii)
absent-operand case, "the record has a handle but **the supplied mask derived no context**" (plan
`:1826-1829`), which is likewise undecidable without a mask→context map.

The plan's own justification — "Decidable frontend-side, because lineage is a Python object chain"
(plan `:1808-1810`) — is true of the parent direction and false of the direction (2a) needs. m51
freezes four controls on this predicate (the silent-corruption case, the chained-context case, the
two absent-operand cases, the universe/nominal refusal, plan `:3318-3340`), so a test-author freezes
behaviour whose decision procedure has no implementable operand — the same "the channel it named
does not exist" class r10/r11/r12 each repaired one layer up for §8.2.

**Evidence.** Read: plan `:1781-1830`, `:883-898`, `:926-932`, `:2341-2359`, `:3318-3340`. No
measurement contradicts this — the point is an absence: nothing in §2.2/§2.6/§9.1 exposes a
child-ward or mask→context traversal.

**Suggested fix.** Re-express (2a) over the operand that *is* available: the supplied mask's own
§2.3e **context handle**. Bind "`graphed.context_of(select_mask)` IS the record's own context
handle" (with the per-label node-id comparison retained only where a mask is compared to a retained
selection). Verified against all four m51-anchored cases with the §2.3e origination/merge rules:

| case | handle(mask) | R | (2a) verdict wanted | handle rule gives |
|---|---|---|---|---|
| canonical `to_parquet(events.Jet, select=graphed.selection(sel))`, `sel = events[m]` | `events` | `events` | accept | accept |
| silent corruption: record read from `sel = events[nominal_mask]`, `select=varied_mask` | `events` | `sel` | refuse | refuse |
| chained: `graphed.selection(sel2)` for `sel2 = sel[mask2]`, record in root row space | `sel` | `events` | refuse | refuse |
| loose record, no handle | any | `None` | skip (2a) | skip |
| `select=graphed.selection(graphed.nominal(sel))`, record read from `sel` | `events` | `sel` | refuse | refuse |

If the plan wants to keep refusing case (ii) (a mask in the record's row space that never derived a
context), it must additionally bind the registry that makes "derived a context" observable — but
note that accepting it is harmless: such a mask is in the right row space and the superset it
defines is well-formed.

---

## HIGH-2 — no row-space contract on a weight factor registered by `graphed.vary(ctx, …, is_weight=True)`

**Section:** §2.1 overload (b) + its stacking rule (plan lines 394–397, 413–423), §2.6b
(plan `:926-932`), against §6.4b's r18 precondition (plan `:1881-1894`).

**Detail.** §2.1(b) says only that "`nominal` … is the central per-event weight factor and every
member is a per-event weight factor". §2.6b says the weight form "registers the factor into the
returned context's ambient weight". Neither binds *which row space* the factor must live in, and
§2.1's stacking rule then records a graph op across whatever it is given:

> an inherited label L's ambient member becomes `old_ambient[L] × factor[L]`

On a derived context this is a cross-row-space multiplication. Measured: §2.6c binds that a derived
context "inherit[s] the ambient registry with every member RE-INDEXED by the derivation mask" (plan
`:945-948`), so `old_ambient[L]` sits at `|sel_L|` rows, while a factor computed from a value read
at the *parent* — e.g. reusing the sketch's own `jets = events.Jet[events.Jet.pt > 25]` in
`graphed.vary(sel, "btag", btag_sf(jets), is_weight=True, …)` — sits at `|events|` rows and carries
`events`' handle by §2.3e's merge rule. `record_op` performs no length check
(`graphed-latest/python/graphed/session.py:142-168`), so the product records cleanly and dies at
execution with a length error whose message §6.1d's refusal contract does not cover (that contract
is scoped to *fill* weight factors, plan `:1527-1532`).

This is not a corner: §6.1d's link-kind machinery exists precisely to re-index ancestor-context
values, and it is applied **at the fill** only (plan `:1441-1456`) — by which time the registration
has already baked the mismatch into an interned expression. Worse, another binding requirement now
*depends* on the unbound premise: §6.4b's r18 row-space precondition reasons that
"`graphed.weight(sel)` for `sel = events[mask]` has a nominal length of `|sel_nominal|` and per-label
lengths that differ" (plan `:1884-1886`). That is true of *inherited* members by §2.6c and simply
unknown for members registered directly on `sel`. And m48 freezes the stacking outcome through
`graphed.weight(ctx)` (plan `:2618-2630`), so the anchor's own fixture depends on an answer the plan
does not give.

**Evidence.** Read: plan `:394-397`, `:413-423`, `:926-932`, `:945-948`, `:1441-1456`, `:1527-1532`,
`:1881-1894`, `:2618-2630`. Code: `graphed-latest/python/graphed/session.py:142-168` (`record_op`
takes inputs and records; no length/row-space validation);
`graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:60-76` (the corpus computes
`sel_jets = good[sel]` then `_btag_weight(sel_jets, …)` — i.e. the factor IS in the derived row
space, which is why the plan's sketch happens to work).

**Suggested fix.** Add one binding sentence to §2.1(b): the registered factor (and every member of a
`Varied` factor) MUST live in the target context's row space; if it carries an ancestor context's
handle it is re-indexed across the intervening lineage links exactly as §6.1d link kinds (1)–(3)
prescribe, and a factor whose handle is neither the target nor an ancestor is the §2.1 divergence
error. State the resulting invariant explicitly — `graphed.weight(ctx)` always answers in `ctx`'s row
space — since §6.4b already assumes it. Give m48's stacking anchor a positive control registering a
factor computed at the PARENT context.

---

## HIGH-3 — three binding requirements need the compiled artifact before `aggregate_plan` is called, and no seam exists

**Section:** §6.1c (plan `:1373-1384`), §7.2's m48 refusal (plan `:2091-2107`), §8.2(i)
(plan `:2242-2245`).

**Detail.** All three requirements are stated over data that only exists *after* compilation, but
they must be baked into objects that are constructed *before* it:

1. §6.1c: "`layout` carries per-slot output **INDICES**, not counts … **derived frontend-side from
   the compiled output list per §7.2**". The layout is a constructor argument of `_GroupReduce` /
   `_GroupZero`, which are passed into `aggregate_plan` as `reduce=`/`empty=`.
2. §7.2 r18: the m48 refusal runs in "`graphed-histogram`'s group-plan builder (`plan()`)" and
   "compares the number of DISTINCT compiled outputs (`GraphStore.deserialize(ir).outputs()`)".
3. §8.2(i): `variation_labels` "is ADDED to the worker process closure (`_PartitionReduce`)" and is
   "keyed on **POST-REDUCTION node ids** taken from the same `compile_ir` call that produced the
   shipped `ir`".

Measured, `aggregate_plan` compiles **internally** and accepts only pre-built closures
(`graphed-latest/python/graphed/aggregate.py:68-108`): `compiled = compile_ir(session, *outputs)` at
`:95`, then `process = _PartitionReduce(ir=bytes(compiled.ir), …, reduce=reduce)` at `:96-104`.
`_PartitionReduce` is a `@dataclass(frozen=True)` (`aggregate.py:44-55`) with a fixed field list and
no `variation_labels`. `graphed_histogram.plan()` builds its layout *before* calling `aggregate_plan`
(`graphed-histogram-latest/src/graphed_histogram/boost.py:282-292`).

So an implementer must invent one of: (a) a second `compile_ir` in `plan()` — doubling the reduction
the §3.3 anti-quadratic benchmark exists to bound, on the variation-expanded graph; (b) mutating a
frozen dataclass after `aggregate_plan` returns via `object.__setattr__`; or (c) a new
`aggregate_plan` parameter/seam. For §8.2(i) options (a) and (b) do not even suffice — the field
lives on the frozen `_PartitionReduce` that `aggregate_plan` itself constructs, so a public
`aggregate_plan` signature change in `graphed` proper, consumed across the package boundary by
`graphed-histogram`'s group-plan builder, is essentially forced. The plan names no such parameter
and pins no spelling — the exact "unwritable as stated" class it repaired for §2.5's diagnostic
channel, §5.3's stats verb, §9.1's fill-node accessor and (in r18) §6.1a's unpack verb.

**Evidence.** Read: plan `:1373-1384`, `:2091-2107`, `:2242-2245`. Code:
`graphed-latest/python/graphed/aggregate.py:44-65,68-108`;
`graphed-histogram-latest/src/graphed_histogram/boost.py:255-292`.

**Suggested fix.** Bind the seam once, in §7.2 (both m48 and m49 consume it): `graphed.aggregate_plan`
gains a keyword taking the per-plan variation metadata **plus** a way for the caller to see the
compiled output order — e.g. `aggregate_plan(…, layout_from_outputs=<callable(list[int]) -> reduce,
empty>)`, or the simpler `aggregate_plan(…, variation_labels=…, on_compiled=<callable(CompiledGraph)>)`.
Exact spelling pinned at m48 freeze, listed alongside the other new surfaces in §9.1, with an explicit
statement that `plan()` MUST NOT compile twice (so the §3.3 cost model still holds).

---

## MID-1 — §9.1's one-argument `unpack(value)` contradicts §6.1a, and the per-output MODE it is meant to consume is redundant

**Section:** §9.1 (plan `:2360-2366`), §6.1a (plan `:1339-1343`), §6.1c (plan `:1393-1400`),
m50's r18 mixed-mode anchor (plan `:3142-3154`).

**Detail.** Two mismatches in the same new r18 surface.

(a) §6.1a binds the unpacker as "a read-only `graphed_histogram` module verb **over the executed plan
value plus the plan's layout**", while §9.1 declares it as `graphed_histogram.unpack(value) ->
dict[str, bh.Histogram | dict[str, bh.Histogram]]` — a one-argument signature that cannot reach the
layout. Measured, the layout is not recoverable from the value: it lives inside
`_GroupReduce`/`_GroupZero`, i.e. inside `Plan.process`/`Plan.empty`
(`graphed-latest/python/graphed/core/execution.py:206-217`; `ExecResult` carries only
`value/n_partitions/n_combines/stopped`, `:219-224`). A test-author pinning the spelling per §9.1
freezes a signature the implementer cannot satisfy per §6.1a.

(b) The tension resolves only because the MODE field §6.1c mandates is **redundant** under §6.1c's
own key shapes. Per output, the key form already determines the mode: an axis-mode output contributes
"exactly ONE slot, keyed `(output, None)`" (plan `:1393`), a sibling-mode output contributes
`(output, label)` slots, and a sibling output reached by no variation has exactly one label
(`"nominal"`), which §6.1a maps to a bare `hist`. There is no key form shared by two modes. §6.1c
concedes half of this ("in a single-mode plan the shape is inferable from the key form alone") but
concludes the MODE is needed for a mixed plan — which does not follow, because the discrimination is
**per output**, not per plan. Consequently m50's new r18 anchor, headlined "the per-OUTPUT MODE's
only reason to exist" (plan `:3142`), cannot witness the field: an implementation that omits MODE
entirely and unpacks from the key form passes every assertion in that anchor.

**Evidence.** Read: plan `:1339-1343`, `:1393-1400`, `:2360-2366`, `:3142-3154`. Code:
`graphed-latest/python/graphed/core/execution.py:206-224` (`Plan` = process/combine/empty/tasks/
next_tasks/stop/open_once — no finalize hook, no layout accessor; `ExecResult.value` is the combine
output); `graphed-histogram-latest/src/graphed_histogram/boost.py:254-292` (`plan()` returns that
`Plan` and nothing else).

**Suggested fix.** Pick one and make the two sections agree: either (i) drop the MODE field, state in
§6.1c that the per-output mode is recovered from the slot key form, keep §9.1's `unpack(value)` and
re-word m50's mixed-mode anchor as an unpacking-correctness anchor (which is what it actually
asserts); or (ii) keep MODE and correct §9.1 to a two-argument shape (`unpack(value, plan)` /
`unpack(value, layout)`), and give the m50 anchor a witness that can actually fail without the field.
(i) is the smaller commitment and matches the measured surface.

---

## MID-2 — a varied `sample=` has no lowering class in §6.1b or §6.2

**Section:** §6.1d (plan `:1431-1436`), §6.1b (plan `:1352-1356`), §6.2 (plan `:1536-1559`), m48
anchor (plan `:2796-2805`).

**Detail.** r15/r16 added `sample=` as a fourth label source at the fill — "`sample=` folds LAST,
after the explicit factors" — and m48 freezes it as a first-class operand: the four-way fold anchor
requires "a varied `sample=`" that "is ACCEPTED/expanded rather than raising `AttributeError`". But
the lowering taxonomy has only two classes:

- §6.1b: "A fill combining **shift labels S and weight labels W** records exactly `1 + |S| + |W|`
  fill nodes" (frozen in m49).
- §6.2: weight labels "collapse into the evaluator-side loop"; "**Shift labels always lower as
  sibling fill nodes**"; axis-mode arity is `1 + |S|`.

A label borne only by `sample=` is in neither set. Its member cannot ride the evaluator-side weight
loop (that loop re-fills with different *weights* against a fixed sample column), so it must lower as
a sibling — but then m49's frozen `1 + |S| + |W|` count is wrong for such a program, and §6.2's
axis-mode `1 + |S|` is wrong too. Nothing states which.

Measured, `sample` really is an unchecked live input: `Histogram.fill` type-checks `args` and
`weights` but appends `sample` with no `isinstance` guard
(`graphed-histogram-latest/src/graphed_histogram/boost.py:160-178`, `inputs.append(sample)` at
`:177-178`), and the recorded params carry `"sampled": sample is not None` (`:198-212`) — so a
sample-borne label is a real, recordable program shape, not a hypothetical.

**Evidence.** Read: plan `:1352-1356`, `:1431-1436`, `:1536-1559`, `:2796-2805`. Code:
`graphed-histogram-latest/src/graphed_histogram/boost.py:152-212`.

**Suggested fix.** Define the taxonomy over lowering behaviour rather than over provenance: let `S` be
"labels requiring a sibling fill node" (labels borne by any axis value **or** by `sample=`) and `W` be
"labels borne only by weight factors (ambient or explicit)". Then `1 + |S| + |W|` (sibling) and
`1 + |S|` (axis) both stay correct, and §6.2's "shift labels always lower as sibling fill nodes"
extends verbatim. One sentence in §6.1b and one in §6.2; m49's arity anchor gains a sample-varied
case, or §6.1b explicitly scopes its formula to programs with no varied `sample=` and §11 parks the
rest.

---

## LOW-1 — m48's §9.1 target line says "only" and omits the r18 unpack verb it is required to build

**Section:** m48 target line (plan `:2466-2472`) vs §9.1 (plan `:2360-2366`).

**Detail.** m48's targets read "**§9.1 partially — `graphed.labels`/`universe`/`nominal`/`weight`,
`graphed.context_of` (r15) and the per-label fill-node accessor only**". r18 added a seventh §9.1
surface, `graphed_histogram.unpack`, explicitly marked "**m48, spelling pinned at m48 freeze**", and
m48's §6.1a anchor is bindingly "worded over §6.1a's bound UNPACK verb" (plan `:2705`). The word
"only" therefore excludes a surface the same milestone's anchor consumes. The plan's own standard
("the DoD scopes an implementer off the target line", plan `:2943`, `:3263`) makes this the kind of
line that gets read literally.

**Evidence.** Read: plan `:2360-2366`, `:2466-2472`, `:2703-2714`.

**Suggested fix.** Add `graphed_histogram.unpack` (whatever its pinned spelling) to m48's §9.1 list.

---

## LOW-2 — m48 targets "§2" unqualified while §2.5's shift-after-weight diagnostic is bindingly m49

**Section:** m48 target line (plan `:2462`) vs §2.5 (plan `:899-903`) and m49 (plan `:2941-2943`).

**Detail.** §2.5 states "The §2.1 shift-after-weight ordering rule gets a diagnostic on the same
channel (r16), and it is **an m49 target**" — it depends on §3.4's reachability cone, which r14 moved
to m49. r18 correspondingly added it to m49's target line. m48's target line still reads "§1, **§2**
(incl. the §2.6 event context), §3.2, §4, §6.1 … except §6.1c's AXIS-MODE slot", with no exclusion.
An implementer scoped off m48's line would attempt a diagnostic whose §3.4 substrate does not exist
yet; a reviewer checking "targets exactly as specified" has two answers.

**Evidence.** Read: plan `:899-903`, `:2461-2472`, `:2941-2943`.

**Suggested fix.** m48's target line: "§2 **except §2.5's shift-after-weight diagnostic (m49, it
needs §3.4)**" — the same parenthetical shape already used for §6.1c's axis-mode slot and §3.4.

---

## LOW-3 — `unweighted=True`'s interaction with an explicit `weight=[…]` is undefined, and m48 freezes it

**Section:** §6.1d (plan `:1439-1440`), m48 anchor (plan `:2891`).

**Detail.** §6.1d binds a new `fill` parameter in one clause: "`weight=[...]` *adds* factors;
`unweighted=True` opts out (counts histograms)". Measured, no such parameter exists today —
`fill(self, *args, weight=None, sample=None, threads=None)`
(`graphed-histogram-latest/src/graphed_histogram/boost.py:152-158`) — so it is new m48 source with a
frozen m48 anchor (the anchor list names "`unweighted=True`" bare, plan `:2891`). What is undefined:
does it suppress only the **ambient** weight, or every weight? "counts histograms" implies the
latter, in which case `fill(x, weight=[w], unweighted=True)` is contradictory and the plan does not
say whether it is an error, whether `weight=` wins, or whether `unweighted=` wins. §2.5's own ethos
("silent-drop failure modes become errors") argues for an error; nothing binds it, and a test-author
freezes whichever they guess.

**Evidence.** Read: plan `:1439-1440`, `:2891`. Code:
`graphed-histogram-latest/src/graphed_histogram/boost.py:152-178,198-212` (params key set today is
`{"spec","n_axes","weighted","sampled"}`, confirming §6.3's r17 literal).

**Suggested fix.** One sentence in §6.1d: `unweighted=True` suppresses the ambient weight **and** any
explicit `weight=[…]`; supplying both is a record-time error naming both (or, if the intent is
ambient-only suppression, say so and state that explicit factors still apply). Name the chosen answer
in m48's anchor.

---

## LOW-4 — the §2.6 sketch's `btag_sf(sel.Jet)` is not the corpus semantics m48/m49 must reproduce

**Section:** §2.6 sketch (plan `:991-996`), cited as the mainline by §2.1 (plan `:375-384`,
`:417-423`).

**Detail.** §2.6c binds "`sel.Jet` IS `events.Jet` re-indexed by `sel`'s derivation mask" — i.e. the
**uncut** jet collection restricted to selected events. The sketch then registers
`btag_sf(sel.Jet)`. Measured, the corpus reference computes the b-tag SF on the **pt-cut** jets:
`graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:60-76` — `jets = _apply_jes(...)`,
`good = jets[jets.pt > 25]`, `sel_jets = good[sel]`, `weight = _btag_weight(sel_jets, …)`, and
`_btag_weight` products a per-jet SF over `axis=1` (`:25-36`), so including the sub-25 GeV jets
changes the weight. §2.1 leans on this exact corpus case to justify the label-aligned stacking rule
("the corpus computes the CENTRAL b-tag SF on JES-shifted, JES-selected jets … so the
`ttbar_4j1b_jes_up` reference IS b-tag weighted"), and r18 additionally cites the sketch line as
proof that a member may be a `Varied`. The corpus-faithful spelling in the context idiom is
`btag_sf(sel.Jet[sel.Jet.pt > 25])`; a test-author transcribing the sketch shape into the m48/m49
reference matrix will miss the 15 stored references and spend an iteration finding out why.

**Evidence.** Read: plan `:375-384`, `:413-423`, `:936-948`, `:991-996`. Code:
`graphed-corpus-latest/src/graphed_corpus/analyses/systematics.py:25-36,60-76`.

**Suggested fix.** Change the sketch's two `btag_sf(...)` arguments to the pt-cut form (or add a
one-line comment saying the corpus applies the SF to the pt-cut jets and the sketch is abbreviated),
and say so in the m48 matrix anchor alongside the existing `gak.full_like` / `stable()`-rounding
mid-freeze-discovery notes.

---

## LOW-5 — §1.1's r18 digit-count formula is ambiguous for dotted mantissas (off by one at the cap)

**Section:** §1.1 (plan `:265-271`).

**Detail.** r18 bound the integer-magnitude guard as: "the magnitude test runs on the COMPUTED DIGIT
COUNT — **mantissa digits + exponent** — BEFORE any rendering". Read literally over the input grammar
`-?\d+(\.\d+)?([eE][+-]?\d+)?`, `"1.5e31"` has 2 mantissa digits and exponent 31 → 33 → rejected,
while its actual plain-digit rendering is `15` followed by 30 zeros = **32** digits, i.e. exactly at
the cap and legal. The formula is correct only if the mantissa is first normalized to an integer and
the exponent decremented accordingly (2 digits + exponent 30 = 32). Harmless for the anchored case
(`"1e40"`, 41 digits) but wrong at the boundary, and the boundary is exactly where the two bound
rejection messages (magnitude vs generic tag-length) are distinguished — which m48 freezes as two
distinct cases (plan `:2919-2925`).

**Evidence.** Read: plan `:255-275`, `:2917-2925`.

**Suggested fix.** State the normalization: "digit count = (mantissa digits after removing the
decimal point, leading zeros stripped) + (exponent adjusted for the decimal point's position)".

---

## Verdict

**DIRTY.** One BLOCKER and three HIGHs must be resolved before this plan is clean on the design lens.

The BLOCKER is a scope omission in an r18 sentence, cheap to fix but fatal as written: §6.1a's flat
slot keying, applied to unvaried programs, breaks five assertions in `graphed-histogram`'s frozen m23
suite that §10 declares binding and unchanged.

The three HIGHs are all missing operands rather than wrong intent, and all sit in the sections the
brief flagged as least-reviewed: §6.4a(2a) binds a record-time predicate whose decision procedure
needs a child-ward lineage traversal §2.6b's parent-pointer chain cannot provide; §2.1(b)/§2.6b bind
no row space for a registered weight factor while §2.1's stacking product and §6.4b's r18
precondition both depend on the answer; and §6.1c/§7.2/§8.2(i) all need the compiled artifact before
`aggregate_plan` — which compiles internally and takes only pre-built frozen closures — with no seam
named or pinned.

Everything else I probed held up. Specifically clean under this lens: §1.1's e-canonicalization
(cross-notation rejection, the r17 family definition, negative zero, the two cap rejections, and the
p-form/e-form parse disjointness all compose correctly); §2.4's union order against §2.6c's per-label
re-indexing and §6.1d's four-way fold; §6.2's axis-mode carrier, declaration and mode-fixing rules
against §6.1c's slot keying (the specs a slot gathers agree by construction in both modes);
§6.4c/§6.4d's XOR-delta same-shape requirement against the object-level migration case (pre-object-cut
storage keeps offsets equal by construction, and the per-level `select=` channel is what makes the
inner masks expressible); §5.4's unconditional verb refusals against its conditional cone rule (the
over-approximation is sound — every route to an Exchange/Join passes a `Varied` to a refusing verb);
§7.3's r17/r18 by-value/by-reference `DurablePlan` scoping (verified against
`core/plan.py:53-108,126-176`); the package-boundary rules (`graphed` proper imports neither
`boost_histogram` nor `awkward` under any binding here; the neutral `broadcast_like` seam and the
duck-typed `.axes` detection both hold the line); and the milestone map, apart from LOW-1 and LOW-2.
