# systematics-vary-plan r23 — review round 15, DESIGN SOUNDNESS lens

- **Lens:** design soundness — is PART II a coherent, implementable specification? Contradictions
  between sections, unhandled interactions, under-specified Implementation Targets, package-boundary
  /factorization violations, milestone-boundary consistency.
- **Plan revision reviewed:** r23 (`systematics-vary-plan.md`, 5605 lines, read in full including
  PART I, every PART II section, §10 milestones, §11, §12, the Anchors appendix and the revision
  history back through r21).
- **Date:** 2026-07-30.
- **Verification roots used** (all code facts below were measured by me in this session, never taken
  from the plan):
  - `/private/tmp/claude-501/graphed-latest` @ `ff7c607a8ba637ebc1b5db37316adf6e10028dcc` (its own
    `.venv`)
  - `/private/tmp/claude-501/graphed-histogram-latest` @ `211cbbe22497b64ce624d4880005af7faddf74f7`
    (its own `.venv`, boost_histogram 1.8.0)
- **Owner-locked decisions** (naming, functional surface, e-form canonicalization, event-context
  attachment, record-time expansion, m48–m51 scope incl. §6.4, the Phase-2 pull-in) were treated as
  fixed; nothing below asks for a different choice, only for internal consistency in how a locked
  choice is specified.

Eight findings: 0 BLOCKER, 0 HIGH, 5 MID, 3 LOW. The plan is, on this lens, close to
implementable — the new r22/r23 surfaces are where the remaining defects cluster, exactly as the
review brief predicted.

---

## MID-1 — §6.1c's `.plan()` refusal is keyed on "varied" while the hazard it exists to prevent is keyed on the axis MODE; r22/r23's own axis-mode-unvaried program falls through it

**Section:** §6.1c (plan lines 1653–1669), interacting with §6.1a r22 (`:1568-1573`), §6.2(ii)
(`:2061-2072`), and m50's new fourth output (`:4191-4197`).

**Detail.** §6.1c binds: "`.plan()` on a **varied** `Histogram` raises, pointing at the group API",
and r14 widened it from sibling mode to "GENERAL — sibling mode AND §6.2's axis mode" on an argument
that is explicitly about the SPEC, not about variations: `Histogram.plan` passes the `__init__`-time
`self._spec` to `_SumFills`/`_ZeroHist`, while §6.2 declares the variation axis at FILL time, so the
reducer's zero and the fill results disagree and cross-axis addition raises. m48's anchor repeats the
trigger verbatim: "`.plan()` on a `Histogram` carrying **varied** staged fill nodes raises"
(`:3352-3356`).

r22 then decoupled the two: §6.1a/§6.1c now bind that "the MODE, not the variation count, decides an
axis-mode output's key", and r23 added a *fourth* m50 output that is **axis-mode with NO variations**
(`:4191-4197`) precisely to witness that rule. That histogram is not varied, so the §6.1c refusal
does not fire — but its fill nodes still carry a spec with the 1-bin `"variation"` axis while
`self._spec` does not, so `.plan()` reaches exactly the failure §6.1c's r14 paragraph describes. The
trigger and the hazard no longer coincide.

**Evidence (measured this session).**

`graphed-histogram@211cbbe`, `src/graphed_histogram/boost.py:242-253` — `plan()` unconditionally
passes the `__init__`-time spec:

```
        return aggregate_plan(
            *self._fill_nodes,
            reduce=_SumFills(self._spec),
            ...
            empty=_ZeroHist(self._spec),
```

and `self._spec` is set once in `__init__` (`:148`, `self._spec: str = spec_of(self)`).
`_SumFills.__call__` does `total = zero_of(self.spec)` then `total = total + f` (`:92-96`).

The addition raises, in that repo's own venv:

```
$ .venv/bin/python -c "import boost_histogram as bh; print(bh.__version__);
  a=bh.Histogram(bh.axis.Regular(3,0,1));
  b=bh.Histogram(bh.axis.Regular(3,0,1), bh.axis.StrCategory(['nominal']));
  print(a+b)"
1.8.0
ValueError axes have different length
```

Note the fixture I used is a **one-bin** StrCategory — i.e. the exact shape §6.2(ii) says the
frontend declares for an axis-mode histogram no variation reaches ("the frontend declares the axis
ALWAYS, from an inferred label set that is `{"nominal"}` there", §6.1a `:1570-1571`).

**Suggested fix.** Re-key the §6.1c refusal on the property that actually predicts the failure:
`.plan()` raises on a `Histogram` that is **varied OR in axis mode** (equivalently: whose staged fill
nodes' spec differs from `self._spec`), naming the group API. Update m48's anchor wording ("varied
staged fill nodes") to the same predicate, and add the axis-mode-unvaried case to m50's `.plan()`
coverage — it is one line in the fixture m50 already builds for the fourth output. Leaving it as-is
does not red any frozen test, which is why it survived: it ships a user-facing hole where a bound,
anchored program shape dies with an opaque `boost_histogram` `ValueError` instead of the bound
refusal.

---

## MID-2 — §3.4's r23 fixture note is factually wrong ("exactly one construction exists") and contradicts §8.2(i)'s own m49 anchor extension; it steers m49's frozen fixture into the degenerate identical-impact-set form

**Section:** §3.4 / m49's §3.4 anchor (plan `:4023-4034`), against §3.4's binding sentence
(`:1297-1303`) and m49's §8.2(i) anchor extension (`:4069-4076`).

**Detail.** r23 added to m49's impact-set anchor: "**The FIXTURE is stated, because exactly one
construction exists** … under hash-consing two labels share a node iff that node's input ids agree,
which transitively requires their `vary` members to be structurally IDENTICAL … so the shared node
comes from giving two labels the SAME member expression — §1.2's dedup case, `vary(x, "jes", up=e,
down=e)` — **and the naive fixture (two labels with DIFFERENT members plus a "shared" downstream op)
does not exist at all**."

The transitivity argument is wrong. §3.4's impact set is `reachable(label outputs) −
reachable(nominal outputs)`. A node lands in two labels' impact sets iff it is reachable from both
non-nominal outputs and NOT from nominal's. That does **not** require the members to be identical —
it requires only that some sub-expression is used by both varied member expressions and by neither
the nominal member nor the shared prefix. That is the ordinary physics spelling of a two-sided
shift: one uncertainty-source array consumed with opposite sign by `up` and `down`, e.g.
`graphed.vary(jets, "jes", up=f(jets, k), down=g(jets, k))` where `k` is a correction array the
nominal branch never touches. §2.1 admits arbitrary member expressions, so this is a legal
`vary` program.

The plan already relies on that construction elsewhere: m49's §8.2(i) anchor is bindingly extended
with "**one derived node consumed by TWO NON-nominal universes**" (`:4069-4070`) and measures its
reduced shape (`2N + 3` / `N + 2`, `:4103-4105`). That is precisely the fixture §3.4's r23 note
declares nonexistent.

The consequence is not cosmetic. Under the prescribed `up=e, down=e` fixture the two impact sets are
**identical** (the note concedes this), so the frozen anchor witnesses §3.4's binding sentence — "a
node shared by `jes_up` and `jes_down` **but not nominal** appears in BOTH impact sets" — only in the
degenerate case where the whole cones coincide. The genuinely overlapping-but-distinct case, which is
the one §8.2(i) calls "the actual non-vacuity witness for §8.2's SET-VALUED keying claim", is left
unexercised in §3.4's own anchor.

**Evidence (measured this session, `graphed-latest@ff7c607`, its own `.venv`).** A shared non-nominal
node with structurally DIFFERENT members:

```
$ .venv/bin/python -c "
import graphed.core as gc
s = gc.GraphStore()
src = s.add_source('events', {'uri':'f.root'})
k    = s.add_op('scale',    [src],    {'c':'3.0'})   # used by BOTH members, by NEITHER nominal
nom  = s.add_op('sel',      [src],    {})
up   = s.add_op('shift',    [src, k], {'d':'up'})
dn   = s.add_op('shift',    [src, k], {'d':'dn'})
o_n, o_u, o_d = (s.add_reduction('sum',[x],{}) for x in (nom, up, dn))
... reachability difference ...
"
k= 1 up= 3 dn= 4
impact(up)= [1, 3, 6]
impact(dn)= [1, 4, 7]
shared, non-nominal: [1]
members differ: True
```

**Suggested fix.** Withdraw the "exactly one construction exists" / "does not exist at all" sentences
and replace the prescribed fixture with the shared-sub-expression one: two labels whose members
DIFFER but both consume one derived node the nominal member does not
(`vary(x, "jes", up=f(x, k), down=g(x, k))`). It gives strictly overlapping-not-equal impact sets —
the discriminating shape for §3.4's binding sentence — and it is the same construction §8.2(i)'s
anchor already builds, so the two anchors can share a fixture. Keep the id-watermark rejection note
(it still discriminates) and keep the `up=e, down=e` dedup case where it belongs, in m48's §1.2
anchor.

---

## MID-3 — `Varied`'s per-idiom public surface is unbound, while m48's class-resolution parity gate plus §10's numpy-idiom fixture pin force 26 numpy-idiom methods onto a type §2.1 says must not be numpy-idiom

**Section:** §2.2 (`:641-642`, "`Varied` is a plain frontend object"), §2.3a (`:643-701`, esp. the
r15 per-name rule at `:695-697`), §2.3e(4) (`:1052-1058`), §2.2's r18/r19 property rule
(`:602-641`), m48's anchors (`:3612-3658`, `:3513-3532`), against §2.1's factorization sentence
(`:406-407`, "per the factorization rule it is not an `Array` method, not gak, not numpy-idiom") and
the root `CLAUDE.md` §A.4 rule that the `graphed` frontend is backend-agnostic.

**Detail.** §2.3a binds a frozen parity gate whose inventory is "enumerated **dynamically from
`type(graphed.nominal(v))`** at test time (so idiom subclasses are covered)" and whose per-name
assertion is explicitly class-level: "each discovered name is resolved ON THE CLASS —
`getattr(type(varied), name, None)`, which the instance `__getattr__` never intercepts — and MUST be
a real attribute" (`:695-697`); §2.3e(4) inherits "the identical class-lookup rule". §2.2's r19
property rule and §10's r20 clause then pin the property fixture to the **numpy idiom**: "The
property-classification fixture MUST be a 1-D partitioned source" (`:3525-3532`), because `T` must be
classified by measuring a `Session.node_count()` delta on a plain nominal `Array`.

So the m48 gate runs over `type(graphed.nominal(v))` where that type is `graphed.numpy.array.
NumpyArray`, and demands that the container type expose every one of its public methods and
properties as a real class attribute. Nothing in the plan says what container type
`graphed.vary(numpy_array, …)` returns. The two natural implementations are both wrong:

- **One neutral `graphed.Varied` carrying the union.** It must define the 22 numpy-only methods and
  the 4 numpy-only properties to pass the gate. That puts numpy-idiom surface on a type exported from
  `graphed` proper — the leakage §2.1 and §A.4 forbid — and it silently shadows field access for
  those 26 names on an **awkward**-idiom `Varied`: `varied.sum` would resolve to a numpy method
  instead of the recorded `field` op that `array.py:332-335` gives the corresponding plain `Array`.
  That is verbatim the §2.6a namespace-collision hazard the whole functional respin (r6) exists to
  delete, re-appearing one object over.
- **One neutral `graphed.Varied` with only `Array`'s six names.** It fails m48's own frozen gate the
  moment the fixture is the mandated numpy one.

**Evidence (measured this session, `graphed-latest@ff7c607`, its own `.venv`).**

```
Array pub:    ['filter', 'map', 'node_id', 'reduce', 'repartition', 'session']   (6)
Numpy extra:  ['T','all','any','argmax','argmin','astype','clip','cumprod','cumsum','dtype',
               'max','mean','min','ndim','prod','ravel','reshape','round','shape','squeeze',
               'std','sum','swapaxes','take','transpose','var']                   (26)
n numpy pub: 32
inspect.isfunction methods: Array 4 (filter/map/reduce/repartition); NumpyArray 26
props: Array ['node_id','session']; NumpyArray ['T','dtype','ndim','node_id','session','shape']
issubclass(NumpyArray, Array): True
```

Grepping the plan for `per-idiom` / `Varied subclass` / `_array_cls` returns only the §2.3e
propagation-chokepoint rows and the parenthetical at `:659` ("so idiom subclasses are covered"),
which is about the *enumeration* source, not about how the container acquires the surface.

**Suggested fix.** Bind the construction, one sentence in §2.2, mirroring the mechanism §2.3e already
measured and cites: **`Varied` is per-idiom, produced through the same seam as `Session._array_cls`**
— a neutral `graphed.Varied` base carrying `Array`'s surface, with `graphed.numpy` supplying the
numpy-idiom subclass whose methods/properties mirror `NumpyArray`'s — and state that
`graphed.vary(x, …)` returns the container class paired with `type(x)`. That makes §2.3a's dynamic
enumeration self-consistent (the discovered inventory and the resolving class come from the same
idiom), keeps the numpy surface inside `graphed.numpy`, and preserves field access for those 26 names
on the awkward idiom. Without it, m48 freezes a gate whose pass condition depends on an unbound
implementation shape.

---

## MID-4 — §9.1's stated purpose for `graphed.weight(ctx)` is a program §6.1d r19 makes a record-time error, and no other spelling for "ambient suppressed, my own weight applied" survives

**Section:** §9.1 (`:2993-3000`) vs §6.1d r19 (`:1767-1775`) and m48's frozen anchor
(`:3830-3838`).

**Detail.** §9.1 gives two reasons `graphed.weight(ctx)` must exist at m48: §6.4b's stored varied
factors, "**nor for anything wanting the event weight explicitly alongside `unweighted=True`**".

§6.1d's r19 clause, added later, forecloses exactly that: "it suppresses the AMBIENT weight **and**
any explicit `weight=[…]` — a counts histogram carries no weight at all — and supplying both
`unweighted=True` and a non-`None` `weight=` in ONE call is a **record-time error naming both**". m48
freezes it: "`fill(x, weight=[w], unweighted=True)` is a RECORD-TIME error naming both"
(`:3838`).

Two problems, one textual and one substantive:

1. §9.1's rationale now names a refused program. A reader (or a docs author working from §9.1, which
   is the introspection-surface section) will write the refused idiom.
2. More importantly, the combination §9.1 wanted has **no replacement spelling**. §6.1d auto-applies
   the unified context's ambient weight to every fill from a contexted value, and the only opt-out is
   `unweighted=True`, which per r19 also kills explicit factors. Reading from an ancestor context does
   not help — the mainline registers `pu`/`pdf` on the root `events` itself (§2.6 sketch,
   `:1194-1201`), and `graphed.nominal(ctx)`/`graphed.universe(ctx, L)` return contexts that still
   carry that label's ambient member (§2.2 `:579-584`). Only an all-loose fill escapes, and nothing
   exposes a way to strip a handle (§2.3e's Drop rule is about ops that *have* no contexted input).
   So "use my weight, not the ambient one" — an entirely ordinary request, e.g. filling a
   normalisation-only control histogram — is unexpressible from a contexted program in v1.

This is not an owner-locked decision; §6.1d r19 chose one of two defensible readings for a parameter
that did not exist before and did not check the surface §9.1 justified on the other reading.

**Suggested fix.** Pick one and make both sections say it:
(a) keep r19's semantics and **strike the `unweighted=True` clause from §9.1's rationale**, adding a
one-line note in §6.1d that a fill wanting a non-ambient weight is not expressible in v1 and parking
it in §11; or
(b) redefine `unweighted=True` as "suppress the AMBIENT weight only" — explicit `weight=[…]` still
applies, the combination is legal, and the counts-histogram case is `unweighted=True` with no
`weight=`. Either way, m48's anchor must be re-worded to match, because it currently freezes (a)'s
error while §9.1 advertises (b). If (b) is chosen, §6.1d's label-set clause (r23) still applies
unchanged to the suppressed ambient factor.

---

## MID-5 — §6.4a's level-≥1 `select=` key is bindingly FIELD-SCOPED, but §6.4's own canonical skim writes the collection itself, for which no field path exists and no key form is defined

**Section:** §6.4a (`:2129-2148`, r22/r23 field scoping), §6.4d (`:2444-2450`), m51's anchors
(`:4329-4331`, `:4411-4413`, `:4420-4421`), against §6.4a/§6.4e's canonical record spelling
(`:2223`, `:2252`, `:2338`, `:4346`, `:4354`, `:4361`).

**Detail.** r22 made every level-≥1 entry field-scoped and r23 swept the surrounding sentences to
match: "**one entry per (FIELD PATH, LEVEL) that varies, level 0 being keyed by the bare depth `0`**"
… "**every level-k ≥ 1 entry is FIELD-SCOPED and names the field path it applies to**". The bare
per-depth key form of r21 was removed entirely (grep over the whole document: every level-≥1 example
is `("Jet", 1)`; no clause admits a bare `1`, a `None` field path, or an empty path).

But the record §6.4 writes, in every canonical example it gives, **is** the varying collection:
`to_parquet(events.Jet, select=graphed.selection(sel))` (`:2223`, `:2252`, `:2338`, `:4346`),
`to_parquet(E1.Jet, …)` (`:4361`), and the silent-corruption control `to_parquet(sel.Jet)`
(`:2163`). For that record, "Jet" is not a field of the record — it is the record. Its depth-1 axis is
the record's own jaggedness, shared by all its fields, so r22's motivating non-single-valuedness
(mixed-depth records; Jet + Muon with two distinct depth-1 offset arrays) does not arise, and a bare
`1` would be exactly single-valued. There is no legal spelling for the object-level mask of the
canonical skim.

m51 then freezes both sides of this against each other: the round-trip anchor writes the
object-migration case "through the per-LEVEL, FIELD-SCOPED `select={0: event_mask, ("Jet", 1):
jet_mask}` channel" (`:4329-4331`), and the (2c) negative control freezes a refusal for
`select={0: evt, ("Jet", 1): evt}` (`:4412`). A test-author building the positive control from
§6.4's own canonical record (`to_parquet(events.Jet, …)`) has to decide, with nothing to work from,
whether `("Jet", 1)` self-references the record, is a missing-field refusal, or must be spelled some
third way — and freezes the guess read-only. §6.4a's own r22 rationale for the (2c) depth check
("a depth mismatch at ANY supplied level is refused … naming the level") also presupposes that the
named field can be resolved, which it cannot here.

**Suggested fix.** Admit the record's own axis explicitly, in the same sentence that binds the
field scoping: a level-k ≥ 1 entry is keyed `(field_path, k)` when the record is a record whose
NAMED field carries the level-k structure, and by the **bare depth `k`** when the level-k structure
is the record's own (the single-collection skim) — with the bare form refused, naming the ambiguity,
whenever the record has more than one distinct level-k offset array. Then state which record shape
each m51 anchor uses: the round-trip object-migration fixture is the one place a field-scoped key is
required, and §6.4d's "a field shallower than a supplied level … is unaffected" only has meaning
there. One sentence in §6.4a plus a clause in m51's round-trip bullet closes it.

---

## LOW-1 — §2.2 claims all three extraction verbs accept four input shapes, but `graphed.nominal(x)` is bound for only two of them, and identity is a plausible silently-wrong answer for the axis-mode histogram

**Section:** §2.2 r23 (`:535-540`), §6.1a (`:1611-1618`), §6.2(i-bis) (`:2012-2027`), m50's (i-bis)
anchor (`:4233-4251`).

**Detail.** §2.2 r23 enumerates, as the definition site, that `graphed.labels(x)`,
`graphed.nominal(x)` and `graphed.universe(x, label)` **each** accept four shapes — a `Varied`, an
event context, a `{label: hist}` result mapping, and a bare histogram-like object — "the per-shape
answers for the two result shapes being bound in §6.1a … and §6.2(i-bis)". But both of those
sections bind only `labels` and `universe`: §6.1a says "`graphed.universe(result[name], label)` and
`graphed.labels(result[name])` work uniformly on BOTH shapes", and §6.2(i-bis) says "`graphed.labels`
and `graphed.universe` therefore recognise it explicitly". `graphed.nominal` is named nowhere for
either shape, and m50's (i-bis) anchor asserts only `labels` and `universe`.

For an axis-mode histogram the natural fallback implementation — return the argument unchanged, the
correct answer for a bare *unvaried* histogram — is silently wrong: it hands back the whole
histogram, variation bins summed into the view the caller believes is the central value. That is the
"confidently wrong bookkeeping answer" class §6.2(i-bis) opens by naming, and no anchor sees it.

**Suggested fix.** One clause in §2.2: for the two result shapes `graphed.nominal(x)` is defined as
`graphed.universe(x, "nominal")` — identity for a bare unvaried histogram (which reads as the single
label `"nominal"`), `x["nominal"]` for a result mapping, and the nominal slice along the variation
axis for an axis-mode histogram. Add `graphed.nominal(h)` to m50's (i-bis) assertion list, where the
manually-sliced reference is already the oracle.

---

## LOW-2 — §2.1's stacking rule never states the two-level §2.4 resolution a `Varied` weight member requires, and "new to the factor" is ambiguous between the container and the member

**Section:** §2.1 (`:418-431` member types, `:476-494` stacking), §2.4 (`:1062-1075`).

**Detail.** r18 established that in overload (b) "a `Varied` factor is KEPT and consumed
label-aligned per §2.4 (`factor[L]`, falling back to its central universe when L is new to the
factor)". In the plan's own mainline that factor is nested two deep: the call
`graphed.vary(sel, "btag", btag_sf(sjets), is_weight=True, up=…, down=…)` registers a container whose
labels are `{nominal, btag_up, btag_down}` and whose **members are themselves `Varied`** over the
inherited jes labels (because `sjets` is `Varied`). Computing the inherited label's ambient member
therefore requires §2.4 twice: first pick the container's member for L (nominal fallback), then
evaluate THAT member at L (its own nominal fallback).

Nothing says this. Read at the container level — the reading the words most directly support — L =
`jes_up` IS "new to the factor" (the container carries only btag labels), so the rule yields "its
central universe" = the whole nominal member, i.e. the b-tag SF on **nominal** jets. That is exactly
the outcome §2.1's next sentence says must not happen ("the `ttbar_4j1b_jes_up` reference IS b-tag
weighted; a naive … reading omits the SF entirely and misses the reference"), and it would not be
caught until m49's 15-reference matrix — one milestone after m48 freezes the stacking anchor.

This is a wording defect, not a semantic one: the surrounding prose and the cited corpus lines
(`graphed-corpus src/graphed_corpus/analyses/systematics.py:74-76`) make the intended answer
unmistakable, and m48's stacking anchor asserts a VALUE against a corpus-derived reference, so a
careful test-author lands on the right oracle. But §2.2 defines `Varied` as holding `{label: Array}`,
so a nested container is a shape the definition does not admit either.

**Suggested fix.** State the resolution once, in §2.1's stacking paragraph: "`factor[L]` means §2.4
applied twice — the container's member for L (its `"nominal"` member when L is new to the container),
then, if that member is itself `Varied`, that member's own L (its `"nominal"` when L is new to the
member) — so the composed ambient is always a flat `{label: Array}`." Add a sentence to §2.2 noting
that a registered weight FACTOR may nest while the ambient weight `graphed.weight(ctx)` returns is
always flat.

---

## LOW-3 — §6.4c's "bit-exact reconstruction is REQUIRED" is unconditional, while the writer only stores masks for the levels the user supplies

**Section:** §6.4c (`:2416-2420`) vs §6.4a (`:2148-2156`, "it stores one packed per-label validity
mask per supplied ENTRY").

**Detail.** §6.4c: "Reading the file back and applying the deltas MUST reproduce **every** universe's
post-selection values and row set bit-for-bit vs the in-memory varied run." §6.4a is explicit that the
writer takes the masks and does not infer them, and stores one mask per **supplied** entry. A user
who applies an object-level cut in memory but supplies only `{0: event_mask}` therefore produces a
file from which no reader can reconstruct the object-level row sets — through no fault of the
implementation, and with no error anywhere. The requirement as written is unsatisfiable for that
program while the code that satisfies its intent is correct.

m51's round-trip anchor supplies both levels, so nothing reds; this is a spec-precision issue, and it
matters because §6.4c is the sink's headline contract.

**Suggested fix.** Scope the sentence to what was supplied: "…MUST reproduce every universe's
post-selection values and row set bit-for-bit **at every selection level supplied through `select=`**"
— and add one line stating the consequence for the user (a level not supplied is not recoverable;
the manifest records which levels are stored), which is also what §6.4e's manifest already carries.

---

## Verdict

**Dirty** — five MID and three LOW findings, no BLOCKER and no HIGH.

Nothing here invalidates the architecture, the milestone ordering, or any owner-locked decision, and
none of the findings requires reversing one. Three of the five MIDs (MID-1, MID-2, MID-5) are
regressions introduced by the r22/r23 edits themselves — a refusal trigger left behind when its
predicate moved, a rationale sentence asserting a falsehood about the graph model, and a key form
narrowed past the plan's own canonical spelling — which is the expected failure mode this late in a
review chain and is why the newest surfaces were the priority. MID-3 and MID-4 are older gaps that
survived because no anchor could see them: an unbound container-construction shape that the m48
parity gate silently depends on, and a capability §9.1 advertises that §6.1d later removed.

All eight have narrow, local fixes; none should need a design round. I would expect r24 to be clean
on this lens.
